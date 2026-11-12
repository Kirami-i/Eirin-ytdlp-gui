"""Таблица доступных форматов."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from ...core.formats import FormatRow

HEADERS = ["ID", "Разрешение", "FPS", "Кодек", "Размер", "Примечание"]


class FormatTable(QTableWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(0, len(HEADERS), parent)
        self.setHorizontalHeaderLabels(HEADERS)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setWordWrap(False)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        self.verticalHeader().setDefaultSectionSize(30)

        self._rows: list[FormatRow] = []

    def set_rows(self, rows: list[FormatRow]) -> None:
        self._rows = list(rows)
        self.setRowCount(0)
        for row in rows:
            index = self.rowCount()
            self.insertRow(index)
            values = [
                row.display_id,
                row.resolution,
                row.fps,
                row.codec,
                row.size,
                row.note,
            ]
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                if column == 0:
                    item.setData(Qt.UserRole, row.format_id)
                    item.setTextAlignment(Qt.AlignCenter)
                if column in (1, 2, 4):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.setItem(index, column, item)
        if rows:
            self.selectRow(0)

    def selected_format(self) -> FormatRow | None:
        indexes = self.selectionModel().selectedRows()
        if not indexes:
            return None
        row = indexes[0].row()
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None
