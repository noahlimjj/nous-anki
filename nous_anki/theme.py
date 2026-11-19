"""
Nous Design Theme & Styling
Provides unified Satoshi typography, colors, and QSS stylesheets matching Nous.
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
FONT_FAMILY = "Satoshi"


def is_night_mode() -> bool:
    """Detects whether Anki is currently in Dark / Night Mode."""
    try:
        from aqt.theme import theme_manager
        return bool(getattr(theme_manager, "night_mode", False))
    except Exception:
        return False


def ensure_fonts_loaded() -> str:
    """Loads bundled Satoshi font weights into Qt font database and returns family name."""
    global _FONTS_INITIALIZED, FONT_FAMILY
    if _FONTS_INITIALIZED:
        return FONT_FAMILY

    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QFontDatabase
    except ImportError:
        try:
            from aqt.qt import QApplication, QFontDatabase
        except ImportError:
            return FONT_FAMILY

    if not QApplication.instance():
        return FONT_FAMILY

    fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
    loaded_families = []
    if os.path.isdir(fonts_dir):
        # Load TTF files first (optimal for Desktop Qt CoreText rendering), then WOFF2 as fallback
        ttf_files = sorted(glob.glob(os.path.join(fonts_dir, "*.ttf")))
        target_files = ttf_files if ttf_files else sorted(glob.glob(os.path.join(fonts_dir, "*.woff2")))
        for fpath in target_files:
            try:
                fid = QFontDatabase.addApplicationFont(fpath)
                if fid != -1:
                    fams = QFontDatabase.applicationFontFamilies(fid)
                    if fams:
                        loaded_families.extend(fams)
            except Exception:
                pass

    if loaded_families:
        FONT_FAMILY = loaded_families[0]
    _FONTS_INITIALIZED = True
    return FONT_FAMILY


def satoshi_font(size: int = 11, weight: int = 400):
    """Creates a QFont instance explicitly bound to the loaded Satoshi family."""
    fam = ensure_fonts_loaded()
    try:
        from PyQt6.QtGui import QFont
    except ImportError:
        from aqt.qt import QFont
    f = QFont(fam, size)
    try:
        if weight <= 300:
            f.setWeight(QFont.Weight.Light)
        elif weight < 500:
            f.setWeight(QFont.Weight.Normal)
        elif weight < 700:
            f.setWeight(QFont.Weight.Medium)
        else:
            f.setWeight(QFont.Weight.Bold)
    except Exception:
        pass
    return f


def apply_satoshi_to_widget_tree(root_widget):
    """Recursively applies Satoshi QFont to widget and all children so CoreText never falls back."""
    try:
        from PyQt6.QtWidgets import QWidget
    except ImportError:
        try:
            from aqt.qt import QWidget
        except ImportError:
            return
    if root_widget is None:
        return
    try:
        base_font = satoshi_font(11, 400)
        root_widget.setFont(base_font)
        for child in root_widget.findChildren(QWidget):
            cf = child.font()
            cf.setFamily(FONT_FAMILY)
            child.setFont(cf)
    except Exception:
        pass


def get_nous_stylesheet(is_dark: Optional[bool] = None) -> str:
    """Generates Nous stylesheet adapted dynamically to light or dark mode."""
    fam = ensure_fonts_loaded()
    if is_dark is None:
        is_dark = is_night_mode()

    if is_dark:
        canvas_bg = "#14151a"
        card_bg = "#1e2028"
        card_border = "#2d303e"
        ink = "#e2e8f0"
        soft = "#94a3b8"
        wash_bg = "#272536"
        wash_border = "#3d3854"
        wash_hover = "#322f44"
        accent_ink = "#c4b5fd"
        input_bg = "#181920"
        tab_bar_bg = "#232230"
        tab_sel_bg = "#1e2028"
    else:
        canvas_bg = "#f6f5fa"
        card_bg = "#ffffff"
        card_border = "#ebe8f3"
        ink = "#363f51"
        soft = "#7d8ca8"
        wash_bg = "#f1eef8"
        wash_border = "#e2ddf0"
        wash_hover = "#eae5f5"
        accent_ink = "#5f5390"
        input_bg = "#ffffff"
        tab_bar_bg = "#efeif8"
        tab_bar_bg = "#f1eef8"
        tab_sel_bg = "#ffffff"

    # Single font-family name in QSS ensures Qt QFontInfo.exactMatch() == True on macOS
    return f"""
