from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from fastitch.constants import (
    APP_NAME,
    DEFAULT_FORMAT,
    DEFAULT_JPEG_QUALITY,
    DEFAULT_SUFFIX,
)


def config_dir() -> Path:
    override = os.environ.get("FASTITCH_CONFIG_DIR")
    if override:
        return Path(override)
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    return Path.home() / ".config" / APP_NAME.lower()


def config_path() -> Path:
    return config_dir() / "settings.json"


@dataclass
class Settings:
    suffix: str = DEFAULT_SUFFIX
    subfolder: str = ""
    output_format: str = DEFAULT_FORMAT
    jpeg_quality: int = DEFAULT_JPEG_QUALITY
    last_dir: str = ""
    window_x: int = -1
    window_y: int = -1
    window_w: int = 1280
    window_h: int = 800
    splitter: list[int] = field(default_factory=lambda: [260, 1020])

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, data: dict) -> "Settings":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        settings = cls(**filtered)
        settings.jpeg_quality = max(1, min(100, int(settings.jpeg_quality)))
        if settings.output_format not in {"jpeg", "jpg", "png", "webp"}:
            settings.output_format = DEFAULT_FORMAT
        if settings.output_format == "jpg":
            settings.output_format = "jpeg"
        if not str(settings.suffix).strip():
            settings.suffix = DEFAULT_SUFFIX
        return settings


def load_settings() -> Settings:
    path = config_path()
    if not path.exists():
        return Settings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return Settings.from_json(data)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
    return Settings()


def save_settings(settings: Settings) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(settings.to_json(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
