from pathlib import Path

import pytest
from PIL import Image

from fastitch.geom import StitchError, is_wider_than_16_9, max_width_for_height
from fastitch.imageops import (
    collect_image_paths,
    ext_for_format,
    list_images,
    render_stitch,
    save_image,
    scale_to_height,
)


def _rgb(width: int, height: int, color: tuple[int, int, int] = (10, 20, 30)) -> Image.Image:
    return Image.new("RGB", (width, height), color)


def test_scale_to_height_up_and_down() -> None:
    assert scale_to_height(_rgb(200, 100), 50).size == (100, 50)
    assert scale_to_height(_rgb(100, 50), 100).size == (200, 100)
    src = _rgb(80, 40)
    assert scale_to_height(src, 40) is src


def test_render_no_trim(tmp_path: Path) -> None:
    images = [_rgb(40, 100, (255, 0, 0)), _rgb(80, 100, (0, 255, 0))]
    out, plan = render_stitch(images)
    assert not plan.trimmed
    assert out.size == (120, 100)
    assert out.getpixel((0, 0)) == (255, 0, 0)
    assert out.getpixel((40, 0)) == (0, 255, 0)


def test_render_trim_equal_widths() -> None:
    left = Image.new("RGB", (100, 100), (0, 0, 0))
    for x in range(100):
        for y in range(100):
            left.putpixel((x, y), (x, 0, 0))
    right = Image.new("RGB", (100, 100), (0, 0, 0))
    for x in range(100):
        for y in range(100):
            right.putpixel((x, y), (0, x, 0))
    out, plan = render_stitch([left, right])
    assert plan.trimmed
    slot = max_width_for_height(100) // 2
    assert out.size == (slot * 2, 100)
    assert out.getpixel((0, 0))[0] == 6
    assert out.getpixel((slot, 0))[1] == 6


def test_first_too_wide_raises() -> None:
    with pytest.raises(StitchError, match="16:9"):
        render_stitch([_rgb(2000, 900)])


def test_narrow_image_is_not_trimmed() -> None:
    wide = _rgb(160, 90, (255, 0, 0))
    narrow = _rgb(10, 90, (0, 255, 0))
    out, plan = render_stitch([wide, narrow])
    assert plan.trimmed
    assert out.size == (90, 90)
    assert out.getpixel((0, 0)) == (255, 0, 0)
    assert out.getpixel((85, 45)) == (0, 255, 0)
    assert not is_wider_than_16_9(out.width, 90)


def test_rgba_canvas_when_any_alpha() -> None:
    rgb = _rgb(40, 100)
    rgba = Image.new("RGBA", (40, 100), (0, 0, 255, 128))
    out, plan = render_stitch([rgb, rgba])
    assert not plan.trimmed
    assert out.mode == "RGBA"
    assert out.size == (80, 100)


def test_save_jpeg_and_png(tmp_path: Path) -> None:
    src = _rgb(30, 20, (255, 128, 0))
    jpg = tmp_path / "out.jpg"
    save_image(src, jpg, jpeg_quality=90)
    with Image.open(jpg) as saved:
        assert saved.size == (30, 20)
    png = tmp_path / "out.png"
    save_image(src, png)
    with Image.open(png) as saved:
        assert saved.size == (30, 20)
        assert saved.getpixel((0, 0)) == (255, 128, 0)


def test_ext_for_format() -> None:
    assert ext_for_format("jpeg") == ".jpg"
    assert ext_for_format("png") == ".png"
    assert ext_for_format("webp") == ".webp"
    assert ext_for_format("nope") == ".jpg"


def test_collect_and_list_images(tmp_path: Path) -> None:
    (tmp_path / "img10.jpg").write_bytes(b"x")
    (tmp_path / "img2.jpg").write_bytes(b"x")
    (tmp_path / "img1.jpg").write_bytes(b"x")
    (tmp_path / "notes.txt").write_bytes(b"x")
    names = [p.name for p in list_images(tmp_path)]
    assert names == ["img1.jpg", "img2.jpg", "img10.jpg"]
    nested = tmp_path / "album"
    nested.mkdir()
    (nested / "a.png").write_bytes(b"x")
    found = collect_image_paths([tmp_path / "notes.txt", nested])
    assert [p.name for p in found] == ["a.png"]
