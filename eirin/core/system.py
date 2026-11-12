"""Проверка внешних зависимостей (ffmpeg, версия yt-dlp)."""

from __future__ import annotations

import shutil

import yt_dlp


def ffmpeg_path() -> str | None:
    return shutil.which("ffmpeg")


def ffprobe_path() -> str | None:
    return shutil.which("ffprobe")


def ytdlp_version() -> str:
    try:
        return yt_dlp.version.__version__
    except AttributeError:  # pragma: no cover - на всякий случай
        return "unknown"
