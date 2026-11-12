"""Фоновые задачи PySide6: анализ ссылки и скачивание."""

from __future__ import annotations

import threading
from dataclasses import replace
from typing import Any

import yt_dlp
from PySide6.QtCore import QThread, Signal

from ..config import Settings
from .jobs import DownloadJob, MediaInfo
from .options import (
    build_download_options,
    build_probe_options,
    thumbnail_embedding_supported,
)


class DownloadCancelled(Exception):
    """Поднимается из progress-hook, чтобы прервать загрузку."""


class _SignalLogger:
    """Прокси логгера yt-dlp в Qt-сигнал."""

    def __init__(self, emit) -> None:
        self._emit = emit

    def debug(self, message: str) -> None:
        if str(message).startswith("[debug]"):
            return
        self._emit(str(message))

    def info(self, message: str) -> None:
        self._emit(str(message))

    def warning(self, message: str) -> None:
        self._emit(f"⚠ {message}")

    def error(self, message: str) -> None:
        self._emit(f"✖ {message}")


def friendly_error(exc: BaseException) -> str:
    """Превращает техническую ошибку в понятный текст."""
    text = str(exc).strip()
    lowered = text.lower()
    if "ffmpeg" in lowered:
        return "Не найден ffmpeg. Установите ffmpeg и добавьте его в PATH.\n\n" + text
    if any(word in lowered for word in ("sign in", "login", "cookies", "bot")):
        return (
            "Источник требует авторизации. Укажите браузер с cookies в настройках "
            "или используйте другой источник.\n\n" + text
        )
    if "unsupported url" in lowered:
        return "Этот сайт не поддерживается yt-dlp.\n\n" + text
    return text or exc.__class__.__name__


class ProbeWorker(QThread):
    """Получает метаданные ссылки, ничего не скачивая."""

    finished_ok = Signal(object)  # MediaInfo
    failed = Signal(str)
    log = Signal(str)

    def __init__(self, url: str, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self._url = url
        self._settings = settings

    def run(self) -> None:  # noqa: D102
        options = build_probe_options(self._settings)
        options["logger"] = _SignalLogger(self.log.emit)
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(self._url, download=False)
        except Exception as exc:  # noqa: BLE001 - показываем пользователю
            self.failed.emit(friendly_error(exc))
            return
        if not info:
            self.failed.emit("Не удалось получить информацию о ссылке.")
            return
        self.finished_ok.emit(MediaInfo.from_info(self._url, info))


class DownloadWorker(QThread):
    """Скачивает один элемент очереди в отдельном потоке."""

    progress = Signal(object)  # dict
    log = Signal(str)
    finished_ok = Signal(str)  # путь к результату или папка
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, job: DownloadJob, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self._job = job
        self._settings = settings
        self._cancel = threading.Event()
        self._last_postprocessor = ""

    def cancel(self) -> None:
        self._cancel.set()

    def run(self) -> None:  # noqa: D102
        settings = self._settings
        if self._job.audio_format:
            settings = replace(settings, audio_format=self._job.audio_format)
        options = build_download_options(
            settings,
            selector=self._job.selector,
            audio_only=self._job.audio_only,
            playlist=self._job.playlist,
        )
        options["progress_hooks"] = [self._on_progress]
        options["postprocessor_hooks"] = [self._on_postprocess]
        options["logger"] = _SignalLogger(self.log.emit)

        warning = self._thumbnail_warning(settings)
        if warning:
            self.log.emit(warning)

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(self._job.url, download=True)
        except DownloadCancelled:
            self.cancelled.emit()
            return
        except Exception as exc:  # noqa: BLE001 - показываем пользователю
            if self._cancel.is_set():
                self.cancelled.emit()
            else:
                self.failed.emit(friendly_error(exc))
            return

        if self._cancel.is_set():
            self.cancelled.emit()
            return
        self.finished_ok.emit(self._result_path(info))

    def _result_path(self, info: Any) -> str:
        try:
            if not isinstance(info, dict):
                return ""
            if info.get("_type") == "playlist":
                return self._settings.output_dir
            downloads = info.get("requested_downloads") or []
            if downloads:
                return str(downloads[0].get("filepath") or downloads[0].get("filename") or "")
            return str(info.get("filepath") or info.get("_filename") or "")
        except Exception:  # noqa: BLE001 - путь не критичен
            return ""

    def _on_progress(self, data: dict[str, Any]) -> None:
        if self._cancel.is_set():
            raise DownloadCancelled()
        if not isinstance(data, dict):
            return
        status = data.get("status")
        payload: dict[str, Any] = {
            "status": status,
            "percent": None,
            "speed": None,
            "eta": None,
            "filename": "",
        }
        if status == "downloading":
            downloaded = data.get("downloaded_bytes") or 0
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            payload.update(
                speed=data.get("speed"),
                eta=data.get("eta"),
                filename=data.get("filename") or "",
            )
            if total:
                payload["percent"] = max(0.0, min(100.0, downloaded / total * 100))
        elif status == "finished":
            payload["percent"] = 100.0
            payload["filename"] = data.get("filename") or ""
        self.progress.emit(payload)

    def _thumbnail_warning(self, settings: Settings) -> str | None:
        if not settings.embed_thumbnail or thumbnail_embedding_supported(
            settings, audio_only=self._job.audio_only
        ):
            return None
        if self._job.audio_only:
            audio_format = (settings.audio_format or "").upper()
            return (
                f"⚠ Обложка не будет встроена: формат {audio_format} не поддерживает "
                "обложки (доступны MP3, M4A, Opus, FLAC, OGG)."
            )
        container = (settings.container or "auto").lower()
        if container == "auto":
            return (
                "⚠ Обложка не будет встроена: контейнер выбирается автоматически. "
                "Укажите MP4 или MKV в настройках, чтобы встраивать обложку."
            )
        return f"⚠ Обложка не будет встроена: контейнер {container.upper()} не поддерживает обложки."

    def _on_postprocess(self, data: dict[str, Any]) -> None:
        if self._cancel.is_set():
            raise DownloadCancelled()
        if isinstance(data, dict) and data.get("status") == "started":
            name = str(data.get("postprocessor") or "постобработка")
            if name != self._last_postprocessor:
                self._last_postprocessor = name
                self.log.emit(f"Постобработка: {name}")
            self.progress.emit({"status": "postprocessing", "percent": None})
