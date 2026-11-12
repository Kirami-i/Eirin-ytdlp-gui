"""Таблица очереди загрузок с прогрессом."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
)

from ...core.formats import human_duration, human_speed
from ...core.jobs import DownloadJob
from ...theme import COLORS

HEADERS = ["#", "Название", "Формат", "Статус", "Прогресс", "Скорость", "Осталось"]

STATE_COLORS = {
    "queued": COLORS["muted"],
    "running": COLORS["accent"],
    "processing": COLORS["warning"],
    "done": COLORS["success"],
    "error": COLORS["danger"],
    "cancelled": COLORS["muted2"],
}


class QueueTable(QTableWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(0, len(HEADERS), parent)
        self.setHorizontalHeaderLabels(HEADERS)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setWordWrap(False)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        self.setColumnWidth(4, 130)
        self.setColumnWidth(5, 100)
        self.setColumnWidth(6, 90)
        self.verticalHeader().setDefaultSectionSize(34)

        self._row_by_id: dict[str, int] = {}

    # ------------------------------------------------------------------ данные

    def rebuild(self, jobs: list[DownloadJob]) -> None:
        self.setRowCount(0)
        self._row_by_id.clear()
        for number, job in enumerate(jobs, start=1):
            self._append(number, job)

    def update_job(self, job: DownloadJob) -> None:
        row = self._row_by_id.get(job.id)
        if row is None or row >= self.rowCount():
            return

        number_item = self.item(row, 0)
        if number_item is not None:
            number_item.setData(Qt.UserRole, job.id)

        title_item = self.item(row, 1)
        if title_item is not None:
            title_item.setText(job.title)
            title_item.setToolTip(job.url)

        format_item = self.item(row, 2)
        if format_item is not None:
            format_item.setText(job.format_label or job.selector)

        status_item = self.item(row, 3)
        if status_item is not None:
            status_item.setText(job.state_label)
            status_item.setForeground(QColor(STATE_COLORS.get(job.state, COLORS["text"])))

        bar = self.cellWidget(row, 4)
        if isinstance(bar, QProgressBar):
            bar.setValue(max(0, min(100, job.progress)))

        speed_item = self.item(row, 5)
        if speed_item is not None:
            speed_item.setText(human_speed(job.speed) if job.state == "running" else "—")

        eta_item = self.item(row, 6)
        if eta_item is not None:
            eta_item.setText(human_duration(job.eta) if job.state == "running" else "—")

        error_item = self.item(row, 1)
        if error_item is not None and job.error:
            error_item.setToolTip(job.error)

    def selected_job_ids(self) -> list[str]:
        ids: list[str] = []
        for index in self.selectionModel().selectedRows():
            item = self.item(index.row(), 0)
            if item is not None:
                job_id = item.data(Qt.UserRole)
                if job_id:
                    ids.append(str(job_id))
        return ids

    # ------------------------------------------------------------------ private

    def _append(self, number: int, job: DownloadJob) -> None:
        row = self.rowCount()
        self.insertRow(row)
        self._row_by_id[job.id] = row

        number_item = QTableWidgetItem(str(number))
        number_item.setData(Qt.UserRole, job.id)
        number_item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 0, number_item)

        self.setItem(row, 1, QTableWidgetItem(job.title))
        self.setItem(row, 2, QTableWidgetItem(job.format_label or job.selector))

        status_item = QTableWidgetItem(job.state_label)
        self.setItem(row, 3, status_item)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(job.progress)
        bar.setTextVisible(True)
        bar.setFormat("%p%")
        bar.setFixedHeight(16)
        self.setCellWidget(row, 4, bar)

        self.setItem(row, 5, QTableWidgetItem("—"))
        self.setItem(row, 6, QTableWidgetItem("—"))
        self.update_job(job)
