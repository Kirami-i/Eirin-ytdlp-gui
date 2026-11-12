"""Тёмная тема оформления (QSS) с токенами цветов."""

from __future__ import annotations

COLORS = {
    "bg": "#101218",
    "surface": "#171a22",
    "surface_alt": "#1b1f29",
    "surface2": "#212633",
    "input": "#141821",
    "border": "#2b3140",
    "hover": "#293041",
    "text": "#e7eaf3",
    "muted": "#8b93a8",
    "muted2": "#5d6478",
    "accent": "#7c5cff",
    "accent_hover": "#9179ff",
    "selection": "#2c2a52",
    "success": "#3ddc97",
    "warning": "#ffb454",
    "danger": "#ff5c7a",
}

_TEMPLATE = """
* {
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 10pt;
    color: @text@;
}
QMainWindow, QDialog, QMessageBox {
    background: @bg@;
}
QWidget#Header {
    background: @surface@;
    border-bottom: 1px solid @border@;
}
QLabel#appTitle {
    font-size: 17pt;
    font-weight: 700;
    color: @text@;
}
QLabel#appSubtitle {
    color: @muted@;
    font-size: 9pt;
    padding-top: 5px;
}
QLabel#chip {
    background: @surface2@;
    border: 1px solid @border@;
    border-radius: 10px;
    padding: 4px 10px;
    color: @muted@;
    font-size: 8.5pt;
}
QLabel#chip[state="ok"] {
    color: @success@;
    border-color: @success@;
}
QLabel#chip[state="warn"] {
    color: @warning@;
    border-color: @warning@;
}
QLabel#sectionTitle {
    font-size: 11pt;
    font-weight: 600;
}
QFrame#card {
    background: @surface@;
    border: 1px solid @border@;
    border-radius: 12px;
}
QLabel#thumb {
    background: @surface2@;
    border-radius: 8px;
    color: @muted@;
}
QLabel#mediaTitle {
    font-size: 14pt;
    font-weight: 600;
}
QLabel#muted {
    color: @muted@;
}
QLineEdit, QComboBox, QSpinBox {
    background: @input@;
    border: 1px solid @border@;
    border-radius: 8px;
    padding: 7px 10px;
    selection-background-color: @accent@;
    selection-color: #ffffff;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border-color: @accent@;
}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {
    color: @muted2@;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background: @surface2@;
    border: 1px solid @border@;
    selection-background-color: @selection@;
    outline: none;
}
QPushButton {
    background: @surface2@;
    border: 1px solid @border@;
    border-radius: 8px;
    padding: 7px 14px;
}
QPushButton:hover {
    background: @hover@;
}
QPushButton:pressed {
    background: @border@;
}
QPushButton:disabled {
    color: @muted2@;
    background: @surface@;
}
QPushButton[class="primary"] {
    background: @accent@;
    border-color: @accent@;
    color: #ffffff;
    font-weight: 600;
}
QPushButton[class="primary"]:hover {
    background: @accent_hover@;
}
QPushButton[class="primary"]:disabled {
    background: @surface2@;
    border-color: @border@;
    color: @muted2@;
}
QPushButton[class="ghost"] {
    background: transparent;
}
QPushButton[class="ghost"]:hover {
    background: @surface2@;
}
QTableWidget {
    background: @surface@;
    border: 1px solid @border@;
    border-radius: 10px;
    gridline-color: @border@;
    alternate-background-color: @surface_alt@;
    selection-background-color: @selection@;
    selection-color: @text@;
    outline: none;
}
QTableWidget::item {
    padding: 4px 8px;
    border: none;
}
QTableWidget::item:selected {
    background: @selection@;
}
QHeaderView::section {
    background: @surface2@;
    color: @muted@;
    border: none;
    border-bottom: 1px solid @border@;
    padding: 7px 8px;
    font-weight: 600;
    font-size: 8.5pt;
}
QTableCornerButton::section {
    background: @surface2@;
    border: none;
}
QProgressBar {
    background: @input@;
    border: none;
    border-radius: 4px;
    text-align: center;
    font-size: 8pt;
    color: @text@;
}
QProgressBar::chunk {
    background: @accent@;
    border-radius: 4px;
}
QPlainTextEdit#logView {
    background: #0c0e13;
    border: 1px solid @border@;
    border-radius: 10px;
    color: #b8bfd2;
    font-family: "Cascadia Mono", "Consolas", monospace;
    font-size: 9pt;
    padding: 6px;
}
QGroupBox {
    border: 1px solid @border@;
    border-radius: 10px;
    margin-top: 16px;
    padding: 10px 12px 8px 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: @muted@;
    font-size: 9pt;
    font-weight: 600;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid @border@;
    border-radius: 4px;
    background: @input@;
}
QCheckBox::indicator:hover {
    border-color: @accent@;
}
QCheckBox::indicator:checked {
    background: @accent@;
    border-color: @accent@;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: @border@;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: @muted2@;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: @border@;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QSplitter::handle {
    background: transparent;
}
QSplitter::handle:vertical {
    height: 10px;
}
QSplitter::handle:horizontal {
    width: 10px;
}
QStatusBar {
    background: @surface@;
    border-top: 1px solid @border@;
    color: @muted@;
}
QStatusBar QLabel {
    color: @muted@;
    font-size: 9pt;
}
QToolTip {
    background: @surface2@;
    color: @text@;
    border: 1px solid @border@;
    padding: 4px 8px;
}
"""


def stylesheet() -> str:
    css = _TEMPLATE
    for key, value in COLORS.items():
        css = css.replace(f"@{key}@", value)
    return css
