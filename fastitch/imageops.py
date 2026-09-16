from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageOps

from fastitch.constants import IMAGE_EXTS
from fastitch.geom import StitchPlan, plan_stitch, scaled_width

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass


_NATURAL_SPLIT = re.compile(r"(\d+)")


def natural_key(name: str) -> list:
    return [
        int(part) if part.isdigit() else part.casefold()
        for part in _NATURAL_SPLIT.split(name)
    ]


def is_image_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTS


def list_images(folder: Path) -> list[Path]:
    try:
        files = [p.resolve() for p in folder.iterdir() if is_image_file(p)]
    except OSError:
        return []
    files.sort(key=lambda p: natural_key(p.name))
    return files


def collect_image_paths(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        path = Path(path)
        candidates: list[Path] = []
        if is_image_file(path):
            candidates = [path]
        elif path.is_dir():
            candidates = list_images(path)
        for candidate in candidates:
            try:
                key = str(candidate.resolve())
            except OSError:
                key = str(candidate)
            if key in seen:
                continue
            seen.add(key)
            out.append(candidate)
    return out


def load_image(path: Path) -> Image.Image:
    with Image.open(path) as opened:
        image = ImageOps.exif_transpose(opened)
        return _normalize_mode(image)


def _normalize_mode(image: Image.Image) -> Image.Image:
    if image.mode in ("RGB", "RGBA"):
        return image.copy()
    if image.mode == "P":
        return image.convert("RGBA" if "transparency" in image.info else "RGB")
    if image.mode in ("LA", "PA"):
        return image.convert("RGBA")
    if image.mode in ("L", "CMYK", "I", "F", "1"):
        return image.convert("RGB")
    return image.convert("RGBA")


def scale_to_height(image: Image.Image, height: int) -> Image.Image:
    new_w = scaled_width(image.width, image.height, height)
    if image.size == (new_w, height):
        return image
    return image.resize((new_w, height), Image.Resampling.LANCZOS)


def render_stitch(images: list[Image.Image]) -> tuple[Image.Image, StitchPlan]:
    sizes = [(im.width, im.height) for im in images]
    plan = plan_stitch(sizes)
    scaled = [scale_to_height(im, plan.height) for im in images]
    mode = "RGBA" if any(im.mode == "RGBA" for im in scaled) else "RGB"
    fill = (0, 0, 0, 0) if mode == "RGBA" else (0, 0, 0)
    out = Image.new(mode, (plan.output_width, plan.height), fill)
    x = 0
    for image, panel in zip(scaled, plan.panels, strict=True):
        cropped = image.crop(panel.crop)
        if cropped.mode != mode:
            cropped = cropped.convert(mode)
        out.paste(cropped, (x, 0))
        x += cropped.width
    return out, plan


def ext_for_format(output_format: str) -> str:
    mapping = {
        "jpeg": ".jpg",
        "jpg": ".jpg",
        "png": ".png",
        "webp": ".webp",
    }
    return mapping.get((output_format or "").lower(), ".jpg")


def save_image(
    image: Image.Image,
    path: Path,
    jpeg_quality: int = 92,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ext = path.suffix.lower()
    quality = max(1, min(100, jpeg_quality))
    if ext in {".jpg", ".jpeg", ".jfif"}:
        to_save = image.convert("RGB") if image.mode != "RGB" else image
        to_save.save(
            path,
            format="JPEG",
            quality=quality,
            optimize=True,
            subsampling=0,
        )
        return
    if ext == ".webp":
        to_save = image
        if image.mode not in ("RGB", "RGBA"):
            to_save = image.convert("RGBA")
        to_save.save(path, format="WEBP", quality=quality, method=4)
        return
    if ext == ".png":
        image.save(path, format="PNG", optimize=True)
        return
    image.save(path)
