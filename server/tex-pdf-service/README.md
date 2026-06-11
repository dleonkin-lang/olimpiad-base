# TeX PDF service for worksheets

Small FastAPI service for building worksheet PDFs from selected tasks. It is meant to run outside GitHub Pages, for example on Cloud Run.

The static site sends structured worksheet JSON to `POST /build-pdf`. The service does not accept raw TeX: it escapes task text, writes selected PNG/JPEG data-URI figures to a temporary directory, generates `worksheet.tex`, and compiles it with `xelatex`.

## Local run

```bash
docker build -t olympiad-worksheet-pdf .
docker run --rm -p 8080:8080 olympiad-worksheet-pdf
```

Health check:

```bash
curl http://localhost:8080/healthz
```

## Cloud Run

From this folder:

```bash
gcloud run deploy olympiad-worksheet-pdf \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars ALLOWED_ORIGINS=https://dleonkin-lang.github.io
```

After deployment, open the static site, go to `Листочки`, press `PDF-сервер`, and paste the Cloud Run URL.

## Settings

- `ALLOWED_ORIGINS`: comma-separated browser origins allowed by CORS. Default is `*`.
- `MAX_PROBLEMS`: maximum tasks per PDF. Default is `80`.
- `MAX_IMAGE_BYTES`: maximum decoded bytes per image. Default is `8000000`.
- `LATEX_TIMEOUT_SECONDS`: `xelatex` timeout. Default is `45`.

## Notes

This is an MVP. The next useful step is a preview/debug mode that returns the generated TeX for trusted local testing, but that should stay disabled in a public deployment.