* {{
    font-family: "{fam}";
}}

QWidget {{
    font-family: "{fam}";
    color: {ink};
}}

QDockWidget {{
    background-color: {canvas_bg};
    color: {ink};
    font-family: "{fam}";
}}

QWidget#nousDockContainer {{
    background-color: {canvas_bg};
}}

QDialog {{
    background-color: {canvas_bg};
    color: {ink};
    font-family: "{fam}";
}}

/* CARDS */
QFrame.treeCard, QFrame.timerCard, QFrame.nousCard, QFrame.accountCard {{
    background-color: {card_bg};
    border: 1px solid {card_border};
    border-radius: 18px;
}}

/* TYPOGRAPHY */
QLabel.treeName {{
    font-family: "{fam}";
    font-size: 16px;
    font-weight: 500;
    color: {ink};
}}

QLabel.treeBlurb {{
    font-family: "{fam}";
    font-size: 11px;
    font-weight: 300;
    color: {soft};
}}

QLabel.timeDisplay {{
    font-family: "{fam}";
    font-size: 28px;
    font-weight: 300;
    color: {ink};
}}

QLabel.subtitle {{
    font-family: "{fam}";
    font-size: 11px;
    font-weight: 400;
    color: {soft};
}}

QLabel.tierBadge {{
    font-family: "{fam}";
    font-size: 10px;
    font-weight: 500;
    border-radius: 10px;
    padding: 3px 9px;
}}

/* PROGRESS BAR */
QProgressBar {{
    border: none;
    border-radius: 4px;
    text-align: center;
    font-size: 1px;
    color: transparent;
    min-height: 8px;
    max-height: 8px;
    background-color: {wash_bg};
}}

QProgressBar::chunk {{
    border-radius: 4px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5FA8A3, stop:0.6 #4b9c96, stop:1 #8B7FB8);
}}

/* BUTTONS */
QPushButton {{
    font-family: "{fam}";
}}

QPushButton.cityButton, QPushButton.tealButton {{
    background-color: #5FA8A3;
    color: #ffffff;
    font-weight: 500;
    font-size: 11px;
    border-radius: 13px;
    padding: 6px 13px;
    border: none;
}}
QPushButton.cityButton:hover, QPushButton.tealButton:hover {{
    background-color: #4f9691;
}}
QPushButton.cityButton:pressed, QPushButton.tealButton:pressed {{
    background-color: #3f7f7a;
}}

QPushButton.primaryButton {{
    background-color: #8B7FB8;
    color: #ffffff;
    font-weight: 500;
    font-size: 11px;
    border-radius: 13px;
    padding: 6px 13px;
    border: none;
}}
QPushButton.primaryButton:hover {{
    background-color: #7b6fa6;
}}
QPushButton.primaryButton:pressed {{
    background-color: #6a5e95;
}}

QPushButton.actionButton, QPushButton.secondaryButton {{
    background-color: {wash_bg};
    color: {accent_ink};
    font-weight: 500;
    font-size: 11px;
    border: 1px solid {wash_border};
    border-radius: 13px;
    padding: 5px 11px;
}}
QPushButton.actionButton:hover, QPushButton.secondaryButton:hover {{
    background-color: {wash_hover};
    border-color: #8B7FB8;
}}
QPushButton.actionButton:pressed, QPushButton.secondaryButton:pressed {{
    background-color: {wash_border};
}}

QPushButton.ghostLinkButton {{
    background-color: transparent;
    color: {soft};
    font-weight: 500;
    font-size: 11px;
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 5px 10px;
}}
QPushButton.ghostLinkButton:hover {{
    color: {accent_ink};
    background-color: {wash_bg};
    border-color: {wash_border};
}}

QPushButton.iconButton {{
    background-color: {card_bg};
    color: {accent_ink};
    border: 1px solid {card_border};
    border-radius: 12px;
    padding: 3px 7px;
    font-size: 11px;
    font-weight: 500;
}}
QPushButton.iconButton:hover {{
    background-color: {wash_bg};
    border-color: #8B7FB8;
}}

