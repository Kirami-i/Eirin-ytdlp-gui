"""Сборка параметров для yt-dlp. Без зависимости от PySide6."""

from __future__ import annotations

from typing import Any

from ..config import Settings
from .formats import AUDIO_ONLY_SELECTOR, BEST_SELECTOR, parse_rate
from .system import detect_js_runtimes

DEFAULT_TEMPLATE = "%(title)s [%(id)s].%(ext)s"
SPONSOR_CATEGORIES = ["sponsor", "selfpromo", "interaction", "intro", "outro"]

# Форматы, в которые yt-dlp умеет встраивать обложку.
THUMBNAIL_AUDIO_FORMATS = frozenset({"mp3", "m4a", "opus", "flac", "ogg", "oga"})
THUMBNAIL_VIDEO_CONTAINERS = frozenset({"mp4", "mkv", "m4v", "mov", "mka"})


def thumbnail_embedding_supported(settings: Settings, *, audio_only: bool) -> bool:
    """Поддерживает ли итоговый контейнер встраивание обложки."""
    if audio_only:
        return (settings.audio_format or "").strip().lower() in THUMBNAIL_AUDIO_FORMATS
    container = (settings.container or "auto").strip().lower()
    return container in THUMBNAIL_VIDEO_CONTAINERS



def _common(settings: Settings) -> dict[str, Any]:
    options: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "windowsfilenames": True,
        "retries": max(0, int(settings.retries)),
        "fragment_retries": max(0, int(settings.retries)),
        "concurrent_fragment_downloads": 4,
        "overwrites": False,
        "continuedl": True,
        "ignoreerrors": False,
    }
    proxy = (settings.proxy or "").strip()
    if proxy:
        options["proxy"] = proxy
    if settings.cookies_browser:
        options["cookiesfrombrowser"] = (settings.cookies_browser,)
    rate = parse_rate(settings.rate_limit)
    if rate:
        options["ratelimit"] = rate
    runtimes = detect_js_runtimes()
    if runtimes:
        options["js_runtimes"] = runtimes
    if settings.allow_remote_components:
        # Официальный EJS-скрипт yt-dlp: нужен YouTube для полного списка форматов.
        options["remote_components"] = {"ejs:github"}
    return options


def build_probe_options(settings: Settings) -> dict[str, Any]:
    """Параметры для быстрого получения метаданных (без скачивания)."""
    options = _common(settings)
    options.update(
        {
            "skip_download": True,
            "extract_flat": False,
            "playlistend": 1,
            "noplaylist": False,
        }
    )
    return options


def build_download_options(
    settings: Settings,
    *,
    selector: str,
    audio_only: bool = False,
    playlist: bool | None = None,
) -> dict[str, Any]:
    """Полный набор параметров для одной задачи скачивания.

    Если ``playlist`` не передан, используется значение из настроек.
    """
    if playlist is None:
        playlist = settings.playlist
    template = (settings.filename_template or "").strip() or DEFAULT_TEMPLATE
    options = _common(settings)
    options.update(
        {
            "paths": {"home": settings.output_dir},
            "outtmpl": {"default": template},
            "noplaylist": not playlist,
            "format": AUDIO_ONLY_SELECTOR if audio_only else (selector or BEST_SELECTOR),
            "postprocessors": [],
            "writethumbnail": False,
        }
    )

    postprocessors: list[dict[str, Any]] = []
    if audio_only:
        postprocessors.append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": settings.audio_format or "mp3",
                "preferredquality": settings.audio_quality or "0",
            }
        )
    elif settings.container and settings.container != "auto":
        postprocessors.append(
            {
                "key": "FFmpegVideoRemuxer",
                # именно такое написание ключа использует yt-dlp
                "preferedformat": settings.container,
            }
        )

    if settings.write_subs:
        languages = [s.strip() for s in settings.subtitle_langs.split(",") if s.strip()]
        options["writesubtitles"] = True
        options["writeautomaticsub"] = True
        options["subtitleslangs"] = languages or ["ru", "en"]
        if settings.embed_subs:
            postprocessors.append(
                {"key": "FFmpegEmbedSubtitle", "already_have_subtitle": False}
            )

    if settings.embed_metadata:
        postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})

    if settings.embed_thumbnail and thumbnail_embedding_supported(
        settings, audio_only=audio_only
    ):
        options["writethumbnail"] = True
        postprocessors.append({"key": "EmbedThumbnail", "already_have_thumbnail": False})

    if settings.sponsorblock:
        postprocessors.append(
            {
                "key": "SponsorBlock",
                "categories": SPONSOR_CATEGORIES,
                "when": "after_filter",
            }
        )
        postprocessors.append(
            {
                "key": "ModifyChapters",
                "remove_sponsor_segments": SPONSOR_CATEGORIES,
            }
        )

    options["postprocessors"] = postprocessors
    return options
