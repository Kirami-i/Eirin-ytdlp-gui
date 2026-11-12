"""Точка входа приложения."""

from __future__ import annotations

import sys

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from . import APP_NAME, __version__
from .config import Settings
from .theme import stylesheet
from .ui.main_window import MainWindow


def main() -> int:
    QCoreApplication.setOrganizationName(APP_NAME)
    QCoreApplication.setApplicationName(APP_NAME)
    QCoreApplication.setApplicationVersion(__version__)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(stylesheet())

    window = MainWindow(Settings.load())
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
