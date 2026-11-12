"""Модели данных: информация о медиа и задача скачивания."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

STATE_LABELS = {
    "queued": "В очереди",
    "running": "Загрузка",
    "processing": "Обработка",
    "done": "Готово",
    "error": "Ошибка",
    "cancelled": "Отменено",
}

FINAL_STATES = frozenset({"done", "error", "cancelled"})


@dataclass
class MediaInfo:
    """Результат анализа ссылки."""

    url: str
    title: str = ""
    uploader: str = ""
    duration: float | None = None
    thumbnail: str = ""
    webpage_url: str = ""
    is_playlist: bool = False
    entry_count: int = 0
    formats: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_info(cls, url: str, info: dict[str, Any]) -> MediaInfo:
        if info.get("_type") == "playlist":
            entries = [entry for entry in (info.get("entries") or []) if isinstance(entry, dict)]
            first = entries[0] if entries else {}
            return cls(
                url=url,
                title=info.get("title") or "Плейлист",
                uploader=info.get("uploader") or info.get("channel") or "",
                duration=None,
                thumbnail=first.get("thumbnail") or info.get("thumbnail") or "",
                webpage_url=info.get("webpage_url") or url,
                is_playlist=True,
                entry_count=int(info.get("playlist_count") or len(entries) or 0),
                formats=first,
            )
        return cls(
            url=url,
            title=info.get("title") or url,
            uploader=info.get("uploader") or info.get("channel") or "",
            duration=info.get("duration"),
            thumbnail=info.get("thumbnail") or "",
            webpage_url=info.get("webpage_url") or url,
            formats=info,
        )


@dataclass
class DownloadJob:
    """Одна задача в очереди."""

    url: str
    title: str
    selector: str
    format_label: str = ""
    audio_only: bool = False
    audio_format: str = ""
    playlist: bool = False
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    state: str = "queued"
    progress: int = 0
    speed: float | None = None
    eta: int | None = None
    filepath: str = ""
    error: str = ""

    @property
    def state_label(self) -> str:
        return STATE_LABELS.get(self.state, self.state)

    @property
    def is_active(self) -> bool:
        return self.state in ("running", "processing")

    @property
    def is_final(self) -> bool:
        return self.state in FINAL_STATES
