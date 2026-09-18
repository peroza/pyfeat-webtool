import io

import numpy as np
import pytest
from PIL import Image

from app.imaging.validate import (
    ImageValidationError,
    decode_image,
    downsample_for_analysis,
)


def _png_bytes(size=(32, 32), color=(255, 0, 0)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def _jpeg_with_orientation(orientation: int, upright_size=(60, 80)) -> bytes:
    """Build a JPEG whose pixels need EXIF orientation to match upright_size."""
    width, height = upright_size
    upright = Image.new("RGB", (width, height), (10, 20, 30))
    # Paint a unique marker near the visual top-left after correct orientation.
    for y in range(8):
        for x in range(8):
            upright.putpixel((x, y), (255, 0, 0))
    # Orientation 6: rotate upright 90° CCW for storage; viewers rotate 90° CW.
    if orientation == 6:
        stored = upright.transpose(Image.ROTATE_90)
    elif orientation == 1:
        stored = upright
    else:
        raise ValueError(f"unsupported test orientation: {orientation}")
    exif = Image.Exif()
    exif[274] = orientation
    buf = io.BytesIO()
    stored.save(buf, format="JPEG", quality=95, exif=exif)
    return buf.getvalue()


def test_decode_valid_png():
    arr = decode_image(_png_bytes(), max_bytes=10_000_000)
    assert arr.shape == (32, 32, 3)


def test_decode_applies_exif_orientation():
    data = _jpeg_with_orientation(6, upright_size=(60, 80))
    arr = decode_image(data, max_bytes=10_000_000)
    # Must be portrait display size, not the landscape sensor storage size.
    assert arr.shape == (80, 60, 3)
    # Red marker should land at visual top-left after transpose.
    assert int(arr[2, 2, 0]) > 200
    assert int(arr[2, 2, 1]) < 40


def test_decode_orientation_1_unchanged_shape():
    data = _jpeg_with_orientation(1, upright_size=(60, 80))
    arr = decode_image(data, max_bytes=10_000_000)
    assert arr.shape == (80, 60, 3)


def test_reject_oversized():
    data = _png_bytes()
    with pytest.raises(ImageValidationError) as exc:
        decode_image(data, max_bytes=10)
    assert exc.value.code == "invalid_image"


def test_reject_garbage():
    with pytest.raises(ImageValidationError) as exc:
        decode_image(b"not-an-image", max_bytes=10_000_000)
    assert exc.value.code == "invalid_image"


def test_downsample_shrinks_long_edge():
    image = np.zeros((3088, 2316, 3), dtype=np.uint8)
    out = downsample_for_analysis(image, max_side=1280)
    assert max(out.shape[0], out.shape[1]) == 1280
    assert out.shape[0] == 1280
    assert out.shape[1] == 960


def test_downsample_leaves_small_images_unchanged():
    image = np.zeros((400, 300, 3), dtype=np.uint8)
    out = downsample_for_analysis(image, max_side=1280)
    assert out.shape == image.shape
    assert np.array_equal(out, image)
