from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image, ImageDraw


def render_landmark_overlay(
    image_rgb: np.ndarray,
    landmarks: list[tuple[float, float]],
) -> str:
    image = Image.fromarray(image_rgb.copy())
    draw = ImageDraw.Draw(image)
    for x, y in landmarks:
        r = 2
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(0, 255, 0))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")
