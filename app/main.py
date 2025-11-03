from __future__ import annotations

import tempfile
from functools import lru_cache
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import PlainTextResponse
from markitdown import MarkItDown

app = FastAPI(title="MarkItDown Document to Markdown Converter")

SUPPORTED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-excel": ".xls",
    "text/csv": ".csv",
    "application/json": ".json",
    "text/xml": ".xml",
    "application/xml": ".xml",
    "application/zip": ".zip",
    "application/epub+zip": ".epub",
    "audio/wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "text/html": ".html",
    "application/vnd.ms-outlook": ".msg",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/bmp": ".bmp",
    "image/webp": ".webp",
    "image/tiff": ".tiff",
    "application/octet-stream": ".bin",
}


@lru_cache(maxsize=1)
def get_markitdown() -> MarkItDown:
    # MarkItDown loads heavy models; defer instantiation until the first request to keep container startup quick.
    return MarkItDown()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def get_file_suffix(content_type: str, filename: Optional[str] = None) -> str:
    """Determine file suffix from content type or filename."""
    if filename and "." in filename:
        return "." + filename.rsplit(".", 1)[1].lower()

    return SUPPORTED_MIME_TYPES.get(content_type, ".bin")


@app.post("/convert", response_class=PlainTextResponse)
async def convert_document(
    request: Request,
    file: Optional[UploadFile] = File(None, description="Document file upload"),
) -> PlainTextResponse:
    file_bytes: bytes
    file_suffix: str

    if file is not None:
        content_type = file.content_type or "application/octet-stream"

        if content_type not in SUPPORTED_MIME_TYPES and content_type not in (
            "application/octet-stream",
            None,
        ):
            supported_types = ", ".join(sorted(set(SUPPORTED_MIME_TYPES.keys())))
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported content type: {content_type}. Supported types: {supported_types}",
            )

        file_bytes = await file.read()
        file_suffix = get_file_suffix(content_type, file.filename)
    else:
        content_type = (
            request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        )

        if (
            content_type
            and content_type not in SUPPORTED_MIME_TYPES
            and content_type != "application/octet-stream"
        ):
            supported_types = ", ".join(sorted(set(SUPPORTED_MIME_TYPES.keys())))
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported content type: {content_type}. Supported types: {supported_types}",
            )

        file_bytes = await request.body()
        file_suffix = get_file_suffix(content_type or "application/octet-stream")

    if not file_bytes:
        raise HTTPException(status_code=400, detail="No file content provided.")

    try:
        with tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_file.flush()
            tmp_file_path = tmp_file.name

        converted = get_markitdown().convert(tmp_file_path)
    except Exception as exc:  # pragma: no cover - defensive logging placeholder
        raise HTTPException(
            status_code=500, detail=f"Failed to convert document: {exc}"
        ) from exc
    finally:
        try:
            import os

            os.unlink(tmp_file_path)
        except OSError:
            pass

    markdown_text = converted.text_content or ""
    return PlainTextResponse(markdown_text, media_type="text/markdown; charset=utf-8")


@app.post("/", response_class=PlainTextResponse)
async def convert_default(
    request: Request, file: Optional[UploadFile] = File(None)
) -> PlainTextResponse:
    return await convert_document(request, file)
