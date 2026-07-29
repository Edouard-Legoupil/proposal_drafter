"""Shared bounds and content checks for uploaded PDF documents."""

import os
from typing import Any

from fastapi import HTTPException, UploadFile

MAX_PDF_UPLOAD_BYTES = int(os.getenv("MAX_PDF_UPLOAD_BYTES", str(10 * 1024 * 1024)))
MAX_PDF_UPLOAD_PAGES = int(os.getenv("MAX_PDF_UPLOAD_PAGES", "100"))
UPLOAD_CHUNK_BYTES = 64 * 1024


async def read_limited_pdf_upload(
    upload: UploadFile,
    *,
    max_bytes: int = MAX_PDF_UPLOAD_BYTES,
) -> bytes:
    """Read a PDF upload in bounded chunks and verify its file signature."""
    content = bytearray()
    while chunk := await upload.read(UPLOAD_CHUNK_BYTES):
        content.extend(chunk)
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail="PDF exceeds the configured upload size limit.")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=422, detail="Uploaded content is not a valid PDF file.")
    return bytes(content)


def validate_pdf_page_count(reader: Any, *, max_pages: int = MAX_PDF_UPLOAD_PAGES) -> None:
    """Reject documents that exceed the configured parsing budget."""
    if len(reader.pages) > max_pages:
        raise HTTPException(status_code=413, detail="PDF exceeds the configured page limit.")
