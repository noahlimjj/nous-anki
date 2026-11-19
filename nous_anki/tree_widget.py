"""
Nous Tree Widget
Provides animated, authentic Nous tree visualization with sky-to-earth gradient,
fluffy drifting clouds, glowing sun/moon, rolling meadow ground, real-time sway animation,
and Satoshi growth badges. Rendered natively via Qt QPainter and QSvgRenderer.
"""

import math
import os
import subprocess
from typing import Optional

try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
    from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
    from PyQt6.QtGui import (
        QPainter, QColor, QLinearGradient, QRadialGradient,
        QBrush, QFont, QPainterPath, QPen
    )
    from PyQt6.QtSvg import QSvgRenderer
except ImportError:
    try:
        from aqt.qt import (
            QWidget, QVBoxLayout, QLabel, Qt, QTimer, QRectF, QPointF,
            QPainter, QColor, QLinearGradient, QRadialGradient,
            QBrush, QFont, QPainterPath, QPen
        )
        from PyQt6.QtSvg import QSvgRenderer
    except ImportError:
        class QWidget:
            def __init__(self, *args, **kwargs): pass
            def update(self): pass
            def setFixedHeight(self, h): pass
            def width(self): return 300
            def height(self): return 176
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
        class QPointF:
            def __init__(self, *args): pass
        class QPainter:
            class RenderHint:
                Antialiasing = 1
            def __init__(self, *args): pass
            def setRenderHint(self, *args): pass
            def setClipPath(self, *args): pass
            def fillRect(self, *args): pass
            def drawPath(self, *args): pass
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
        class QRadialGradient:
            def __init__(self, *args): pass
            def setColorAt(self, *args): pass
        class QBrush:
            def __init__(self, *args): pass
        class QPen:
            def __init__(self, *args): pass
        class QFont:
            class Weight:
                Light = 300
                Normal = 400
                Medium = 500
                Bold = 700
            def __init__(self, *args): pass
        class QPainterPath:
            def __init__(self): pass
            def addRoundedRect(self, *args): pass
            def addEllipse(self, *args): pass
            def moveTo(self, *args): pass
            def quadTo(self, *args): pass
            def lineTo(self, *args): pass
            def closeSubpath(self): pass
        QSvgRenderer = None

from .tree_art import render_tree_svg_py
from .theme import satoshi_font


def get_tree_svg(tree_id: str, pct: float, is_growing: bool) -> str:
    """Generates authentic Nous vector tree SVG."""
    js_path = os.path.join(os.path.dirname(__file__), "tree_renderer.js")
    if os.path.exists(js_path):
        try:
            code = f'const {{ renderNousTreeSVG }} = require("{js_path}"); console.log(renderNousTreeSVG("{tree_id}", {pct}, {str(is_growing).lower()}));'
            res = subprocess.run(["node", "-e", code], capture_output=True, text=True, timeout=1.5)
            if res.returncode == 0 and res.stdout.strip().startswith("<svg"):
                return res.stdout.strip()
        except Exception:
            pass
    return render_tree_svg_py(tree_id, pct, is_growing)


