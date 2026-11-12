"""Настройки приложения: загрузка и сохранение в JSON."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

APP_NAME = "Eirin"


def config_dir() -> Path:
    """Каталог конфигурации, соответствующий соглашениям ОС."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / APP_NAME


CONFIG_FILE = config_dir() / "settings.json"


def default_output_dir() -> Path:
    downloads = Path.home() / "Downloads"
    return downloads / APP_NAME if downloads.is_dir() else Path.home() / APP_NAME


@dataclass
class Settings:
    """Пользовательские настройки. Все поля сериализуются в JSON."""

    output_dir: str = field(default_factory=lambda: str(default_output_dir()))
    filename_template: str = "%(title)s [%(id)s].%(ext)s"

    # Аудио
    audio_only: bool = False
    audio_format: str = "mp3"
    audio_quality: str = "0"

    # Видео
    container: str = "auto"  # auto | mp4 | mkv | webm

    # Субтитры и метаданные
    write_subs: bool = False
    subtitle_langs: str = "ru,en"
    embed_subs: bool = True
    embed_thumbnail: bool = True
    embed_metadata: bool = True

    # Прочее
    sponsorblock: bool = False
    cookies_browser: str = ""  # "", chrome, firefox, edge, brave, opera, vivaldi, chromium
    proxy: str = ""
    rate_limit: str = ""  # например, "5M"
    retries: int = 10
    concurrent_downloads: int = 2
    playlist: bool = False
    allow_remote_components: bool = True  # EJS-скрипты yt-dlp для YouTube

    @classmethod
    def load(cls, path: Path | None = None) -> Settings:
        target = path or CONFIG_FILE
        try:
            raw = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        if not isinstance(raw, dict):
            return cls()
        known = {f.name for f in fields(cls)}
        try:
            return cls(**{k: v for k, v in raw.items() if k in known})
        except TypeError:
            return cls()

    def save(self, path: Path | None = None) -> None:
        target = path or CONFIG_FILE
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(asdict(self), ensure_ascii=False, indent=2)
        target.write_text(payload, encoding="utf-8")
