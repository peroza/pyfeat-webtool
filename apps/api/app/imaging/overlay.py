from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image, ImageDraw

# Marker size as a fraction of the shorter image side (keeps dots visible on
# large phone photos while staying small on tiny fixtures).
_MARKER_SCALE = 0.012
_MIN_RADIUS = 4
_MAX_RADIUS = 28


def _landmark_radius(width: int, height: int) -> int:
    shorter = min(width, height)
    return max(_MIN_RADIUS, min(_MAX_RADIUS, int(shorter * _MARKER_SCALE)))


def _box_line_width(width: int, height: int) -> int:
    shorter = min(width, height)
    return max(2, min(8, int(shorter * 0.004)))


def render_landmark_overlay(
    image_rgb: np.ndarray,
    landmarks: list[tuple[float, float]],
    face_bbox: tuple[float, float, float, float] | None = None,
) -> str:
    image = Image.fromarray(image_rgb.copy())
    draw = ImageDraw.Draw(image)
    if face_bbox is not None:
        x, y, w, h = face_bbox
        line = _box_line_width(image.width, image.height)
        # FaceRect from the detector is typically well placed; draw it so the
        # overlay still has a trustworthy visual even when mesh points drift.
        draw.rectangle((x, y, x + w, y + h), outline=(0, 200, 255), width=line)
    radius = _landmark_radius(image.width, image.height)
    outline = max(1, radius // 4)
    for x, y in landmarks:
        marker = (x - radius, y - radius, x + radius, y + radius)
        # Dark outline then bright fill so markers read on light and dark faces.
        draw.ellipse(marker, fill=(0, 220, 80), outline=(0, 60, 20), width=outline)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")