/* TIMER MODE PILLS */
QPushButton.modePill {{
    background-color: transparent;
    color: {soft};
    border: none;
    border-radius: 10px;
    padding: 4px 9px;
    font-size: 11px;
    font-weight: 500;
}}
QPushButton.modePill:hover {{
    color: {accent_ink};
    background-color: {wash_hover};
}}
QPushButton.modePillActive {{
    background-color: {tab_sel_bg};
    color: {accent_ink};
    border: 1px solid {wash_border};
    border-radius: 10px;
    padding: 4px 9px;
    font-size: 11px;
    font-weight: 500;
}}

/* DROPDOWN BUTTONS (QComboBox) */
QComboBox {{
    font-family: "{fam}";
    background-color: {wash_bg};
    color: {accent_ink};
    border: 1px solid {wash_border};
    border-radius: 13px;
    padding: 4px 24px 4px 11px;
    min-height: 18px;
    font-size: 11px;
    font-weight: 500;
}}
QComboBox:hover {{
    background-color: {wash_hover};
    border-color: #8B7FB8;
}}
QComboBox:focus {{
    border: 1.5px solid #8B7FB8;
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: none;
    border-top-right-radius: 13px;
    border-bottom-right-radius: 13px;
}}
QComboBox::down-arrow {{
    image: none;
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #8B7FB8;
    margin-right: 7px;
}}
QComboBox::down-arrow:on {{
    border-top: none;
    border-bottom: 5px solid #8B7FB8;
}}
QComboBox QAbstractItemView {{
    font-family: "{fam}";
    background-color: {card_bg};
    border: 1px solid {card_border};
    border-radius: 12px;
    padding: 4px;
    selection-background-color: {wash_bg};
    selection-color: {accent_ink};
    color: {ink};
    font-size: 11px;
    font-weight: 500;
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    padding: 5px 8px;
    border-radius: 8px;
    font-weight: 500;
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: {wash_hover};
    color: {accent_ink};
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: {wash_bg};
    color: {accent_ink};
}}

/* INPUTS */
QLineEdit {{
    font-family: "{fam}";
    background-color: {input_bg};
    border: 1px solid {card_border};
    border-radius: 12px;
    padding: 5px 11px;
    color: {ink};
    font-size: 11px;
    font-weight: 400;
}}
QLineEdit:focus {{
    border: 1.5px solid #8B7FB8;
}}

QTextEdit, QTextBrowser {{
    font-family: "{fam}";
    background-color: {input_bg};
    border: 1px solid {card_border};
    border-radius: 14px;
    padding: 8px 10px;
    color: {ink};
    font-size: 12px;
    font-weight: 400;
}}
QTextEdit:focus, QTextBrowser:focus {{
    border: 1.5px solid #8B7FB8;
}}

/* SEGMENTED PILL TABS */
QTabWidget::pane {{
    border: none;
    background: transparent;
    padding: 0px;
    margin-top: 4px;
}}
QTabWidget::tab-bar {{
    alignment: center;
}}
QTabBar {{
    background-color: {tab_bar_bg};
    border: 1px solid {wash_border};
    border-radius: 16px;
    padding: 2px;
}}
QTabBar::tab {{
    font-family: "{fam}";
    font-size: 11px;
    font-weight: 500;
    color: {soft};
    background-color: transparent;
    padding: 5px 13px;
    border-radius: 13px;
    margin: 2px;
    border: 1px solid transparent;
}}
QTabBar::tab:hover {{
    color: {accent_ink};
    background-color: {wash_hover};
}}
QTabBar::tab:selected {{
    color: {accent_ink};
    background-color: {tab_sel_bg};
    border: 1px solid {wash_border};
    font-weight: 500;
}}

/* GROUP BOX & FORM */
QGroupBox {{
    font-family: "{fam}";
    font-size: 12px;
    font-weight: 500;
    color: {accent_ink};
    border: 1px solid {card_border};
    border-radius: 14px;
    margin-top: 12px;
    padding: 14px 10px 10px 10px;
    background-color: {card_bg};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
    font-weight: 500;
}}

QSpinBox {{
    font-family: "{fam}";
    background-color: {input_bg};
    border: 1px solid {card_border};
    border-radius: 12px;
    padding: 4px 8px;
    color: {ink};
    font-weight: 400;
}}
QSpinBox:focus {{
    border: 1.5px solid #8B7FB8;
}}

/* SCROLLBAR */
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {wash_border};
    min-height: 20px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: #8B7FB8;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""


NOUS_STYLESHEET = get_nous_stylesheet(False)
