"""
Nous Tree Widget
Provides animated, authentic Nous tree visualization with sky-to-earth gradient,
drifting clouds, glowing sun, real-time sway animation, and growth badges.
"""

import math
import os
import subprocess
import time
from typing import Optional

try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
    from PyQt6.QtCore import Qt, QTimer, QRectF, QUrl
    from PyQt6.QtGui import QPainter, QPixmap, QColor, QLinearGradient, QBrush, QFont, QPainterPath
    from PyQt6.QtSvg import QSvgRenderer
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    try:
        from aqt.qt import (
            QWidget, QVBoxLayout, QLabel, Qt, QTimer, QRectF, QUrl,
            QPainter, QPixmap, QColor, QLinearGradient, QBrush, QFont, QPainterPath
        )
        from PyQt6.QtSvg import QSvgRenderer
        from PyQt6.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        class QWidget:
            def __init__(self, *args, **kwargs): pass
            def update(self): pass
        QWebEngineView = None
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

        # Setup WebEngine view for live animated rendering if available
        self.web_view = None
        self.use_web = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        html_path = os.path.join(os.path.dirname(__file__), "tree_scene.html")
        if QWebEngineView and os.path.exists(html_path) and os.environ.get("QT_QPA_PLATFORM") != "offscreen":
            try:
                self.web_view = QWebEngineView(self)
                self.web_view.page().setBackgroundColor(QColor(0, 0, 0, 0))
                self.web_view.load(QUrl.fromLocalFile(html_path))
                layout.addWidget(self.web_view)
                self.use_web = True
            except Exception:
                self.use_web = False

        # Native animation timer for sway & cloud drifting
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(50)  # 20 FPS organic sway

    def set_tree(self, tree_id: str, pct: float, is_growing: bool = True):
        self.tree_id = tree_id or "oak"
        self.pct = max(0.0, min(100.0, pct))
        self.is_growing = is_growing
        self.is_night = self.tree_id in ("starry-night", "crystal", "aurora", "moon-willow", "spirit-sakura", "moon-laurel", "lantern")

        self.svg_data = get_tree_svg(self.tree_id, self.pct, self.is_growing)
        if QSvgRenderer and self.svg_data:
            self.svg_renderer = QSvgRenderer(self.svg_data.encode("utf-8"))

        if self.use_web and self.web_view:
            try:
                self.web_view.page().runJavaScript(
                    f"if (typeof window.updateTree === 'function') window.updateTree('{self.tree_id}', {self.pct}, {str(self.is_growing).lower()});"
                )
            except Exception:
                pass

        self.update()

    def _on_tick(self):
        self.anim_time += 0.05
        self.cloud_offset += 0.2
        if self.cloud_offset > 360.0:
            self.cloud_offset = -40.0

        if not self.use_web:
            self.update()

    def paintEvent(self, event):
        """Native Qt painter fallback / screenshot renderer."""
        if self.use_web and os.environ.get("QT_QPA_PLATFORM") != "offscreen":
            return super().paintEvent(event)

        p = QPainter(self)
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
        if self.svg_renderer and self.svg_renderer.isValid():
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

        p.setFont(QFont("Satoshi", 9, QFont.Weight.Medium))
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

            p.setFont(QFont("Satoshi", 8, QFont.Weight.Bold))
            p.setPen(QColor("#5FA8A3"))
            p.drawText(QRectF(grow_x, grow_y, grow_w, grow_h), Qt.AlignmentFlag.AlignCenter, "growing… 🌱")

        p.end()
