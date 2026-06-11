from __future__ import annotations

import base64
import binascii
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field


MAX_PROBLEMS = int(os.getenv("MAX_PROBLEMS", "80"))
MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", "8000000"))
LATEX_TIMEOUT_SECONDS = int(os.getenv("LATEX_TIMEOUT_SECONDS", "45"))
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]


class Figure(BaseModel):
    dataUri: str | None = Field(default=None, max_length=12_000_000)
    alt: str | None = ""


class WorksheetProblem(BaseModel):
    id: str = ""
    title: str | None = ""
    statement: str | None = ""
    statementOriginal: str | None = ""
    sourceName: str | None = ""
    sourceProblemNumber: str | None = ""
    grade: list[str | int] = Field(default_factory=list)
    difficulty: int | None = None
    figures: list[Figure] = Field(default_factory=list)
    answer: str | None = ""
    answerFigures: list[Figure] = Field(default_factory=list)
    solution: str | None = ""
    solutionFigures: list[Figure] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    subtopicLabels: list[str] = Field(default_factory=list)


class WorksheetOptions(BaseModel):
    showSources: bool = True
    showTags: bool = False
    includeFigures: bool = True
    includeAnswers: bool = False
    includeSolutions: bool = False
    language: Literal["ru", "de", "both"] = "ru"
    columns: int = 1
    space: Literal["none", "small", "medium", "large"] = "none"


class BuildPdfRequest(BaseModel):
    title: str = "Листок задач"
    subtitle: str | None = ""
    options: WorksheetOptions = Field(default_factory=WorksheetOptions)
    problems: list[WorksheetProblem]


app = FastAPI(title="Olympiad Worksheet TeX PDF Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


LATEX_ESCAPE = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "<": r"\textless{}",
    ">": r"\textgreater{}",
}
DATA_URI_RE = re.compile(
    r"^data:image/(?P<kind>png|jpe?g);base64,(?P<data>[A-Za-z0-9+/=\s]+)$",
    re.IGNORECASE,
)


def tex_escape(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    out: list[str] = []
    previous_newline = False
    for char in text:
        if char == "\n":
            if not previous_newline:
                out.append(r"\par ")
                out.append("\n")
            previous_newline = True
            continue
        previous_newline = False
        out.append(LATEX_ESCAPE.get(char, char))
    return "".join(out).strip()


def compact_text(value: object) -> str:
    return " ".join(("" if value is None else str(value)).split())


def safe_problem_limit(problems: list[WorksheetProblem]) -> None:
    if not problems:
        raise HTTPException(status_code=400, detail="В листке нет задач.")
    if len(problems) > MAX_PROBLEMS:
        raise HTTPException(
            status_code=400,
            detail=f"Слишком много задач для одного PDF: {len(problems)} > {MAX_PROBLEMS}.",
        )


def write_data_uri_figure(temp_dir: Path, figure: Figure, name: str) -> str | None:
    if not figure.dataUri:
        return None
    match = DATA_URI_RE.match(figure.dataUri)
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Поддерживаются только PNG/JPEG-иллюстрации в data URI.",
        )
    encoded = re.sub(r"\s+", "", match.group("data"))
    try:
        raw = base64.b64decode(encoded, validate=True)
    except binascii.Error as exc:
        raise HTTPException(status_code=400, detail="Некорректная base64-иллюстрация.") from exc
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Иллюстрация слишком большая: {len(raw)} байт.",
        )
    ext = "jpg" if match.group("kind").lower() in {"jpg", "jpeg"} else "png"
    filename = f"{name}.{ext}"
    (temp_dir / filename).write_bytes(raw)
    return filename


