import io

import pytest
from PIL import Image

from app.imaging.validate import ImageValidationError, decode_image


def _png_bytes(size=(32, 32), color=(255, 0, 0)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def test_decode_valid_png():
    arr = decode_image(_png_bytes(), max_bytes=10_000_000)
    assert arr.shape == (32, 32, 3)


def test_reject_oversized():
    data = _png_bytes()
    with pytest.raises(ImageValidationError) as exc:
        decode_image(data, max_bytes=10)
    assert exc.value.code == "invalid_image"


def test_reject_garbage():
    with pytest.raises(ImageValidationError) as exc:
        decode_image(b"not-an-image", max_bytes=10_000_000)
    assert exc.value.code == "invalid_image"
