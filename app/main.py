from __future__ import annotations

import tempfile
from functools import lru_cache
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import PlainTextResponse
from markitdown import MarkItDown

app = FastAPI(title="MarkItDown PDF to Markdown")


@lru_cache(maxsize=1)
def get_markitdown() -> MarkItDown:
    # MarkItDown loads heavy models; defer instantiation until the first request to keep container startup quick.
    return MarkItDown()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/convert", response_class=PlainTextResponse)
async def convert_pdf(
    request: Request,
    file: Optional[UploadFile] = File(None, description="PDF file upload"),
) -> PlainTextResponse:
    pdf_bytes: bytes

    if file is not None:
        if file.content_type not in (
            "application/pdf",
            "application/octet-stream",
            None,
        ):
            raise HTTPException(
                status_code=415, detail="Only application/pdf uploads are supported."
            )
        pdf_bytes = await file.read()
    else:
        content_type = (
            request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        )
        if content_type not in ("application/pdf", "application/octet-stream", ""):
            raise HTTPException(
                status_code=415,
                detail="Send the PDF as application/pdf or multipart upload.",
            )
        pdf_bytes = await request.body()

    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="No PDF content provided.")

    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(pdf_bytes)
            tmp_pdf.flush()
            converted = get_markitdown().convert(tmp_pdf.name)
    except Exception as exc:  # pragma: no cover - defensive logging placeholder
        raise HTTPException(
            status_code=500, detail=f"Failed to convert PDF: {exc}"
        ) from exc

    markdown_text = converted.text_content or ""
    return PlainTextResponse(markdown_text, media_type="text/markdown; charset=utf-8")


@app.post("/", response_class=PlainTextResponse)
async def convert_default(
    request: Request, file: Optional[UploadFile] = File(None)
) -> PlainTextResponse:
    return await convert_pdf(request, file)