def figure_block(temp_dir: Path, figures: list[Figure], prefix: str) -> str:
    blocks: list[str] = []
    for index, figure in enumerate(figures, 1):
        filename = write_data_uri_figure(temp_dir, figure, f"{prefix}_{index:03d}")
        if not filename:
            continue
        caption = tex_escape(compact_text(figure.alt or ""))
        caption_tex = f"\n{{\\footnotesize\\itshape {caption}\\par}}" if caption else ""
        blocks.append(
            "\\begin{center}\n"
            f"% Image file is generated by the PDF service from the worksheet payload.\n"
            f"\\includegraphics[width=0.78\\linewidth,height=0.30\\textheight,keepaspectratio]{{{filename}}}"
            f"{caption_tex}\n"
            "\\end{center}\n"
        )
    return "".join(blocks)


def statement_blocks(problem: WorksheetProblem, options: WorksheetOptions) -> str:
    ru = tex_escape(problem.statement or "")
    de = tex_escape(problem.statementOriginal or "")
    if options.language == "de" and de:
        return de
    if options.language == "both" and de:
        return (
            "\\textbf{Русский перевод.}\\par\n"
            f"{ru}\n\n"
            "\\textbf{Оригинал.}\\par\n"
            f"{de}"
        )
    return ru


def meta_line(problem: WorksheetProblem) -> str:
    bits: list[str] = []
    if problem.sourceProblemNumber:
        bits.append(f"№ {compact_text(problem.sourceProblemNumber)}")
    if problem.grade:
        bits.append(f"{', '.join(str(g) for g in problem.grade)} класс")
    if problem.difficulty:
        bits.append(f"сложность {problem.difficulty}")
    return " · ".join(bits)


def tags_line(problem: WorksheetProblem) -> str:
    tags = [*problem.topics, *problem.subtopicLabels, *problem.methods]
    return " · ".join(compact_text(tag) for tag in tags if compact_text(tag))


def workspace_block(space: str) -> str:
    heights = {
        "small": "28mm",
        "medium": "50mm",
        "large": "82mm",
    }
    if space not in heights:
        return ""
    return (
        "\\par\\vspace{2mm}\n"
        f"\\noindent\\rule{{\\linewidth}}{{0.2pt}}\\par\\vspace{{{heights[space]}}}\n"
    )


def render_problem(
    temp_dir: Path,
    problem: WorksheetProblem,
    number: int,
    options: WorksheetOptions,
) -> str:
    title = tex_escape(problem.title or "Задача")
    source = tex_escape(problem.sourceName or "")
    meta = tex_escape(meta_line(problem))
    body = [
        "\\Needspace{8\\baselineskip}\n",
        f"\\problem{{{number}}}{{{title}}}\n",
    ]
    if meta:
        body.append(f"{{\\footnotesize\\itshape {meta}\\par}}\n")
    if options.showSources and source:
        body.append(f"{{\\footnotesize\\itshape {source}\\par}}\n")
    body.append(statement_blocks(problem, options))
    body.append("\n")
    if options.includeFigures:
        body.append(figure_block(temp_dir, problem.figures, f"p{number}_fig"))
    if options.showTags:
        tags = tex_escape(tags_line(problem))
        if tags:
            body.append(f"{{\\scriptsize\\itshape {tags}\\par}}\n")
    if options.includeAnswers and (problem.answer or problem.answerFigures):
        body.append("\\answerheading\n")
        if problem.answer:
            body.append(tex_escape(problem.answer))
            body.append("\n")
        body.append(figure_block(temp_dir, problem.answerFigures, f"p{number}_answer"))
    if options.includeSolutions and (problem.solution or problem.solutionFigures):
        body.append("\\solutionheading\n")
        if problem.solution:
            body.append(tex_escape(problem.solution))
            body.append("\n")
        body.append(figure_block(temp_dir, problem.solutionFigures, f"p{number}_solution"))
    body.append(workspace_block(options.space))
    body.append("\n")
    return "".join(body)


