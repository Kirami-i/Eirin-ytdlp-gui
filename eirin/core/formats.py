"""Разбор форматов yt-dlp и человекочитаемое форматирование значений.

Модуль намеренно не зависит от PySide6 — его можно тестировать отдельно.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

AUDIO_ONLY_SELECTOR = "ba/b"
BEST_SELECTOR = "bv*+ba/b"

_UNITS = ("B", "KiB", "MiB", "GiB", "TiB", "PiB")
_RATE_RE = re.compile(r"^\s*([\d.]+)\s*([kmg]?)(?:i?b)?\s*(?:/\s*s)?\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class FormatRow:
    """Строка таблицы форматов."""

    format_id: str
    selector: str
    resolution: str
    fps: str
    codec: str
    size: str
    note: str
    audio_only: bool = False
    is_preset: bool = False

    @property
    def display_id(self) -> str:
        return "★" if self.is_preset else self.format_id


PRESETS: tuple[FormatRow, ...] = (
    FormatRow(
        format_id="preset:best",
        selector=BEST_SELECTOR,
        resolution="Лучшее качество",
        fps="",
        codec="video+audio",
        size="",
        note="Автоматический выбор дорожек",
        is_preset=True,
    ),
    FormatRow(
        format_id="preset:mp4",
        selector="bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        resolution="Лучшее MP4",
        fps="",
        codec="H.264 / AAC",
        size="",
        note="Максимальная совместимость",
        is_preset=True,
    ),
    FormatRow(
        format_id="preset:worst",
        selector="wv*+wa/w",
        resolution="Минимальное",
        fps="",
        codec="video+audio",
        size="",
        note="Экономия трафика",
        is_preset=True,
    ),
    FormatRow(
        format_id="preset:audio",
        selector=AUDIO_ONLY_SELECTOR,
        resolution="Только аудио",
        fps="",
        codec="audio",
        size="",
        note="Без видео",
        audio_only=True,
        is_preset=True,
    ),
)


def human_bytes(value: float | int | None) -> str:
    """1536 → «1.5 KiB». Для пустых значений возвращает тире."""
    if value is None or value <= 0:
        return "—"
    size = float(value)
    for unit in _UNITS:
        if size < 1024 or unit == _UNITS[-1]:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PiB"


def human_duration(seconds: float | int | None) -> str:
    """3725 → «1:02:05». None → «—»."""
    if seconds is None:
        return "—"
    total = int(round(float(seconds)))
    if total < 0:
        return "—"
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def human_speed(bytes_per_second: float | None) -> str:
    if not bytes_per_second or bytes_per_second <= 0:
        return "—"
    return f"{human_bytes(bytes_per_second)}/s"


def parse_rate(text: str) -> int | None:
    """«5M» → 5 MiB/s. Некорректная строка → None."""
    if not text or not text.strip():
        return None
    match = _RATE_RE.match(text)
    if not match:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    multiplier = {"": 1, "k": 1024, "m": 1024**2, "g": 1024**3}[match.group(2).lower()]
    return int(value * multiplier)


def _short_codec(value: Any) -> str:
    if not value or value == "none":
        return ""
    return str(value).split(".")[0].upper()


def _kind(fmt: dict[str, Any]) -> str | None:
    has_video = fmt.get("vcodec") not in (None, "none")
    has_audio = fmt.get("acodec") not in (None, "none")
    if has_video and has_audio:
        return "video+audio"
    if has_video:
        return "video"
    if has_audio:
        return "audio"
    return None


def _resolution(fmt: dict[str, Any], kind: str) -> str:
    height = fmt.get("height")
    width = fmt.get("width")
    if height:
        return f"{height}p"
    if width:
        return f"{width}px"
    if kind == "audio":
        abr = fmt.get("abr")
        if abr:
            return f"{float(abr):.0f} kbps"
    return "—"


def _note(fmt: dict[str, Any], kind: str) -> str:
    parts: list[str] = []
    if kind == "video":
        parts.append("видео без звука")
    elif kind == "audio":
        parts.append("только звук")
    note = fmt.get("format_note")
    if note:
        parts.append(str(note))
    dynamic_range = fmt.get("dynamic_range")
    if dynamic_range and dynamic_range != "SDR":
        parts.append(str(dynamic_range))
    return " · ".join(parts)


def pick_filesize(fmt: dict[str, Any]) -> int | None:
    for key in ("filesize", "filesize_approx"):
        value = fmt.get(key)
        if isinstance(value, (int, float)) and value > 0:
            return int(value)
    return None


def build_format_rows(info: dict[str, Any] | None, limit: int = 80) -> list[FormatRow]:
    """Собирает список строк: пресеты + реальные форматы из ответа yt-dlp."""
    rows: list[FormatRow] = list(PRESETS)
    if not info:
        return rows

    seen: set[str] = set()
    candidates: list[tuple[int, float, FormatRow]] = []
    for fmt in info.get("formats") or []:
        if not isinstance(fmt, dict):
            continue
        format_id = fmt.get("format_id")
        if not format_id or format_id in seen:
            continue
        if fmt.get("ext") == "mhtml":
            continue
        kind = _kind(fmt)
        if kind is None:
            continue
        seen.add(format_id)
        selector = format_id if kind != "video" else f"{format_id}+ba/b"
        fps_value = fmt.get("fps")
        fps = f"{int(float(fps_value))}" if fps_value else ""
        codec = _short_codec(fmt.get("vcodec")) or _short_codec(fmt.get("acodec"))
        if kind == "video+audio":
            codec = f"{_short_codec(fmt.get('vcodec'))} / {_short_codec(fmt.get('acodec'))}"
        height = int(fmt.get("height") or 0)
        tbr = float(fmt.get("tbr") or 0)
        row = FormatRow(
            format_id=format_id,
            selector=selector,
            resolution=_resolution(fmt, kind),
            fps=fps,
            codec=codec or "—",
            size=human_bytes(pick_filesize(fmt)),
            note=_note(fmt, kind),
            audio_only=kind == "audio",
        )
        candidates.append((height, tbr, row))

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    rows.extend(row for _, _, row in candidates[:limit])
    return rows
