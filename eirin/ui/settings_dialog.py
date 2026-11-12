"""Диалог настроек приложения."""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..config import Settings

AUDIO_QUALITIES = [
    ("0", "Лучшее (VBR)"),
    ("2", "Высокое"),
    ("5", "Среднее"),
    ("7", "Низкое"),
    ("128", "128 kbps"),
    ("192", "192 kbps"),
    ("320", "320 kbps"),
]

BROWSERS = [
    ("", "Не использовать"),
    ("chrome", "Chrome"),
    ("firefox", "Firefox"),
    ("edge", "Edge"),
    ("brave", "Brave"),
    ("opera", "Opera"),
    ("vivaldi", "Vivaldi"),
    ("chromium", "Chromium"),
]

CONTAINERS = [
    ("auto", "Как у источника"),
    ("mp4", "MP4"),
    ("mkv", "MKV"),
    ("webm", "WebM"),
]


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(580)
        self._settings = replace(settings)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)
        layout.addWidget(self._build_download_group())
        layout.addWidget(self._build_postprocess_group())
        layout.addWidget(self._build_network_group())

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        ok_button = buttons.button(QDialogButtonBox.Ok)
        if ok_button is not None:
            ok_button.setProperty("class", "primary")
            ok_button.setText("Сохранить")
        buttons.button(QDialogButtonBox.Cancel).setText("Отмена")
        layout.addSpacing(8)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------ группы

    def _build_download_group(self) -> QGroupBox:
        group = QGroupBox("Загрузка")
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignLeft)
        form.setSpacing(10)

        folder_row = QHBoxLayout()
        self._output_edit = QLineEdit(self._settings.output_dir)
        browse = QPushButton("Обзор…")
        browse.clicked.connect(self._browse_folder)
        folder_row.addWidget(self._output_edit, 1)
        folder_row.addWidget(browse)
        form.addRow("Папка:", folder_row)

        self._template_edit = QLineEdit(self._settings.filename_template)
        self._template_edit.setToolTip(
            "Шаблон имени файла yt-dlp, например: %(title)s [%(id)s].%(ext)s"
        )
        form.addRow("Шаблон имени:", self._template_edit)

        self._concurrent_spin = QSpinBox()
        self._concurrent_spin.setRange(1, 6)
        self._concurrent_spin.setValue(max(1, min(6, int(self._settings.concurrent_downloads))))
        form.addRow("Одновременных загрузок:", self._concurrent_spin)

        self._retries_spin = QSpinBox()
        self._retries_spin.setRange(0, 50)
        self._retries_spin.setValue(max(0, min(50, int(self._settings.retries))))
        form.addRow("Повторов при ошибке:", self._retries_spin)

        self._container_combo = QComboBox()
        for value, label in CONTAINERS:
            self._container_combo.addItem(label, value)
        self._select_data(self._container_combo, self._settings.container)
        form.addRow("Контейнер:", self._container_combo)

        return group

    def _build_postprocess_group(self) -> QGroupBox:
        group = QGroupBox("Аудио, субтитры и метаданные")
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignLeft)
        form.setSpacing(10)

        audio_row = QHBoxLayout()
        self._audio_format_combo = QComboBox()
        self._audio_format_combo.addItems(["mp3", "m4a", "opus", "flac", "wav"])
        self._audio_format_combo.setCurrentText(self._settings.audio_format)
        self._audio_quality_combo = QComboBox()
        for value, label in AUDIO_QUALITIES:
            self._audio_quality_combo.addItem(label, value)
        self._select_data(self._audio_quality_combo, self._settings.audio_quality)
        audio_row.addWidget(QLabel("Формат:"))
        audio_row.addWidget(self._audio_format_combo)
        audio_row.addSpacing(12)
        audio_row.addWidget(QLabel("Качество:"))
        audio_row.addWidget(self._audio_quality_combo, 1)
        form.addRow("Аудио:", audio_row)

        self._subs_check = QCheckBox("Скачивать субтитры")
        self._subs_check.setChecked(self._settings.write_subs)
        form.addRow("", self._subs_check)

        self._subs_langs_edit = QLineEdit(self._settings.subtitle_langs)
        self._subs_langs_edit.setPlaceholderText("ru,en")
        form.addRow("Языки субтитров:", self._subs_langs_edit)

        self._embed_subs_check = QCheckBox("Встраивать субтитры в файл")
        self._embed_subs_check.setChecked(self._settings.embed_subs)
        form.addRow("", self._embed_subs_check)

        self._thumb_check = QCheckBox("Встраивать обложку")
        self._thumb_check.setChecked(self._settings.embed_thumbnail)
        self._thumb_check.setToolTip(
            "Работает для MP3, M4A, Opus, FLAC, OGG, MP4 и MKV. "
            "Для WAV и WebM обложка не встраивается."
        )
        form.addRow("", self._thumb_check)

        self._metadata_check = QCheckBox("Записывать метаданные")
        self._metadata_check.setChecked(self._settings.embed_metadata)
        form.addRow("", self._metadata_check)

        self._sponsor_check = QCheckBox("Вырезать спонсорские вставки (SponsorBlock)")
        self._sponsor_check.setChecked(self._settings.sponsorblock)
        form.addRow("", self._sponsor_check)

        return group

    def _build_network_group(self) -> QGroupBox:
        group = QGroupBox("Сеть и доступ")
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignLeft)
        form.setSpacing(10)

        self._cookies_combo = QComboBox()
        for value, label in BROWSERS:
            self._cookies_combo.addItem(label, value)
        self._select_data(self._cookies_combo, self._settings.cookies_browser)
        self._cookies_combo.setToolTip("Брать cookies из профиля браузера для закрытых видео")
        form.addRow("Cookies из браузера:", self._cookies_combo)

        self._proxy_edit = QLineEdit(self._settings.proxy)
        self._proxy_edit.setPlaceholderText("http://127.0.0.1:8080 или socks5://…")
        form.addRow("Прокси:", self._proxy_edit)

        self._rate_edit = QLineEdit(self._settings.rate_limit)
        self._rate_edit.setPlaceholderText("например, 5M (без ограничения — пусто)")
        form.addRow("Ограничение скорости:", self._rate_edit)

        self._remote_components_check = QCheckBox("Загружать JS-компоненты yt-dlp (EJS)")
        self._remote_components_check.setChecked(self._settings.allow_remote_components)
        self._remote_components_check.setToolTip(
            "Официальный скрипт-решатель JS-задач YouTube с GitHub. "
            "Нужен для полного списка форматов; без него часть качества может отсутствовать."
        )
        form.addRow("", self._remote_components_check)

        return group

    # ------------------------------------------------------------------ логика

    def result_settings(self) -> Settings:
        settings = self._settings
        settings.output_dir = self._output_edit.text().strip() or settings.output_dir
        settings.filename_template = (
            self._template_edit.text().strip() or "%(title)s [%(id)s].%(ext)s"
        )
        settings.concurrent_downloads = self._concurrent_spin.value()
        settings.retries = self._retries_spin.value()
        settings.container = str(self._container_combo.currentData())
        settings.audio_format = self._audio_format_combo.currentText()
        settings.audio_quality = str(self._audio_quality_combo.currentData())
        settings.write_subs = self._subs_check.isChecked()
        settings.subtitle_langs = self._subs_langs_edit.text().strip() or "ru,en"
        settings.embed_subs = self._embed_subs_check.isChecked()
        settings.embed_thumbnail = self._thumb_check.isChecked()
        settings.embed_metadata = self._metadata_check.isChecked()
        settings.sponsorblock = self._sponsor_check.isChecked()
        settings.cookies_browser = str(self._cookies_combo.currentData() or "")
        settings.proxy = self._proxy_edit.text().strip()
        settings.rate_limit = self._rate_edit.text().strip()
        settings.allow_remote_components = self._remote_components_check.isChecked()
        return settings

    # ------------------------------------------------------------------ private

    def _browse_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Папка для загрузок", self._output_edit.text()
        )
        if folder:
            self._output_edit.setText(folder)

    @staticmethod
    def _select_data(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)