def render_tex(temp_dir: Path, request: BuildPdfRequest) -> str:
    options = request.options
    columns = 2 if int(options.columns or 1) == 2 else 1
    title = tex_escape(compact_text(request.title) or "Листок задач")
    subtitle = tex_escape(compact_text(request.subtitle or ""))
    rendered_problems = [
        render_problem(temp_dir, problem, index, options)
        for index, problem in enumerate(request.problems, 1)
    ]
    body = "\n".join(rendered_problems)
    if columns == 2:
        body = "\\begin{multicols}{2}\n" + body + "\n\\end{multicols}\n"
    subtitle_tex = f"{{\\centering\\large {subtitle}\\par}}" if subtitle else ""
    return rf"""\documentclass[11pt,a4paper]{{article}}
\usepackage[a4paper,left=18mm,right=18mm,top=16mm,bottom=18mm]{{geometry}}
\usepackage{{fontspec}}
\setmainfont{{DejaVu Serif}}
\setsansfont{{DejaVu Sans}}
\usepackage{{polyglossia}}
\setdefaultlanguage{{russian}}
\setotherlanguage{{german}}
\usepackage{{graphicx}}
\usepackage{{enumitem}}
\usepackage{{multicol}}
\usepackage{{needspace}}
\usepackage{{hyperref}}
\hypersetup{{colorlinks=false,pdfborder={{0 0 0}}}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{0.55em}}
\setlength{{\columnsep}}{{9mm}}
\setlist{{nosep}}
\newcommand{{\problem}}[2]{{%
  \par\medskip
  \noindent\textbf{{Задача #1.}}\quad\textbf{{#2}}\par\nobreak
}}
\newcommand{{\answerheading}}{{\par\smallskip\noindent\textit{{Ответ.}}\quad}}
\newcommand{{\solutionheading}}{{\par\smallskip\noindent\textit{{Решение.}}\quad}}
\begin{{document}}
{{\centering\LARGE\bfseries {title}\par}}
{subtitle_tex}
\vspace{{2mm}}
\hrule
\vspace{{5mm}}
{body}
\end{{document}}
"""



def compile_pdf(tex_source: str, temp_dir: Path) -> bytes:
    tex_path = temp_dir / "worksheet.tex"
    tex_path.write_text(tex_source, encoding="utf-8")
    command = [
        "xelatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        tex_path.name,
    ]
    try:
        result = subprocess.run(
            command,
            cwd=temp_dir,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=LATEX_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="На сервере не найден xelatex. Проверьте Docker-образ.",
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="Сборка PDF заняла слишком много времени.") from exc

    pdf_path = temp_dir / "worksheet.pdf"
    if result.returncode != 0 or not pdf_path.exists():
        log_path = temp_dir / "worksheet.log"
        log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
        if not log:
            log = result.stdout.decode("utf-8", errors="replace")
        raise HTTPException(status_code=500, detail=log[-4000:])
    return pdf_path.read_bytes()


@app.get("/healthz")
def healthz() -> dict[str, object]:
    return {
        "ok": True,
        "maxProblems": MAX_PROBLEMS,
        "latexTimeoutSeconds": LATEX_TIMEOUT_SECONDS,
    }


@app.post("/build-pdf")
def build_pdf(request: BuildPdfRequest) -> Response:
    safe_problem_limit(request.problems)
    with tempfile.TemporaryDirectory(prefix="worksheet-pdf-") as tmp:
        temp_dir = Path(tmp)
        tex_source = render_tex(temp_dir, request)
        pdf = compile_pdf(tex_source, temp_dir)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="worksheet.pdf"'},
    )

@app.post("/build-tex")
def build_tex(request: BuildPdfRequest) -> Response:
    safe_problem_limit(request.problems)
    with tempfile.TemporaryDirectory(prefix="worksheet-tex-") as tmp:
        temp_dir = Path(tmp)
        tex_source = render_tex(temp_dir, request)
    return Response(
        content=tex_source,
        media_type="application/x-tex; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="worksheet.tex"'},
    )

