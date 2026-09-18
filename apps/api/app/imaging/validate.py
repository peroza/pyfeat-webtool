from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageOps

# MPO is a multi-frame JPEG variant common on iPhone photos; Pillow labels it
# "MPO" even when the browser reports image/jpeg.
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "MPO"}


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
            # iPhone (and many cameras) store pixels in sensor orientation and
            # put the display rotation in EXIF. Browsers honor that tag for
            # <img> previews; without applying it here, Detectorv2 sees a
            # sideways face, finds a box, then predicts an upright mesh — so
            # the overlay looks "shifted" on phone photos while internet
            # downloads (usually Orientation=1) look fine.
            #
            # MPO (common after HEIC→JPEG on iPhone) may have a second
            # disparity/depth frame; Image.open uses the first RGB frame.
            oriented = ImageOps.exif_transpose(img)
            rgb = oriented.convert("RGB")
            return np.asarray(rgb)
    except ImageValidationError:
        raise
    except Exception as exc:
        raise ImageValidationError(
            "invalid_image",
            "Could not decode image. Use a valid JPEG, PNG, or WebP file.",
        ) from exc


def downsample_for_analysis(
    image_rgb: np.ndarray,
    max_side: int,
) -> np.ndarray:
    """Shrink large photos so the face detector sees one whole face.

    On multi-megapixel iPhone selfies (especially with glasses), RetinaFace
    often fires separate detections on each eye. Landmarks then look like a
    tiny face glued to one eye. Capping the long edge restores a single
    face-sized box — JPEG export quality is irrelevant.
    """
    if max_side <= 0:
        raise ValueError("max_side must be positive")
    height, width = image_rgb.shape[:2]
    long_side = max(height, width)
    if long_side <= max_side:
        return image_rgb
    scale = max_side / long_side
    new_size = (max(1, int(round(width * scale))), max(1, int(round(height * scale))))
    resized = Image.fromarray(image_rgb).resize(new_size, Image.Resampling.LANCZOS)
    return np.asarray(resized)