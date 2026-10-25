"""
Nous Tree Widget
Provides animated, authentic Nous tree visualization with sky-to-earth gradient,
drifting clouds, glowing sun, real-time sway animation, and growth badges.
Rendered entirely via native Qt QPainter and QSvgRenderer with zero WebEngine overhead.
"""

import math
import os
import subprocess
import time
from typing import Optional

try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
    from PyQt6.QtCore import Qt, QTimer, QRectF
    from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QBrush, QFont, QPainterPath
    from PyQt6.QtSvg import QSvgRenderer
except ImportError:
    try:
        from aqt.qt import (
            QWidget, QVBoxLayout, QLabel, Qt, QTimer, QRectF,
            QPainter, QColor, QLinearGradient, QBrush, QFont, QPainterPath
        )
        from PyQt6.QtSvg import QSvgRenderer
    except ImportError:
        class QWidget:
            def __init__(self, *args, **kwargs): pass
            def update(self): pass
            def setFixedHeight(self, h): pass
            def width(self): return 300
            def height(self): return 190
        class QVBoxLayout:
            def __init__(self, *args, **kwargs): pass
            def setContentsMargins(self, *args): pass
        class QLabel: pass
        class Qt:
            class PenStyle:
                NoPen = None
            class AlignmentFlag:
                AlignCenter = None
        class QTimer:
            def __init__(self, *args): pass
            def start(self, *args): pass
            timeout = None
        class QRectF:
            def __init__(self, *args): pass
        class QPainter:
            class RenderHint:
                Antialiasing = 1
            def __init__(self, *args): pass
            def setRenderHint(self, *args): pass
            def setClipPath(self, *args): pass
            def fillRect(self, *args): pass
            def setPen(self, *args): pass
            def setBrush(self, *args): pass
            def drawEllipse(self, *args): pass
            def drawRoundedRect(self, *args): pass
            def save(self): pass
            def restore(self): pass
            def translate(self, *args): pass
            def rotate(self, *args): pass
            def setFont(self, *args): pass
            def drawText(self, *args): pass
            def end(self): pass
        class QColor:
            def __init__(self, *args): pass
        class QLinearGradient:
            def __init__(self, *args): pass
            def setColorAt(self, *args): pass
        class QBrush:
            def __init__(self, *args): pass
        class QFont:
            class Weight:
                Normal = 400
                Medium = 500
                Bold = 700
            def __init__(self, *args): pass
        class QPainterPath:
            def __init__(self): pass
            def addRoundedRect(self, *args): pass
        QSvgRenderer = None

from .tree_art import render_tree_svg_py


def get_tree_svg(tree_id: str, pct: float, is_growing: bool) -> str:
    """Generates authentic Nous vector tree SVG."""
    # Try Node.js renderer first if available for full JS fidelity
    js_path = os.path.join(os.path.dirname(__file__), "tree_renderer.js")
    if os.path.exists(js_path):
        try:
            code = f'const {{ renderNousTreeSVG }} = require("{js_path}"); console.log(renderNousTreeSVG("{tree_id}", {pct}, {str(is_growing).lower()}));'
            res = subprocess.run(["node", "-e", code], capture_output=True, text=True, timeout=1.5)
            if res.returncode == 0 and res.stdout.strip().startswith("<svg"):
                return res.stdout.strip()
        except Exception:
            pass
    # Pure Python fallback
    return render_tree_svg_py(tree_id, pct, is_growing)


