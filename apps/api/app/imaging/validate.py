from __future__ import annotations

import io

import numpy as np
from PIL import Image

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


class ImageValidationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def decode_image(data: bytes, max_bytes: int) -> np.ndarray:
    if len(data) == 0 or len(data) > max_bytes:
        raise ImageValidationError(
            "invalid_image",
            "Image is empty or exceeds the maximum allowed size.",
        )
    try:
        with Image.open(io.BytesIO(data)) as img:
            if img.format not in ALLOWED_FORMATS:
                raise ImageValidationError(
                    "invalid_image",
                    "Unsupported image format. Use JPEG, PNG, or WebP.",
                )
            rgb = img.convert("RGB")
            return np.asarray(rgb)
    except ImageValidationError:
        raise
    except Exception as exc:
        raise ImageValidationError(
            "invalid_image",
            "Could not decode image. Use a valid JPEG, PNG, or WebP file.",
        ) from exc
