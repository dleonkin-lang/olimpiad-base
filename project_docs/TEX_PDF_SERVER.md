# TeX/PDF export for worksheets

The static GitHub Pages site cannot compile TeX by itself. The first server option is therefore a separate PDF service:

1. The user selects tasks in `Листочки`.
2. The browser sends only the selected worksheet data to a server endpoint.
3. The server generates a temporary `.tex` file.
4. For PDF export, the server compiles it with `xelatex` and the browser downloads `worksheet.pdf`.
5. For TeX export, the browser downloads the generated `worksheet.tex`.

The service lives in `server/tex-pdf-service/`.

## Why this is separate from GitHub Pages

GitHub Pages only serves already prepared files: HTML, CSS, JavaScript, images, and JSON. It does not run Python, TeX, or background jobs for a visitor. PDF generation needs a runtime, temporary files, and a TeX distribution, so it belongs in a separate service such as Cloud Run.

## Data flow

The existing HTML already contains the database in `const DATA = ...`. JSON files in `docs/data/` remain the backup/source for future rebuilds. For PDF export, the page builds a small request from the selected worksheet tasks and current worksheet settings.

The server does not accept raw TeX. It accepts structured JSON, escapes text, writes selected images to a temporary directory, and then either compiles the generated TeX or returns it as a source file. This keeps the public endpoint narrower and safer.

## Endpoints

- `GET /healthz`: simple health check.
- `POST /build-pdf`: builds and returns `worksheet.pdf`.
- `POST /build-tex`: returns the generated `worksheet.tex`.

The current TeX download is a plain `.tex` file. If figures are enabled, it references the temporary image filenames generated during server-side compilation. A later improvement can add a `.zip` TeX bundle with `worksheet.tex` and image files together.

## Deployment sketch

From `server/tex-pdf-service/`:

```bash
gcloud run deploy olympiad-worksheet-pdf \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars ALLOWED_ORIGINS=https://dleonkin-lang.github.io
```

After Cloud Run returns a URL, open the static site, go to `Листочки`, press `PDF-сервер`, and paste that URL. The URL is stored only in the browser's `localStorage`.

## Invariants

- `docs/index.html` must remain public read-only: `CAN_EDIT = false`.
- `docs/admin.html` must remain editable: `CAN_EDIT = true`.
- The PDF export must not change task data, rubrics, topics, subtopics, methods, or sources.
- The worksheet payload must include only selected tasks, not the full database.
- If the PDF server is not configured, the old HTML print/export path must still work.
