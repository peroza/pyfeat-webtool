from __future__ import annotations

from fastapi import HTTPException, UploadFile

UPLOAD_READ_CHUNK_SIZE = 64 * 1024


async def read_bounded_upload(file: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(UPLOAD_READ_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=400,
                detail="Upload exceeds maximum size.",
            )
        chunks.append(chunk)
    return b"".join(chunks)
