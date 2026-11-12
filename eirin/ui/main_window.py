"""Главное окно приложения."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFontMetrics, QKeySequence, QPixmap, QShortcut
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from .. import APP_NAME, __version__
from ..config import Settings
from ..core.formats import BEST_SELECTOR, build_format_rows
from ..core.jobs import DownloadJob, MediaInfo
from ..core.service import DownloadWorker, ProbeWorker
from ..core.system import ffmpeg_path, ytdlp_version
from .settings_dialog import SettingsDialog
from .widgets.format_table import FormatTable
from .widgets.media_card import THUMB_HEIGHT, THUMB_WIDTH, MediaCard
from .widgets.queue_table import QueueTable


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.current_info: MediaInfo | None = None

        self._probe: ProbeWorker | None = None
        self._jobs: list[DownloadJob] = []
        self._workers: dict[str, DownloadWorker] = {}
        self._last_progress_update: dict[str, float] = {}
        self._network = QNetworkAccessManager(self)
        self._qt_settings = QSettings()

        self.setWindowTitle(f"{APP_NAME} — GUI для yt-dlp")
        self.resize(1180, 880)
        self.setMinimumSize(980, 720)
        self.setAcceptDrops(True)

        self._build_ui()
        self._install_shortcuts()
        self._restore_geometry()
        self._refresh_folder_label()
        self._refresh_dependency_chip()
        self._update_status()
        self.format_table.set_rows(build_format_rows(None))
        self.append_log(f"{APP_NAME} {__version__} · yt-dlp {ytdlp_version()}")
        if not ffmpeg_path():
            self.append_log(
                "⚠ ffmpeg не найден в PATH: объединение видео и звука, конвертация и "
                "встраивание обложек работать не будут."
            )

    # ------------------------------------------------------------------ разметка

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_header())

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 16, 20, 14)
        body_layout.setSpacing(14)
        body_layout.addWidget(self._build_url_row())

        self.main_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.addWidget(self._build_download_panel())
        self.main_splitter.addWidget(self._build_bottom_panel())
        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 2)
        self.main_splitter.setSizes([470, 330])
        body_layout.addWidget(self.main_splitter, 1)

        root_layout.addWidget(body, 1)
        self.setCentralWidget(root)

        self.setStatusBar(QStatusBar())
        self.status_label = QLabel()
        self.statusBar().addWidget(self.status_label)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("Header")
        row = QHBoxLayout(header)
        row.setContentsMargins(20, 10, 20, 10)
        row.setSpacing(10)

        title = QLabel(APP_NAME)
        title.setObjectName("appTitle")
        subtitle = QLabel("GUI для yt-dlp")
        subtitle.setObjectName("appSubtitle")

        self.dependency_chip = QLabel()
        self.dependency_chip.setObjectName("chip")

        settings_button = QPushButton("Настройки")
        settings_button.setProperty("class", "ghost")
        settings_button.clicked.connect(self.open_settings)

        row.addWidget(title)
        row.addWidget(subtitle)
        row.addStretch(1)
        row.addWidget(self.dependency_chip)
        row.addWidget(settings_button)
        return header

    def _build_url_row(self) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Вставьте ссылку на видео, плейлист или канал…")
        self.url_edit.setClearButtonEnabled(True)
        self.url_edit.returnPressed.connect(self.analyze)

        self.analyze_button = QPushButton("Анализировать")
        self.analyze_button.setProperty("class", "primary")
        self.analyze_button.setMinimumWidth(150)
        self.analyze_button.clicked.connect(self.analyze)

        row.addWidget(self.url_edit, 1)
        row.addWidget(self.analyze_button)
        return container

    def _build_download_panel(self) -> QWidget:
        panel = QWidget()
        column = QVBoxLayout(panel)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(10)

        self.media_card = MediaCard()
        column.addWidget(self.media_card)

        self.format_table = FormatTable()
        self.format_table.setMinimumHeight(170)
        self.format_table.itemSelectionChanged.connect(self._on_format_selected)
        column.addWidget(self.format_table, 1)

        options = QHBoxLayout()
        options.setSpacing(10)
        self.folder_label = QLabel()
        self.folder_label.setObjectName("muted")
        self.folder_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.folder_label.setMinimumWidth(120)

        folder_button = QPushButton("Папка…")
        folder_button.setProperty("class", "ghost")
        folder_button.clicked.connect(self.choose_folder)

        self.audio_check = QCheckBox("Только аудио")
        self.audio_check.toggled.connect(self._on_audio_toggled)

        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["mp3", "m4a", "opus", "flac", "wav"])
        self.audio_format_combo.setCurrentText(self.settings.audio_format)
        self.audio_format_combo.setVisible(False)

        self.playlist_check = QCheckBox("Весь плейлист")
        self.playlist_check.setVisible(False)

        self.add_button = QPushButton("Добавить в очередь")
        self.add_button.setProperty("class", "primary")
        self.add_button.setEnabled(False)
        self.add_button.clicked.connect(self.add_to_queue)

        options.addWidget(self.folder_label, 1)
        options.addWidget(folder_button)
        options.addWidget(self.audio_check)
        options.addWidget(self.audio_format_combo)
        options.addWidget(self.playlist_check)
        options.addWidget(self.add_button)
        column.addLayout(options)
        return panel

    def _build_bottom_panel(self) -> QWidget:
        splitter = QSplitter(Qt.Horizontal)

        queue_panel = QWidget()
        queue_layout = QVBoxLayout(queue_panel)
        queue_layout.setContentsMargins(0, 0, 0, 0)
        queue_layout.setSpacing(8)

        queue_header = QHBoxLayout()
        queue_title = QLabel("Очередь загрузок")
        queue_title.setObjectName("sectionTitle")
        start_button = QPushButton("Запустить")
        start_button.clicked.connect(self.start_queue)
        cancel_button = QPushButton("Отменить")
        cancel_button.clicked.connect(self.cancel_selected)
        clear_button = QPushButton("Очистить")
        clear_button.clicked.connect(self.clear_finished)
        open_button = QPushButton("Открыть папку")
        open_button.setProperty("class", "ghost")
        open_button.clicked.connect(self.open_output_dir)

        queue_header.addWidget(queue_title)
        queue_header.addStretch(1)
        queue_header.addWidget(start_button)
        queue_header.addWidget(cancel_button)
        queue_header.addWidget(clear_button)
        queue_header.addWidget(open_button)

        self.queue_table = QueueTable()
        self.queue_table.cellDoubleClicked.connect(self._on_queue_double_click)

        queue_layout.addLayout(queue_header)
        queue_layout.addWidget(self.queue_table, 1)

        log_panel = QWidget()
        log_layout = QVBoxLayout(log_panel)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(8)
        log_title = QLabel("Журнал")
        log_title.setObjectName("sectionTitle")
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(5000)
        self.log_view.setPlaceholderText("Здесь появится вывод yt-dlp…")
        log_layout.addWidget(log_title)
        log_layout.addWidget(self.log_view, 1)

        splitter.addWidget(queue_panel)
        splitter.addWidget(log_panel)
        splitter.setSizes([720, 380])
        return splitter

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.add_to_queue)
        QShortcut(QKeySequence("Ctrl+L"), self, activated=self.url_edit.setFocus)
        QShortcut(QKeySequence("F5"), self, activated=self.start_queue)

    # ------------------------------------------------------------------ анализ

    def analyze(self) -> None:
        url = self.url_edit.text().strip()
        if not url:
            self.url_edit.setFocus()
            return
        if self._probe is not None and self._probe.isRunning():
            return

        self.append_log(f"Анализ: {url}")
        self.analyze_button.setEnabled(False)
        self.analyze_button.setText("Анализ…")
        self.add_button.setEnabled(False)

        worker = ProbeWorker(url, self.settings, self)
        worker.finished_ok.connect(self._on_probe_ok)
        worker.failed.connect(self._on_probe_failed)
        worker.log.connect(self.append_log)
        worker.finished.connect(self._on_probe_done)
        self._probe = worker
        worker.start()

    def _on_probe_ok(self, info: MediaInfo) -> None:
        self.current_info = info
        self.media_card.set_info(info)
        self.format_table.set_rows(build_format_rows(info.formats))
        self.playlist_check.setVisible(info.is_playlist)
        self.playlist_check.setChecked(False)
        self.add_button.setEnabled(True)
        self._load_thumbnail(info.thumbnail)
        suffix = f" (плейлист, {info.entry_count} эл.)" if info.is_playlist else ""
        self.append_log(f"Найдено: {info.title}{suffix}")
        self._update_status()

    def _on_probe_failed(self, message: str) -> None:
        self.append_log(f"✖ {message}")
        self.media_card.clear()
        self.format_table.set_rows(build_format_rows(None))
        self.current_info = None
        self.add_button.setEnabled(False)

    def _on_probe_done(self) -> None:
        if self._probe is not None:
            self._probe.deleteLater()
            self._probe = None
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("Анализировать")

    def _on_format_selected(self) -> None:
        row = self.format_table.selected_format()
        if row is not None and row.audio_only:
            self.audio_check.setChecked(True)

    def _on_audio_toggled(self, checked: bool) -> None:
        self.audio_format_combo.setVisible(checked)

    # ------------------------------------------------------------------ очередь

    def add_to_queue(self) -> None:
        if self.current_info is None:
            return
        row = self.format_table.selected_format()
        audio_only = self.audio_check.isChecked()
        if audio_only:
            selector = "ba/b"
            label = f"Аудио · {self.audio_format_combo.currentText()}"
        else:
            selector = row.selector if row is not None else BEST_SELECTOR
            label = row.resolution if row is not None else "Лучшее качество"

        job = DownloadJob(
            url=self.current_info.url,
            title=self.current_info.title,
            selector=selector,
            format_label=label,
            audio_only=audio_only,
            audio_format=self.audio_format_combo.currentText() if audio_only else "",
            playlist=self.playlist_check.isVisible() and self.playlist_check.isChecked(),
        )
        self._jobs.append(job)
        self.queue_table.rebuild(self._jobs)
        self.append_log(f"В очередь: {job.title} — {label}")
        self._update_status()
        self._maybe_start_next()

    def start_queue(self) -> None:
        if not any(job.state == "queued" for job in self._jobs):
            self.append_log("Нет задач в очереди.")
            return
        self._maybe_start_next()

    def cancel_selected(self) -> None:
        for job_id in self.queue_table.selected_job_ids():
            job = self._job(job_id)
            if job is None:
                continue
            if job.state == "queued":
                job.state = "cancelled"
                self.queue_table.update_job(job)
                self.append_log(f"Отменено: {job.title}")
            elif job.is_active and job_id in self._workers:
                self._workers[job_id].cancel()
                self.append_log(f"Останавливаю: {job.title}")
        self._update_status()

    def clear_finished(self) -> None:
        self._jobs = [job for job in self._jobs if not job.is_final]
        self.queue_table.rebuild(self._jobs)
        self._update_status()

    def _maybe_start_next(self) -> None:
        limit = max(1, int(self.settings.concurrent_downloads))
        active = sum(1 for job in self._jobs if job.is_active)
        for job in self._jobs:
            if active >= limit:
                break
            if job.state == "queued":
                self._start_job(job)
                active += 1
        self._update_status()

    def _start_job(self, job: DownloadJob) -> None:
        worker = DownloadWorker(job, self.settings, self)
        # Подключаем именно методы QObject: так сигналы из рабочего потока
        # гарантированно доставляются в GUI-поток через очередь событий.
        worker.progress.connect(self._on_worker_progress)
        worker.log.connect(self.append_log)
        worker.finished_ok.connect(self._on_worker_finished_ok)
        worker.failed.connect(self._on_worker_failed)
        worker.cancelled.connect(self._on_worker_cancelled)
        worker.finished.connect(self._on_worker_thread_finished)
        self._workers[job.id] = worker

        job.state = "running"
        job.progress = 0
        job.speed = None
        job.eta = None
        job.error = ""
        self.queue_table.update_job(job)
        self.append_log(f"Старт: {job.title}")
        worker.start()

    def _worker_id(self, worker: object) -> str | None:
        return next(
            (job_id for job_id, candidate in self._workers.items() if candidate is worker),
            None,
        )

    def _on_worker_progress(self, payload: dict) -> None:
        job_id = self._worker_id(self.sender())
        if job_id:
            self._on_progress(job_id, payload)

    def _on_worker_finished_ok(self, path: str) -> None:
        job_id = self._worker_id(self.sender())
        if job_id:
            self._on_job_finished(job_id, path)

    def _on_worker_failed(self, message: str) -> None:
        job_id = self._worker_id(self.sender())
        if job_id:
            self._on_job_failed(job_id, message)

    def _on_worker_cancelled(self) -> None:
        job_id = self._worker_id(self.sender())
        if job_id:
            self._on_job_cancelled(job_id)

    def _on_worker_thread_finished(self) -> None:
        job_id = self._worker_id(self.sender())
        if job_id:
            self._cleanup_worker(job_id)

    def _cleanup_worker(self, job_id: str) -> None:
        worker = self._workers.pop(job_id, None)
        if worker is not None:
            worker.deleteLater()
        self._last_progress_update.pop(job_id, None)
        self._update_status()

    def _on_progress(self, job_id: str, payload: dict) -> None:
        job = self._job(job_id)
        if job is None:
            return
        status = payload.get("status")
        percent = payload.get("percent")
        if percent is not None:
            job.progress = int(percent)
        if status == "postprocessing":
            job.state = "processing"
        job.speed = payload.get("speed")
        job.eta = payload.get("eta")

        now = time.monotonic()
        last = self._last_progress_update.get(job_id, 0.0)
        if status != "downloading" or now - last >= 0.25:
            self._last_progress_update[job_id] = now
            self.queue_table.update_job(job)

    def _on_job_finished(self, job_id: str, path: str) -> None:
        job = self._job(job_id)
        if job is None:
            return
        job.state = "done"
        job.progress = 100
        job.speed = None
        job.eta = None
        job.filepath = path
        self.queue_table.update_job(job)
        self.append_log(f"Готово: {job.title}" + (f" → {path}" if path else ""))
        self._maybe_start_next()

    def _on_job_failed(self, job_id: str, message: str) -> None:
        job = self._job(job_id)
        if job is None:
            return
        job.state = "error"
        job.error = message
        self.queue_table.update_job(job)
        self.append_log(f"✖ Ошибка «{job.title}»: {message}")
        self._maybe_start_next()

    def _on_job_cancelled(self, job_id: str) -> None:
        job = self._job(job_id)
        if job is None:
            return
        job.state = "cancelled"
        job.speed = None
        job.eta = None
        self.queue_table.update_job(job)
        self.append_log(f"Отменено: {job.title}")
        self._maybe_start_next()

    def _job(self, job_id: str) -> DownloadJob | None:
        return next((job for job in self._jobs if job.id == job_id), None)

    def _on_queue_double_click(self, row: int, _column: int) -> None:
        item = self.queue_table.item(row, 0)
        if item is None:
            return
        job = self._job(str(item.data(Qt.UserRole)))
        if job is not None and job.filepath and Path(job.filepath).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(job.filepath))
        else:
            self.open_output_dir()

    # ------------------------------------------------------------------ прочее

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Папка для загрузок", self.settings.output_dir
        )
        if folder:
            self.settings.output_dir = folder
            self.settings.save()
            self._refresh_folder_label()

    def open_output_dir(self) -> None:
        path = Path(self.settings.output_dir)
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.Accepted:
            self.settings = dialog.result_settings()
            self.settings.save()
            self._refresh_folder_label()
            self.audio_format_combo.setCurrentText(self.settings.audio_format)
            self.append_log("Настройки сохранены.")
            self._refresh_dependency_chip()
            self._update_status()

    def append_log(self, text: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        for line in str(text).splitlines():
            self.log_view.appendPlainText(f"[{stamp}] {line}")

    def _refresh_folder_label(self) -> None:
        path = self.settings.output_dir
        metrics = QFontMetrics(self.folder_label.font())
        self.folder_label.setText(metrics.elidedText(path, Qt.ElideMiddle, 380))
        self.folder_label.setToolTip(path)

    def _refresh_dependency_chip(self) -> None:
        ffmpeg = ffmpeg_path()
        if ffmpeg:
            self.dependency_chip.setText("ffmpeg: найден")
            self.dependency_chip.setProperty("state", "ok")
            self.dependency_chip.setToolTip(ffmpeg)
        else:
            self.dependency_chip.setText("ffmpeg: не найден")
            self.dependency_chip.setProperty("state", "warn")
            self.dependency_chip.setToolTip(
                "Без ffmpeg не работает объединение дорожек, конвертация и обложки"
            )
        self.dependency_chip.style().unpolish(self.dependency_chip)
        self.dependency_chip.style().polish(self.dependency_chip)

    def _update_status(self) -> None:
        active = sum(1 for job in self._jobs if job.is_active)
        queued = sum(1 for job in self._jobs if job.state == "queued")
        done = sum(1 for job in self._jobs if job.state == "done")
        self.status_label.setText(
            f"yt-dlp {ytdlp_version()}   ·   задач: {len(self._jobs)} "
            f"(активных {active}, в очереди {queued}, готово {done})"
        )

    def _load_thumbnail(self, url: str) -> None:
        self.media_card.set_thumbnail(None)
        if not url:
            return
        request = QNetworkRequest(QUrl(url))
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, "Mozilla/5.0 Eirin")
        reply = self._network.get(request)
        reply.finished.connect(lambda current=reply: self._on_thumbnail_ready(current))

    def _on_thumbnail_ready(self, reply: QNetworkReply) -> None:
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                return
            pixmap = QPixmap()
            if pixmap.loadFromData(bytes(reply.readAll())):
                self.media_card.set_thumbnail(self._crop_thumbnail(pixmap))
        finally:
            reply.deleteLater()

    @staticmethod
    def _crop_thumbnail(pixmap: QPixmap) -> QPixmap:
        scaled = pixmap.scaled(
            THUMB_WIDTH,
            THUMB_HEIGHT,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        x = max(0, (scaled.width() - THUMB_WIDTH) // 2)
        y = max(0, (scaled.height() - THUMB_HEIGHT) // 2)
        return scaled.copy(x, y, THUMB_WIDTH, THUMB_HEIGHT)

    # ------------------------------------------------------------------ события

    def dragEnterEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802 - Qt API
        mime = event.mimeData()
        text = ""
        if mime.hasUrls() and mime.urls():
            text = mime.urls()[0].toString()
        elif mime.hasText():
            text = mime.text()
        text = text.strip()
        if text:
            self.url_edit.setText(text)
            self.analyze()

    def _restore_geometry(self) -> None:
        geometry = self._qt_settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        active = [job for job in self._jobs if job.is_active]
        if active:
            answer = QMessageBox.question(
                self,
                "Идут загрузки",
                "Остановить активные загрузки и закрыть приложение?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                event.ignore()
                return
            for worker in self._workers.values():
                worker.cancel()
            for worker in self._workers.values():
                worker.wait(3000)
        self._qt_settings.setValue("window/geometry", self.saveGeometry())
        self.settings.save()
        super().closeEvent(event)
