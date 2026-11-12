"""Карточка с превью и метаданными выбранного медиа."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

from ...core.formats import human_duration
from ...core.jobs import MediaInfo

THUMB_WIDTH = 300
THUMB_HEIGHT = 169


class MediaCard(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self._thumb = QLabel("Нет превью")
        self._thumb.setObjectName("thumb")
        self._thumb.setFixedSize(THUMB_WIDTH, THUMB_HEIGHT)
        self._thumb.setAlignment(Qt.AlignCenter)

        self._title = QLabel("Вставьте ссылку и нажмите «Анализировать»")
        self._title.setObjectName("mediaTitle")
        self._title.setWordWrap(True)
        self._title.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self._meta = QLabel("")
        self._meta.setObjectName("muted")

        self._url = QLabel("")
        self._url.setObjectName("muted")
        self._url.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._url.setWordWrap(False)

        text_column = QVBoxLayout()
        text_column.setSpacing(6)
        text_column.addWidget(self._title)
        text_column.addWidget(self._meta)
        text_column.addWidget(self._url)
        text_column.addStretch(1)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.addWidget(self._thumb)
        layout.addLayout(text_column, 1)

    def set_info(self, info: MediaInfo) -> None:
        self._title.setText(info.title or "Без названия")
        parts: list[str] = []
        if info.uploader:
            parts.append(info.uploader)
        if info.duration:
            parts.append(human_duration(info.duration))
        if info.is_playlist:
            parts.append(f"плейлист · {info.entry_count} эл.")
        self._meta.setText("   •   ".join(parts))
        self._url.setText(info.webpage_url or info.url)
        self._url.setToolTip(info.webpage_url or info.url)

    def set_thumbnail(self, pixmap: QPixmap | None) -> None:
        if pixmap is None or pixmap.isNull():
            self._thumb.clear()
            self._thumb.setText("Нет превью")
            return
        self._thumb.setText("")
        self._thumb.setPixmap(pixmap)

    def clear(self) -> None:
        self._title.setText("Вставьте ссылку и нажмите «Анализировать»")
        self._meta.setText("")
        self._url.setText("")
        self._url.setToolTip("")
        self.set_thumbnail(None)
