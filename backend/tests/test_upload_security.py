import io
from unittest.mock import Mock

import pytest
from fastapi import HTTPException, UploadFile

from backend.utils.upload_security import read_limited_pdf_upload, validate_pdf_page_count


@pytest.mark.asyncio
async def test_pdf_upload_rejects_payload_over_limit():
    upload = UploadFile(filename="large.pdf", file=io.BytesIO(b"%PDF-" + b"x" * 20))

    with pytest.raises(HTTPException) as exc_info:
        await read_limited_pdf_upload(upload, max_bytes=10)

    assert exc_info.value.status_code == 413


@pytest.mark.asyncio
async def test_pdf_upload_rejects_spoofed_pdf():
    upload = UploadFile(filename="spoofed.pdf", file=io.BytesIO(b"not a pdf"))

    with pytest.raises(HTTPException) as exc_info:
        await read_limited_pdf_upload(upload)

    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_pdf_upload_accepts_pdf_signature():
    upload = UploadFile(filename="valid.pdf", file=io.BytesIO(b"%PDF-1.7\nbody"))

    assert await read_limited_pdf_upload(upload) == b"%PDF-1.7\nbody"


def test_pdf_page_count_is_bounded():
    reader = Mock(pages=[Mock()] * 101)

    with pytest.raises(HTTPException) as exc_info:
        validate_pdf_page_count(reader, max_pages=100)

    assert exc_info.value.status_code == 413