class NousTreeWidget(QWidget):
    """
    Animated Tree Widget matching Nous web experience.
    Shows the natural sky-to-earth gradient, glowing sun, drifting clouds,
    live tree art with organic sway, and growth percentage pill badge.
    Runs 100% natively via QPainter and QSvgRenderer.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tree_id = "oak"
        self.pct = 0.0
        self.is_growing = False
        self.is_night = False
        self.svg_data = ""
        self.svg_renderer = None
        self.cloud_offset = 0.0
        self.anim_time = 0.0

        self.setFixedHeight(190)

        # Initialize default tree SVG
        self.set_tree(self.tree_id, self.pct, self.is_growing)

        # Native animation timer for sway & cloud drifting
        self.timer = QTimer(self)
        try:
            self.timer.timeout.connect(self._on_tick)
            self.timer.start(50)  # 20 FPS organic sway
        except Exception:
            pass

    def set_tree(self, tree_id: str, pct: float, is_growing: bool = True):
        self.tree_id = tree_id or "oak"
        self.pct = max(0.0, min(100.0, pct))
        self.is_growing = is_growing
        self.is_night = self.tree_id in ("starry-night", "crystal", "aurora", "moon-willow", "spirit-sakura", "moon-laurel", "lantern")

        self.svg_data = get_tree_svg(self.tree_id, self.pct, self.is_growing)
        if QSvgRenderer and self.svg_data:
            try:
                self.svg_renderer = QSvgRenderer(self.svg_data.encode("utf-8"))
            except Exception:
                self.svg_renderer = None

        self.update()

    def _on_tick(self):
        self.anim_time += 0.05
        self.cloud_offset += 0.2
        if self.cloud_offset > 360.0:
            self.cloud_offset = -40.0
        self.update()

    def paintEvent(self, event):
        """Native Qt painter rendering sky, sun, clouds, swaying SVG tree, and badges."""
        p = QPainter(self)
        if hasattr(p, "setRenderHint") and hasattr(QPainter, "RenderHint"):
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Rounded Clip Path
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), 16, 16)
        p.setClipPath(path)

        # 2. Sky Gradient
        grad = QLinearGradient(0, 0, 0, h)
        if self.is_night:
            grad.setColorAt(0.0, QColor("#1e1b4b"))
            grad.setColorAt(0.45, QColor("#312e81"))
            grad.setColorAt(0.75, QColor("#1e3a5f"))
            grad.setColorAt(1.0, QColor("#14532d"))
        else:
            grad.setColorAt(0.0, QColor("#e0f2fe"))
            grad.setColorAt(0.40, QColor("#bae6fd"))
            grad.setColorAt(0.70, QColor("#a7f3d0"))
            grad.setColorAt(1.0, QColor("#86efac"))
        p.fillRect(0, 0, w, h, grad)

        # 3. Sun / Moon
        p.setPen(Qt.PenStyle.NoPen)
        if self.is_night:
            p.setBrush(QColor("#FEF3C7"))
            p.drawEllipse(18, 14, 26, 26)
        else:
            sun_grad = QLinearGradient(20, 16, 46, 42)
            sun_grad.setColorAt(0.0, QColor("#FEF9C3"))
            sun_grad.setColorAt(0.6, QColor("#FDE68A"))
            p.setBrush(QBrush(sun_grad))
            p.drawEllipse(18, 14, 32, 32)

        # 4. Drifting Clouds
        if not self.is_night:
            p.setBrush(QColor(255, 255, 255, 210))
            c1_x = int(60 + self.cloud_offset) % (w + 60) - 30
            c2_x = int(180 - self.cloud_offset * 0.7) % (w + 60) - 30
            p.drawRoundedRect(QRectF(c1_x, 20, 48, 14), 7, 7)
            p.drawRoundedRect(QRectF(c2_x, 42, 36, 11), 5, 5)

        # 5. Tree SVG with Organic Sway
        if self.svg_renderer and hasattr(self.svg_renderer, "isValid") and self.svg_renderer.isValid():
            p.save()
            tree_w = min(w - 20, 240)
            tree_h = 175
            tree_x = (w - tree_w) / 2
            tree_y = h - tree_h - 4

            # Sway transform
            sway_angle = 1.3 * math.sin(self.anim_time * 1.1) if self.is_growing else 0.0
            cx = tree_x + tree_w / 2
            cy = tree_y + tree_h * 0.92
            p.translate(cx, cy)
            p.rotate(sway_angle)
            p.translate(-cx, -cy)

            self.svg_renderer.render(p, QRectF(tree_x, tree_y, tree_w, tree_h))
            p.restore()

        # 6. Growth Badge (Top-Right)
        badge_w = 90
        badge_h = 22
        badge_x = w - badge_w - 12
        badge_y = 10
        p.setBrush(QColor(255, 255, 255, 235))
        p.setPen(QColor("#ebe8f3"))
        p.drawRoundedRect(QRectF(badge_x, badge_y, badge_w, badge_h), 11, 11)

        p.setFont(QFont("Satoshi", 9, QFont.Weight.Normal))
        p.setPen(QColor("#363f51"))
        p.drawText(QRectF(badge_x, badge_y, badge_w, badge_h), Qt.AlignmentFlag.AlignCenter, f"{self.pct:.1f}% grown")

        # 7. Growing Badge (Bottom-Left)
        if self.is_growing and self.pct < 100.0:
            grow_w = 78
            grow_h = 20
            grow_x = 12
            grow_y = h - grow_h - 10
            p.setBrush(QColor(255, 255, 255, 235))
            p.setPen(QColor("#ebe8f3"))
            p.drawRoundedRect(QRectF(grow_x, grow_y, grow_w, grow_h), 10, 10)

            p.setFont(QFont("Satoshi", 8, QFont.Weight.Normal))
            p.setPen(QColor("#5FA8A3"))
            p.drawText(QRectF(grow_x, grow_y, grow_w, grow_h), Qt.AlignmentFlag.AlignCenter, "growing… 🌱")

        p.end()
