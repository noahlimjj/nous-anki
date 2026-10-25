"""
Nous Design Theme & Styling
Provides unified typography, colors, and QSS stylesheets matching Nous.
"""

import os
import glob
from typing import Optional

# Nous Color Palette
CANVAS_BG = "#f8f9fb"
CARD_BG = "#ffffff"
CARD_BORDER = "#ebe8f3"
INK = "#363f51"
SOFT = "#7d8ca8"
FAINT = "#a8b3c7"
LINE = "#ebe8f3"

# Accents
ACCENT_PURPLE = "#8B7FB8"
ACCENT_PURPLE_HOVER = "#7b6fa6"
ACCENT_PURPLE_ACTIVE = "#6a5e95"
ACCENT_INK = "#5f5390"
ACCENT_WASH = "#f1eef8"
ACCENT_WASH_BORDER = "#e2ddf0"
ACCENT_WASH_HOVER = "#eae5f5"

# Focus Teal
FOCUS_TEAL = "#5FA8A3"
FOCUS_TEAL_HOVER = "#4f9691"
FOCUS_TEAL_ACTIVE = "#3f7f7a"

_FONTS_INITIALIZED = False


def ensure_fonts_loaded():
    """Loads bundled Satoshi font weights into Qt font database."""
    global _FONTS_INITIALIZED
    if _FONTS_INITIALIZED:
        return

    try:
        from PyQt6.QtGui import QFontDatabase
    except ImportError:
        try:
            from aqt.qt import QFontDatabase
        except ImportError:
            return

    fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
    if os.path.isdir(fonts_dir):
        # Register TTF first, then WOFF2
        for pattern in ["*.ttf", "*.woff2"]:
            for fpath in sorted(glob.glob(os.path.join(fonts_dir, pattern))):
                QFontDatabase.addApplicationFont(fpath)

    _FONTS_INITIALIZED = True


