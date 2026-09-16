from __future__ import annotations

import re
from pathlib import Path

from fastitch.constants import DEFAULT_SUFFIX


def normalize_ext(ext: str) -> str:
    ext = ext.strip() or ".jpg"
    if not ext.startswith("."):
        ext = "." + ext
    return ext.lower()


def normalize_suffix(suffix: str) -> str:
    text = suffix.strip()
    return text if text else DEFAULT_SUFFIX


def example_name(
    source_name: str,
    *,
    suffix: str = DEFAULT_SUFFIX,
    subfolder: str = "",
    ext: str = ".jpg",
) -> str:
    stem = Path(source_name).stem or "image"
    filename = f"{stem}{normalize_suffix(suffix)}{normalize_ext(ext)}"
    sub = subfolder.strip().replace("\\", "/").strip("/")
    if sub:
        return f"{sub}/{filename}"
    return filename


def next_dest_path(
    source: Path,
    *,
    suffix: str = DEFAULT_SUFFIX,
    subfolder: str = "",
    ext: str | None = None,
) -> Path:
    source = Path(source)
    ext = normalize_ext(ext if ext is not None else ".jpg")
    suffix = normalize_suffix(suffix)
    dest_dir = source.parent
    sub = subfolder.strip().replace("\\", "/").strip("/")
    if sub:
        dest_dir = dest_dir / sub
    dest_dir.mkdir(parents=True, exist_ok=True)

    stem = source.stem or "image"
    candidate = dest_dir / f"{stem}{suffix}{ext}"
    if not _taken(candidate, source):
        return candidate

    pattern = re.compile(
        rf"^{re.escape(stem)}{re.escape(suffix)}_(\d+){re.escape(ext)}$",
        re.IGNORECASE,
    )
    n = max(2, _max_number(dest_dir, pattern) + 1)
    while True:
        candidate = dest_dir / f"{stem}{suffix}_{n}{ext}"
        if not _taken(candidate, source):
            return candidate
        n += 1


def _max_number(folder: Path, pattern: re.Pattern[str]) -> int:
    highest = 1
    try:
        names = [p.name for p in folder.iterdir() if p.is_file()]
    except OSError:
        return 1
    for name in names:
        match = pattern.match(name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest


def _taken(candidate: Path, source: Path) -> bool:
    if candidate.exists():
        return True
    try:
        return candidate.resolve() == source.resolve()
    except OSError:
        return False
