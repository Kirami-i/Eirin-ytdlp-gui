"""Генерирует docs/screenshot.png в offscreen-режиме (для README)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QCoreApplication, QPointF, QRectF, Qt  # noqa: E402
from PySide6.QtGui import (  # noqa: E402
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPixmap,
)
from PySide6.QtWidgets import QApplication  # noqa: E402

from eirin.config import Settings  # noqa: E402
from eirin.core.jobs import DownloadJob, MediaInfo  # noqa: E402
from eirin.core.system import ytdlp_version  # noqa: E402
from eirin.theme import stylesheet  # noqa: E402
from eirin.ui.main_window import MainWindow  # noqa: E402

QCoreApplication.setOrganizationName("Eirin")
QCoreApplication.setApplicationName("Eirin")

app = QApplication(sys.argv)
app.setStyle("Fusion")
app.setStyleSheet(stylesheet())

window = MainWindow(Settings(output_dir=str(Path.home() / "Downloads" / "Eirin")))
window.resize(1180, 960)
window.main_splitter.setSizes([590, 320])

info = MediaInfo(
    url="https://www.youtube.com/watch?v=demo",
    title="Пример видео: обзор форматов, кодеков и качества",
    uploader="Demo Channel",
    duration=754,
    webpage_url="https://www.youtube.com/watch?v=demo",
)
info.formats = {
    "formats": [
        {"format_id": "137", "ext": "mp4", "vcodec": "avc1.640028", "acodec": "none",
         "height": 1080, "fps": 30, "filesize": 148_000_000, "format_note": "1080p"},
        {"format_id": "248", "ext": "webm", "vcodec": "vp9", "acodec": "none",
         "height": 1080, "fps": 60, "filesize": 122_000_000, "format_note": "1080p60"},
        {"format_id": "22", "ext": "mp4", "vcodec": "avc1.64001F", "acodec": "mp4a.40.2",
         "height": 720, "fps": 30, "filesize": 74_000_000, "format_note": "720p"},
        {"format_id": "18", "ext": "mp4", "vcodec": "avc1.42001E", "acodec": "mp4a.40.2",
         "height": 360, "fps": 30, "filesize": 21_000_000, "format_note": "360p"},
        {"format_id": "140", "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2",
         "abr": 129, "filesize": 11_000_000, "format_note": "medium"},
    ]
}
window.url_edit.setText(info.url)
window._on_probe_ok(info)

cover = QPixmap(600, 338)
cover.fill(QColor("#1b1f29"))
painter = QPainter(cover)
gradient = QLinearGradient(QPointF(0, 0), QPointF(600, 338))
gradient.setColorAt(0.0, QColor("#7c5cff"))
gradient.setColorAt(1.0, QColor("#2b1f5e"))
painter.fillRect(cover.rect(), gradient)
triangle = QPainterPath()
triangle.moveTo(270, 130)
triangle.lineTo(270, 208)
triangle.lineTo(338, 169)
triangle.closeSubpath()
painter.setRenderHint(QPainter.Antialiasing)
painter.fillPath(triangle, QColor(255, 255, 255, 235))
font = QFont("Segoe UI", 11)
font.setBold(True)
painter.setFont(font)
painter.setPen(QColor(255, 255, 255, 200))
painter.drawText(QRectF(0, 250, 600, 40), Qt.AlignCenter, "DEMO PREVIEW")
painter.end()
window.media_card.set_thumbnail(window._crop_thumbnail(cover))

jobs = [
    DownloadJob(
        url="https://youtu.be/demo", title="Пример видео: обзор форматов, кодеков и качества",
        selector="bv*+ba/b", format_label="Лучшее качество", state="running",
        progress=63, speed=4.2 * 1024 * 1024, eta=95,
    ),
    DownloadJob(
        url="https://youtu.be/podcast", title="Подкаст — выпуск 42: про инструменты",
        selector="ba/b", format_label="Аудио · mp3", audio_only=True, state="done",
        progress=100,
    ),
    DownloadJob(
        url="https://youtu.be/playlist", title="Плейлист: лучшие моменты сезона",
        selector="137+ba/b", format_label="1080p", state="queued",
    ),
    DownloadJob(
        url="https://youtu.be/private", title="Закрытое видео (нужны cookies)",
        selector="bv*+ba/b", format_label="Лучшее качество", state="error",
        error="Источник требует авторизации. Укажите браузер с cookies в настройках.",
    ),
]
window._jobs = jobs
window.queue_table.rebuild(jobs)
window._update_status()

window.log_view.clear()
for line in [
    f"Eirin 0.1.0 · yt-dlp {ytdlp_version()}",
    "Анализ: https://www.youtube.com/watch?v=demo",
    "Найдено: Пример видео: обзор форматов, кодеков и качества",
    "В очередь: Пример видео: обзор форматов, кодеков и качества — Лучшее качество",
    "Старт: Пример видео: обзор форматов, кодеков и качества",
    "[download]  63.4% of ~148.00MiB at 4.20MiB/s ETA 00:35",
    "Постобработка: FFmpegMetadata",
]:
    window.append_log(line)

window.setAttribute(Qt.WA_DontShowOnScreen, True)
window.show()
for _ in range(5):
    app.processEvents()

out = Path(__file__).resolve().parents[1] / "docs" / "screenshot.png"
out.parent.mkdir(parents=True, exist_ok=True)
window.grab().save(str(out), "PNG")
print(f"saved {out} ({out.stat().st_size} bytes)", flush=True)

for job in jobs:
    job.state = "done"
window.close()