class NousTreeWidget(QWidget):
    """
    Animated Tree Widget matching Nous web experience.
    Shows the natural sky-to-earth gradient, glowing sun/moon, fluffy drifting clouds,
    meadow hills, live tree art with organic sway, and Satoshi growth pill badges.
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

        self.setFixedHeight(176)
        self.set_tree(self.tree_id, self.pct, self.is_growing)

        self.timer = QTimer(self)
        try:
            self.timer.timeout.connect(self._on_tick)
            self.timer.start(50)
        except Exception:
            pass

    def set_tree(self, tree_id: str, pct: float, is_growing: bool = True):
        self.tree_id = tree_id or "oak"
        self.pct = max(0.0, min(100.0, pct))
        self.is_growing = is_growing
        self.is_night = self.tree_id in (
            "starry-night", "crystal", "aurora", "moon-willow",
            "spirit-sakura", "moon-laurel", "lantern"
        )

        self.svg_data = get_tree_svg(self.tree_id, self.pct, self.is_growing)
        if QSvgRenderer and self.svg_data:
            try:
                self.svg_renderer = QSvgRenderer(self.svg_data.encode("utf-8"))
            except Exception:
                self.svg_renderer = None

        if hasattr(self, "timer") and hasattr(self.timer, "isActive") and self.timer.isActive():
            try:
                self.timer.setInterval(50 if self.is_growing else 150)
            except Exception:
                pass

        self.update()

    def _on_tick(self):
        if hasattr(self, "isVisible") and not self.isVisible():
            return
        self.anim_time += 0.05
        self.cloud_offset += 0.18
        if self.cloud_offset > 380.0:
            self.cloud_offset = -50.0
        self.update()

    def _draw_fluffy_cloud(self, p: QPainter, x: float, y: float, scale: float, alpha: int = 225):
        """Draws a soft, multi-puff vector cloud."""
        p.save()
        p.translate(x, y)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, alpha))
        p.drawRoundedRect(QRectF(0, 6 * scale, 46 * scale, 12 * scale), 6 * scale, 6 * scale)
        p.drawEllipse(QRectF(7 * scale, 1 * scale, 16 * scale, 15 * scale))
        p.drawEllipse(QRectF(18 * scale, -2 * scale, 18 * scale, 17 * scale))
        p.drawEllipse(QRectF(29 * scale, 3 * scale, 12 * scale, 12 * scale))
        p.restore()

    def paintEvent(self, event):
        """Native Qt painter rendering sky, sun, clouds, meadow, swaying SVG tree, and badges."""
        p = QPainter(self)
        if hasattr(p, "setRenderHint") and hasattr(QPainter, "RenderHint"):
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())

        # 1. Rounded Clip Path
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), 14, 14)
        p.setClipPath(path)

        # 2. Sky Gradient
        grad = QLinearGradient(0, 0, 0, h)
        if self.is_night:
            grad.setColorAt(0.0, QColor("#151338"))
            grad.setColorAt(0.45, QColor("#282566"))
            grad.setColorAt(0.78, QColor("#1b3a5c"))
            grad.setColorAt(1.0, QColor("#134e35"))
        else:
            grad.setColorAt(0.0, QColor("#dff2fe"))
            grad.setColorAt(0.42, QColor("#bae6fd"))
            grad.setColorAt(0.75, QColor("#a7f3d0"))
            grad.setColorAt(1.0, QColor("#6ee7b7"))
        p.fillRect(QRectF(0, 0, w, h), grad)

        # 3. Sun / Moon + Stars
        p.setPen(Qt.PenStyle.NoPen)
        if self.is_night:
            # Twinkling stars
            star_coords = [(58, 22), (112, 16), (175, 28), (235, 19), (86, 44), (210, 48)]
            for idx, (sx, sy) in enumerate(star_coords):
                twinkle = 140 + int(95 * math.sin(self.anim_time * 1.4 + idx))
                p.setBrush(QColor(254, 249, 195, max(50, min(245, twinkle))))
                r = 1.6 if idx % 2 == 0 else 1.2
                p.drawEllipse(QRectF((sx % max(100, int(w - 20))), sy, r * 2, r * 2))
            # Moon halo + crescent
            p.setBrush(QColor(254, 243, 199, 45))
            p.drawEllipse(QRectF(14, 10, 34, 34))
            p.setBrush(QColor("#FEF3C7"))
            p.drawEllipse(QRectF(19, 15, 24, 24))
        else:
            # Soft outer sun glow
            pulse = 1.5 * math.sin(self.anim_time * 0.8)
            p.setBrush(QColor(254, 240, 138, 65))
            p.drawEllipse(QRectF(13 - pulse, 9 - pulse, 38 + pulse * 2, 38 + pulse * 2))
            sun_grad = QLinearGradient(18, 14, 44, 40)
            sun_grad.setColorAt(0.0, QColor("#FEF9C3"))
            sun_grad.setColorAt(0.7, QColor("#FDE047"))
            sun_grad.setColorAt(1.0, QColor("#FACC15"))
            p.setBrush(QBrush(sun_grad))
            p.drawEllipse(QRectF(18, 14, 28, 28))

        # 4. Fluffy Drifting Clouds
        if not self.is_night:
            span = max(200, int(w + 70))
            c1_x = (int(65 + self.cloud_offset) % span) - 45
            c2_x = (int(185 - self.cloud_offset * 0.65) % span) - 45
            self._draw_fluffy_cloud(p, c1_x, 18, 0.95, 225)
            self._draw_fluffy_cloud(p, c2_x, 38, 0.72, 185)

        # 5. Soft Meadow Horizon Curve at Base
        hill = QPainterPath()
        hill.moveTo(0, h)
        hill.lineTo(0, h - 18)
        hill.quadTo(w * 0.5, h - 28, w, h - 16)
        hill.lineTo(w, h)
        hill.closeSubpath()
        if self.is_night:
            p.setBrush(QColor(16, 85, 55, 135))
        else:
            p.setBrush(QColor(110, 231, 183, 145))
        p.drawPath(hill)

        # 6. Tree SVG with Organic Sway
        if self.svg_renderer and hasattr(self.svg_renderer, "isValid") and self.svg_renderer.isValid():
            p.save()
            tree_w = min(w - 20, 220)
            tree_h = 162
            tree_x = (w - tree_w) / 2.0
            tree_y = h - tree_h - 3.0

            sway_angle = 1.3 * math.sin(self.anim_time * 1.1) if self.is_growing else 0.0
            cx = tree_x + tree_w / 2.0
            cy = tree_y + tree_h * 0.92
            p.translate(cx, cy)
            p.rotate(sway_angle)
            p.translate(-cx, -cy)

            self.svg_renderer.render(p, QRectF(tree_x, tree_y, tree_w, tree_h))
            p.restore()

        # 7. Growth Badge (Top-Right)
        badge_w = 96.0
        badge_h = 22.0
        badge_x = w - badge_w - 10.0
        badge_y = 10.0
        p.setBrush(QColor(255, 255, 255, 238))
        p.setPen(QColor("#e2ddf0"))
        p.drawRoundedRect(QRectF(badge_x, badge_y, badge_w, badge_h), 11, 11)

        p.setFont(satoshi_font(10, 500))
        p.setPen(QColor("#2f6f5e" if not self.is_night else "#363f51"))
        p.drawText(
            QRectF(badge_x, badge_y, badge_w, badge_h),
            Qt.AlignmentFlag.AlignCenter,
            f"{self.pct:.1f}% grown"
        )

        # 8. Growing Badge (Bottom-Left)
        if self.is_growing and self.pct < 100.0:
            grow_w = 84.0
            grow_h = 21.0
            grow_x = 10.0
            grow_y = h - grow_h - 9.0
            p.setBrush(QColor(255, 255, 255, 238))
            p.setPen(QColor("#e2ddf0"))
            p.drawRoundedRect(QRectF(grow_x, grow_y, grow_w, grow_h), 10.5, 10.5)

            p.setFont(satoshi_font(9, 500))
            p.setPen(QColor("#4f9691"))
            p.drawText(
                QRectF(grow_x, grow_y, grow_w, grow_h),
                Qt.AlignmentFlag.AlignCenter,
                "growing… 🌱"
            )

        p.end()
