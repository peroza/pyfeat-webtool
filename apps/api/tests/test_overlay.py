import base64
import io

import numpy as np
from PIL import Image

from app.imaging.overlay import _landmark_radius, render_landmark_overlay


def test_overlay_returns_png_base64():
    image = np.zeros((40, 40, 3), dtype=np.uint8)
    b64 = render_landmark_overlay(image, [(10.0, 10.0), (20.0, 20.0)])
    raw = base64.b64decode(b64)
    with Image.open(io.BytesIO(raw)) as img:
        assert img.format == "PNG"
        assert img.size == (40, 40)


def test_landmark_radius_scales_with_image_size():
    assert _landmark_radius(40, 40) == 4  # floor at minimum
    assert _landmark_radius(2000, 3000) >= 20


def test_overlay_draws_visible_green_on_large_image():
    image = np.zeros((800, 600, 3), dtype=np.uint8)
    b64 = render_landmark_overlay(image, [(300.0, 400.0)])
    raw = base64.b64decode(b64)
    with Image.open(io.BytesIO(raw)) as img:
        arr = np.asarray(img)
    # Center of the marker should be clearly green, not black.
    pixel = arr[400, 300]
    assert int(pixel[1]) > 150
    assert int(pixel[1]) > int(pixel[0])
    assert int(pixel[1]) > int(pixel[2])


def test_overlay_draws_face_bbox_when_provided():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    b64 = render_landmark_overlay(
        image,
        landmarks=[],
        face_bbox=(10.0, 20.0, 40.0, 50.0),
    )
    raw = base64.b64decode(b64)
    with Image.open(io.BytesIO(raw)) as img:
        arr = np.asarray(img)
    # Top edge of the cyan rectangle should be present.
    edge = arr[20, 30]
    assert int(edge[2]) > 150
    assert int(edge[2]) > int(edge[0])
