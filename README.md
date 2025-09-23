# MarkItDown PDF Converter Worker

Cloudflare Worker (container-based) that accepts POSTed PDF documents and responds with their Markdown representation by leveraging Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) library.

## API

- `POST /convert` – Accepts either a raw `application/pdf` request body or a `multipart/form-data` upload field named `file`. Returns `text/markdown` with the converted content.
- `POST /` – Same as `/convert`, provided for convenience.
- `GET /health` – Lightweight health probe.

Responses use UTF-8 encoded Markdown. The service returns `415` for unsupported media types and `400` for empty payloads.

## Local development

Dependencies are managed with [uv](https://docs.astral.sh/uv/). Install it once per machine using the official installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

1. Sync dependencies and spin up a local venv (creates `.venv/` and `uv.lock`):

   ```bash
   uv sync
   ```

2. Run the API locally with uv (optional `--reload` for auto-restart):

   ```bash
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
   ```

3. Build the container image (the Dockerfile uses Astral's uv base image with `uv pip` during the build):

   ```bash
   docker build -t markitdown-pdf .
   ```

4. Run the container locally (Cloudflare's container Workers also listen on port `8080`):

   ```bash
   docker run --rm -p 8080:8080 markitdown-pdf
   ```

5. Convert a PDF:

   ```bash
   curl -X POST \
        -H "Content-Type: application/pdf" \
        --data-binary @sample.pdf \
        http://localhost:8080/convert
   ```

   Or using multipart upload:

   ```bash
   curl -X POST \
        -F "file=@sample.pdf" \
        http://localhost:8080/convert
   ```

## Deploying to Cloudflare Workers (Container)

Cloudflare's container-based Workers are currently in early access. Once your account is enabled and you have Wrangler ≥ 3.52 installed, you can deploy as follows:

1. Authenticate:

   ```bash
   npx wrangler login
   ```

2. Build and push the container image to Cloudflare's registry. The current beta exposes these via `wrangler containers`:

   ```bash
   npx wrangler containers build --name markitdown-pdf
   npx wrangler containers push --name markitdown-pdf
   ```

3. Deploy the worker referencing the pushed image:

   ```bash
   npx wrangler deploy --config wrangler.toml
   ```

Adjust the image name to match your chosen Worker name. If you maintain multiple environments, use Wrangler's `--env` flag and duplicate the relevant configuration in `wrangler.toml`.

## Configuration

- `PORT` – Defaults to `8080`. Cloudflare sets this automatically when running the container.

## Project structure

```
.
├── Dockerfile
├── README.md
├── app
│   └── main.py
├── pyproject.toml
└── wrangler.toml
```

### Notes

- The container installs MarkItDown and its dependencies at build time. Ensure your PDFs do not exceed the memory limits configured for your containerized Worker.
- If you need to support other document formats, MarkItDown can handle them as well—extend the API to branch on MIME type and call `MarkItDown.convert` accordingly.
