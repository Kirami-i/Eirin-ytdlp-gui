"""Проверка внешних зависимостей (ffmpeg, JS-рантаймы, версия yt-dlp)."""

from __future__ import annotations

import shutil
from functools import lru_cache

import yt_dlp

JS_RUNTIME_EXECUTABLES = (
    ("deno", "deno"),
    ("node", "node"),
    ("bun", "bun"),
    ("quickjs", "qjs"),
)


def ffmpeg_path() -> str | None:
    return shutil.which("ffmpeg")


def ffprobe_path() -> str | None:
    return shutil.which("ffprobe")


@lru_cache(maxsize=1)
def detect_js_runtimes() -> dict[str, dict[str, str]]:
    """Находит установленные JS-рантаймы, которые понимает yt-dlp.

    YouTube всё сильнее зависит от JS: без рантайма часть форматов может
    отсутствовать. yt-dlp по умолчанию ищет только deno, поэтому остальные
    нужно передать явно через параметр ``js_runtimes``.
    """
    runtimes: dict[str, dict[str, str]] = {}
    for name, executable in JS_RUNTIME_EXECUTABLES:
        if shutil.which(executable):
            runtimes[name] = {}
    return runtimes


def ytdlp_version() -> str:
    try:
        return yt_dlp.version.__version__
    except AttributeError:  # pragma: no cover - на всякий случай
        return "unknown"
