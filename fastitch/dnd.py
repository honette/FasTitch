from __future__ import annotations

from pathlib import Path

from fastitch.imageops import collect_image_paths


def dropped_image_paths(mime) -> list[Path]:  # noqa: ANN001
    if mime is None or not mime.hasUrls():
        return []
    paths: list[Path] = []
    for url in mime.urls():
        local = url.toLocalFile()
        if local:
            paths.append(Path(local))
    return collect_image_paths(paths)