NOUS_STYLESHEET = """
* {
    font-family: "Satoshi", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

QWidget {
    color: #363f51;
}

QDockWidget {
    background-color: #f8f9fb;
    color: #363f51;
}

QDialog {
    background-color: #f8f9fb;
    color: #363f51;
}

/* CARDS */
QFrame.treeCard, QFrame.timerCard, QFrame.nousCard {
    background-color: #ffffff;
    border: 1px solid #ebe8f3;
    border-radius: 16px;
    padding: 10px;
}

/* TYPOGRAPHY */
QLabel.treeName {
    font-size: 16px;
    font-weight: 500;
    color: #363f51;
    letter-spacing: 0.01em;
}

QLabel.timeDisplay {
    font-size: 34px;
    font-weight: 300;
    color: #363f51;
    letter-spacing: -0.02em;
}

QLabel.subtitle {
    font-size: 11px;
    font-weight: 500;
    color: #7d8ca8;
}

QLabel.tierBadge {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    color: #ffffff;
    border-radius: 10px;
    padding: 2px 8px;
    letter-spacing: 0.04em;
}

/* PROGRESS BAR */
QProgressBar {
    border: none;
    border-radius: 6px;
    text-align: center;
    font-size: 10px;
    font-weight: 600;
    height: 10px;
    background-color: #f1eef8;
    color: #5f5390;
}

QProgressBar::chunk {
    border-radius: 6px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5FA8A3, stop:1 #42958f);
}

/* BUTTONS */
QPushButton.cityButton, QPushButton.tealButton {
    background-color: #5FA8A3;
    color: #ffffff;
    font-weight: 500;
    font-size: 12px;
    border-radius: 15px;
    padding: 6px 14px;
    border: none;
    letter-spacing: 0.01em;
}
QPushButton.cityButton:hover, QPushButton.tealButton:hover {
    background-color: #4f9691;
}
QPushButton.cityButton:pressed, QPushButton.tealButton:pressed {
    background-color: #3f7f7a;
}

QPushButton.primaryButton {
    background-color: #8B7FB8;
    color: #ffffff;
    font-weight: 500;
    font-size: 11px;
    border-radius: 14px;
    padding: 5px 13px;
    border: none;
    letter-spacing: 0.01em;
}
QPushButton.primaryButton:hover {
    background-color: #7b6fa6;
}
QPushButton.primaryButton:pressed {
    background-color: #6a5e95;
}

QPushButton.actionButton, QPushButton.secondaryButton {
    background-color: #f1eef8;
    color: #5f5390;
    font-weight: 500;
    font-size: 11px;
    border: 1px solid #e2ddf0;
    border-radius: 14px;
    padding: 5px 12px;
}
QPushButton.actionButton:hover, QPushButton.secondaryButton:hover {
    background-color: #eae5f5;
    border-color: #8B7FB8;
}
QPushButton.actionButton:pressed, QPushButton.secondaryButton:pressed {
    background-color: #ded6f0;
}

QPushButton.iconButton {
    background-color: #ffffff;
    color: #5f5390;
    border: 1px solid #ebe8f3;
    border-radius: 12px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 500;
}
QPushButton.iconButton:hover {
    background-color: #f1eef8;
    border-color: #8B7FB8;
}

/* DROPDOWN BUTTONS (QComboBox) */
QComboBox {
    background-color: #f1eef8;
    color: #5f5390;
    border: 1px solid #e2ddf0;
    border-radius: 14px;
    padding: 5px 26px 5px 12px;
    min-height: 18px;
    font-size: 11px;
    font-weight: 500;
}
QComboBox:hover {
    background-color: #eae5f5;
    border-color: #8B7FB8;
}
QComboBox:focus {
    border: 1.5px solid #8B7FB8;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: none;
    border-top-right-radius: 14px;
    border-bottom-right-radius: 14px;
}
QComboBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #8B7FB8;
    margin-right: 8px;
}
QComboBox::down-arrow:on {
    border-top: none;
    border-bottom: 5px solid #8B7FB8;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #ebe8f3;
    border-radius: 12px;
    padding: 4px;
    selection-background-color: #f1eef8;
    selection-color: #5f5390;
    color: #363f51;
    font-size: 12px;
    outline: none;
}
QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    border-radius: 8px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #f8f6fc;
    color: #5f5390;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #f1eef8;
    color: #5f5390;
}

/* INPUTS */
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #ebe8f3;
    border-radius: 13px;
    padding: 5px 12px;
    color: #363f51;
    font-size: 12px;
}
QLineEdit:focus {
    border: 1.5px solid #8B7FB8;
}

QTextEdit, QTextBrowser {
    background-color: #ffffff;
    border: 1px solid #ebe8f3;
    border-radius: 12px;
    padding: 8px 10px;
    color: #363f51;
    font-size: 12px;
}
QTextEdit:focus, QTextBrowser:focus {
    border: 1.5px solid #8B7FB8;
}

/* TABS */
QTabWidget::pane {
    border: 1px solid #ebe8f3;
    background-color: #ffffff;
    border-radius: 16px;
    padding: 6px;
    margin-top: -1px;
}
QTabBar {
    background: transparent;
}
QTabBar::tab {
    font-size: 11px;
    font-weight: 500;
    color: #7d8ca8;
    background-color: transparent;
    padding: 5px 12px;
    border-radius: 12px;
    margin-right: 3px;
    margin-bottom: 3px;
    border: 1px solid transparent;
}
QTabBar::tab:hover {
    color: #5f5390;
    background-color: #f8f6fc;
}
QTabBar::tab:selected {
    color: #5f5390;
    background-color: #f1eef8;
    border: 1px solid #e2ddf0;
    font-weight: 600;
}

/* GROUP BOX & FORM */
QGroupBox {
    font-size: 12px;
    font-weight: 500;
    color: #5f5390;
    border: 1px solid #ebe8f3;
    border-radius: 14px;
    margin-top: 12px;
    padding: 14px 10px 10px 10px;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}

QSpinBox {
    background-color: #ffffff;
    border: 1px solid #ebe8f3;
    border-radius: 12px;
    padding: 4px 8px;
    color: #363f51;
}
QSpinBox:focus {
    border: 1.5px solid #8B7FB8;
}

/* SCROLLBAR */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #d8d3e8;
    min-height: 20px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #8B7FB8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
