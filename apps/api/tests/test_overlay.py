import base64
import io

import numpy as np
from PIL import Image

from app.imaging.overlay import render_landmark_overlay


def test_overlay_returns_png_base64():
    image = np.zeros((40, 40, 3), dtype=np.uint8)
    b64 = render_landmark_overlay(image, [(10.0, 10.0), (20.0, 20.0)])
    raw = base64.b64decode(b64)
    with Image.open(io.BytesIO(raw)) as img:
        assert img.format == "PNG"
        assert img.size == (40, 40)
