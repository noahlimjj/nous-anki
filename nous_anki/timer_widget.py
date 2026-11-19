"""
Nous Timer Widget for Anki
Implements an interactive radial progress ring focus timer with Satoshi typography,
quick duration preset pills, authentic sound effects (Web Audio port),
and instant syncing to the Nous habit dashboard when stopped.
"""

import math
import time
from typing import Any, Callable, Dict, List, Optional

try:
    from aqt.qt import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QComboBox, QFrame, QTimer, Qt, QCursor
    )
    from PyQt6.QtCore import QRectF, QPointF
    from PyQt6.QtGui import QPainter, QColor, QPen, QConicalGradient, QBrush
except ImportError:
    try:
        from PyQt6.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
            QComboBox, QFrame
        )
        from PyQt6.QtCore import QTimer, Qt, QRectF, QPointF
        from PyQt6.QtGui import QCursor, QPainter, QColor, QPen, QConicalGradient, QBrush
    except ImportError:
        class QWidget:
            def __init__(self, *args, **kwargs): pass
            def update(self): pass
            def setFixedSize(self, *args): pass
            def setMinimumHeight(self, *args): pass
            def width(self): return 140
            def height(self): return 140
        class QVBoxLayout:
            def __init__(self, *args, **kwargs): pass
            def addWidget(self, *args, **kwargs): pass
            def addLayout(self, *args): pass
            def addStretch(self, *args): pass
            def setContentsMargins(self, *args): pass
            def setSpacing(self, *args): pass
        class QHBoxLayout:
            def __init__(self, *args, **kwargs): pass
            def addWidget(self, *args, **kwargs): pass
            def addStretch(self, *args): pass
            def addLayout(self, *args): pass
            def setContentsMargins(self, *args): pass
            def setSpacing(self, *args): pass
        class QLabel:
            def __init__(self, *args, **kwargs): pass
            def setText(self, t): pass
            def text(self): return "00:00"
            def setProperty(self, *args): pass
            def setAlignment(self, *args): pass
            def setStyleSheet(self, *args): pass
            def setFont(self, *args): pass
        class QPushButton:
            def __init__(self, *args, **kwargs): pass
            def setText(self, t): pass
            def text(self): return ""
            def setFixedWidth(self, w): pass
            def setFixedSize(self, *args): pass
            def setToolTip(self, t): pass
            def setStyleSheet(self, *args): pass
            def setProperty(self, *args): pass
            def setCursor(self, *args): pass
            def setFont(self, *args): pass
            clicked = None
        class QComboBox:
            def __init__(self, *args, **kwargs): pass
            def addItems(self, *args): pass
            def currentIndex(self): return 0
            def setCurrentIndex(self, i): pass
            def hide(self): pass
            currentIndexChanged = None
        class QFrame:
            def __init__(self, *args, **kwargs): pass
            def setStyleSheet(self, *args): pass
            def setProperty(self, *args): pass
        class QTimer:
            def __init__(self, *args): pass
            def start(self, ms): pass
            def stop(self): pass
            timeout = None
        class Qt:
            class AlignmentFlag:
                AlignCenter = None
            class PenCapStyle:
                RoundCap = None
            class PenStyle:
                NoPen = None
        QRectF = QPointF = QPainter = QColor = QPen = QConicalGradient = QBrush = None

from .sound import NousSoundPlayer
from .sync import NousSyncService, _iso_from_timestamp, _iso_now
from .theme import (
    ensure_fonts_loaded, satoshi_font, apply_satoshi_to_widget_tree, is_night_mode
)


class NousTimerDial(QWidget):
    """
    Custom-painted radial focus ring dial with smooth teal-to-purple arc,
    glowing orbital dot, and breathing aura when actively focusing.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0.0  # 0.0 to 1.0
        self.running = False
        self.paused = False
        self.pulse_phase = 0.0
        self.setMinimumHeight(134)

        self.anim_timer = QTimer(self)
        try:
            self.anim_timer.timeout.connect(self._on_anim)
            self.anim_timer.start(60)
        except Exception:
            pass

    def _on_anim(self):
        if not self.running:
            return
        if hasattr(self, "isVisible") and not self.isVisible():
            return
        self.pulse_phase += 0.12
        self.update()

    def set_state(self, progress: float, running: bool, paused: bool = False):
        self.progress = max(0.0, min(1.0, float(progress)))
        self.running = running
        self.paused = paused
        self.update()

    def paintEvent(self, event):
        if QPainter is None:
            return
        p = QPainter(self)
        if hasattr(p, "setRenderHint") and hasattr(QPainter, "RenderHint"):
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        cx = w / 2.0
        cy = h / 2.0
        radius = min(w, h) / 2.0 - 11.0
        if radius < 20:
            p.end()
            return

        dark = is_night_mode()
        rect = QRectF(cx - radius, cy - radius, radius * 2.0, radius * 2.0)

        # 1. Breathing ambient glow when focusing
        if self.running:
            pulse = 3.0 + 2.2 * math.sin(self.pulse_phase)
            glow_rect = QRectF(
                cx - radius - pulse,
                cy - radius - pulse,
                (radius + pulse) * 2.0,
                (radius + pulse) * 2.0
            )
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(95, 168, 163, 24 if not dark else 34))
            p.drawEllipse(glow_rect)

        # 2. Inner soft circle fill
        p.setPen(Qt.PenStyle.NoPen)
        if dark:
            p.setBrush(QColor("#1a1b23"))
        else:
            p.setBrush(QColor("#fbfafe"))
        p.drawEllipse(QRectF(cx - radius + 4, cy - radius + 4, (radius - 4) * 2, (radius - 4) * 2))

        # 3. Track Ring
        track_pen = QPen(QColor("#2c2a3a" if dark else "#efeaf7"), 6.5)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(track_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(rect)

        # 4. Subtle tick marks at 12, 3, 6, 9 o'clock
        tick_color = QColor("#413b56" if dark else "#dcd5ec")
        p.setPen(QPen(tick_color, 1.5))
        for deg in (0, 90, 180, 270):
            rad = math.radians(deg)
            r_in = radius - 9.0
            r_out = radius - 6.0
            p.drawLine(
                QPointF(cx + r_in * math.cos(rad), cy + r_in * math.sin(rad)),
                QPointF(cx + r_out * math.cos(rad), cy + r_out * math.sin(rad))
            )

        # 5. Active Progress Arc
        arc_frac = self.progress
        if self.running and arc_frac < 0.02:
            arc_frac = 0.02

        if arc_frac > 0.001:
            start_angle = 90 * 16  # 12 o'clock in 1/16th degrees
            span_angle = -int(arc_frac * 360 * 16)

            grad = QConicalGradient(QPointF(cx, cy), 90.0)
            grad.setColorAt(0.0, QColor("#8B7FB8"))
            grad.setColorAt(0.5, QColor("#5FA8A3"))
            grad.setColorAt(1.0, QColor("#5FA8A3"))

            arc_pen = QPen(QBrush(grad), 6.5)
            arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(arc_pen)
            p.drawArc(rect, start_angle, span_angle)

            # 6. Glowing Orbital Tip Dot
            tip_angle_rad = math.radians(90.0 - arc_frac * 360.0)
            tip_x = cx + radius * math.cos(tip_angle_rad)
            tip_y = cy - radius * math.sin(tip_angle_rad)

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(95, 168, 163, 75))
            p.drawEllipse(QPointF(tip_x, tip_y), 6.5, 6.5)
            p.setBrush(QColor("#ffffff"))
            p.setPen(QPen(QColor("#5FA8A3" if self.running else "#8B7FB8"), 2.2))
            p.drawEllipse(QPointF(tip_x, tip_y), 3.8, 3.8)

        p.end()


class NousTimerWidget(QFrame):
    MODE_PRESETS = [
        ("stopwatch", "stopwatch", 0),
        ("25m", "25m focus", 25 * 60),
        ("45m", "45m focus", 45 * 60),
        ("60m", "60m focus", 60 * 60),
    ]

    def __init__(
        self,
        parent,
        sync_service: NousSyncService,
        sound_player: NousSoundPlayer,
        on_synced: Optional[Callable[[], None]] = None,
        on_auth_needed: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.sync_service = sync_service
        self.sound = sound_player
        self.on_synced = on_synced
        self.on_auth_needed = on_auth_needed

        self.running = False
        self.mode = "stopwatch"  # "stopwatch" or "countdown"
        self.target_seconds = 0
        self.elapsed_seconds = 0
        self.start_timestamp: Optional[float] = None
        self.mode_pill_btns: List[QPushButton] = []

        self.setup_ui()

        self.qtimer = QTimer(self)
        try:
            self.qtimer.timeout.connect(self._on_tick)
        except Exception:
            pass

    def setup_ui(self):
        fam = ensure_fonts_loaded()
        self.setProperty("class", "timerCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 11)
        layout.setSpacing(8)

        # 1. Top Row: Segmented Mode Pills + Sound Mute Toggle
        top_row = QHBoxLayout()
        top_row.setSpacing(3)

        pills_frame = QFrame()
        pills_frame.setStyleSheet(
            "QFrame { background-color: #f1eef8; border: 1px solid #e2ddf0; border-radius: 12px; }"
        )
        pills_layout = QHBoxLayout(pills_frame)
        pills_layout.setContentsMargins(2, 2, 2, 2)
        pills_layout.setSpacing(2)

        # Keep QComboBox for backwards compatibility with any test or caller
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([label for _, label, _ in self.MODE_PRESETS])
        try:
            self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
            self.mode_combo.hide()
        except Exception:
            pass

        for idx, (short_label, full_label, _) in enumerate(self.MODE_PRESETS):
            btn = QPushButton(short_label)
            btn.setFont(satoshi_font(10, 500))
            if hasattr(Qt, "CursorShape"):
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
            try:
                btn.clicked.connect(lambda _, i=idx: self.select_mode_index(i))
            except Exception:
                pass
            self.mode_pill_btns.append(btn)
            pills_layout.addWidget(btn)

        self.sound_btn = QPushButton("🔊")
        self.sound_btn.setFixedWidth(30)
        self.sound_btn.setFont(satoshi_font(11, 500))
        self.sound_btn.setStyleSheet(
            "QPushButton { border: 1px solid #e2ddf0; border-radius: 11px; "
            "background-color: #f1eef8; color: #5f5390; padding: 3px 0px; font-size: 11px; }"
            "QPushButton:hover { background-color: #eae5f5; border-color: #8B7FB8; }"
        )
        self.sound_btn.setToolTip("toggle focus sound effects")
        if hasattr(Qt, "CursorShape"):
            self.sound_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        try:
            self.sound_btn.clicked.connect(self._toggle_sound)
        except Exception:
            pass

        top_row.addWidget(pills_frame)
        top_row.addStretch()
        top_row.addWidget(self.sound_btn)
        layout.addLayout(top_row)

        # 2. Center Radial Dial with Embedded Time & Status
        self.dial = NousTimerDial(self)
        dial_layout = QVBoxLayout(self.dial)
        dial_layout.setContentsMargins(0, 18, 0, 18)
        dial_layout.setSpacing(1)
        dial_layout.addStretch()

        self.time_label = QLabel("00:00")
        self.time_label.setProperty("class", "timeDisplay")
        self.time_label.setFont(satoshi_font(27, 300))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter if hasattr(Qt, "AlignmentFlag") else Qt.AlignCenter)
        self.time_label.setStyleSheet(
            f"font-family: '{fam}'; font-size: 27px; font-weight: 300; color: #363f51; background: transparent; border: none;"
        )
        dial_layout.addWidget(self.time_label)

        self.timer_status = QLabel("ready to focus")
        self.timer_status.setFont(satoshi_font(10, 400))
        self.timer_status.setAlignment(Qt.AlignmentFlag.AlignCenter if hasattr(Qt, "AlignmentFlag") else Qt.AlignCenter)
        self.timer_status.setStyleSheet(
            f"font-family: '{fam}'; font-size: 10px; color: #7d8ca8; font-weight: 400; background: transparent; border: none;"
        )
        dial_layout.addWidget(self.timer_status)
        dial_layout.addStretch()

        layout.addWidget(self.dial)

        # 3. Bottom Controls Row
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(6)

        self.start_btn = QPushButton("▶ start")
        self.start_btn.setFont(satoshi_font(11, 500))
        if hasattr(Qt, "CursorShape"):
            self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._style_start_btn("start")
        try:
            self.start_btn.clicked.connect(self.toggle_start_pause)
        except Exception:
            pass

        self.stop_btn = QPushButton("⏹ stop && sync")
        self.stop_btn.setFont(satoshi_font(11, 500))
        if hasattr(Qt, "CursorShape"):
            self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setStyleSheet(
            f"QPushButton {{ background-color: #f1eef8; color: #5f5390; font-family: '{fam}'; "
            "font-weight: 500; font-size: 11px; border: 1px solid #e2ddf0; border-radius: 13px; padding: 6px 12px; }"
            "QPushButton:hover { background-color: #eae5f5; border-color: #8B7FB8; }"
        )
        try:
            self.stop_btn.clicked.connect(self.stop_and_sync)
        except Exception:
            pass

        self.reset_btn = QPushButton("↺")
        self.reset_btn.setFixedWidth(28)
        self.reset_btn.setFont(satoshi_font(12, 500))
        self.reset_btn.setToolTip("reset timer without syncing")
        if hasattr(Qt, "CursorShape"):
            self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: #7d8ca8; font-family: '{fam}'; "
            "font-weight: 500; font-size: 12px; border: 1px solid #ebe8f3; border-radius: 12px; padding: 5px 0px; }"
            "QPushButton:hover { background-color: #f1eef8; color: #5f5390; border-color: #e2ddf0; }"
        )
        try:
            self.reset_btn.clicked.connect(self.reset_timer)
        except Exception:
            pass

        ctrl_row.addWidget(self.start_btn, 3)
        ctrl_row.addWidget(self.stop_btn, 3)
        ctrl_row.addWidget(self.reset_btn, 0)
        layout.addLayout(ctrl_row)

        self._style_mode_pills(0)
        apply_satoshi_to_widget_tree(self)

    def _style_start_btn(self, state: str):
        fam = ensure_fonts_loaded()
        if state == "pause":
            self.start_btn.setStyleSheet(
                f"QPushButton {{ background-color: #8B7FB8; color: #ffffff; font-family: '{fam}'; "
                "font-weight: 500; font-size: 11px; border-radius: 13px; padding: 6px 14px; border: none; }"
                "QPushButton:hover { background-color: #7b6fa6; }"
            )
        else:
            self.start_btn.setStyleSheet(
                f"QPushButton {{ background-color: #5FA8A3; color: #ffffff; font-family: '{fam}'; "
                "font-weight: 500; font-size: 11px; border-radius: 13px; padding: 6px 14px; border: none; }"
                "QPushButton:hover { background-color: #4f9691; }"
            )

    def _style_mode_pills(self, active_idx: int):
        fam = ensure_fonts_loaded()
        for idx, btn in enumerate(self.mode_pill_btns):
            if idx == active_idx:
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: #ffffff; color: #5f5390; font-family: '{fam}'; "
                    "font-size: 10px; font-weight: 500; border: 1px solid #e2ddf0; border-radius: 9px; padding: 3px 8px; }"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: transparent; color: #7d8ca8; font-family: '{fam}'; "
                    "font-size: 10px; font-weight: 500; border: none; border-radius: 9px; padding: 3px 8px; }"
                    "QPushButton:hover { color: #5f5390; background-color: #eae5f5; }"
                )

    def select_mode_index(self, idx: int):
        if self.running:
            return
        self.mode_combo.setCurrentIndex(idx)
        self._on_mode_changed(idx)

    def _on_mode_changed(self, idx: int):
        if self.running:
            return
        self._style_mode_pills(idx)
        if idx == 0:
            self.mode = "stopwatch"
            self.target_seconds = 0
            self.elapsed_seconds = 0
        elif idx == 1:
            self.mode = "countdown"
            self.target_seconds = 25 * 60
            self.elapsed_seconds = self.target_seconds
        elif idx == 2:
            self.mode = "countdown"
            self.target_seconds = 45 * 60
            self.elapsed_seconds = self.target_seconds
        elif idx == 3:
            self.mode = "countdown"
            self.target_seconds = 60 * 60
            self.elapsed_seconds = self.target_seconds

        self._update_display()

    def _format_time(self, total_seconds: int) -> str:
        total_seconds = max(0, int(total_seconds))
        mins = total_seconds // 60
        secs = total_seconds % 60
        if mins >= 60:
            hrs = mins // 60
            mins = mins % 60
            return f"{hrs:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def _compute_progress(self) -> float:
        if self.mode == "stopwatch":
            # Smooth 25-minute cycle around the ring
            cycle = 25 * 60
            return (self.elapsed_seconds % cycle) / float(cycle) if self.elapsed_seconds > 0 else 0.0
        else:
            if self.target_seconds <= 0:
                return 0.0
            done = max(0, self.target_seconds - self.elapsed_seconds)
            return min(1.0, done / float(self.target_seconds))

    def _update_display(self):
        self.time_label.setText(self._format_time(self.elapsed_seconds))
        if hasattr(self, "dial") and self.dial:
            self.dial.set_state(
                self._compute_progress(),
                running=self.running,
                paused=(not self.running and self.start_timestamp is not None)
            )

    def _toggle_sound(self):
        self.sound.muted = not self.sound.muted
        self.sound_btn.setText("🔇" if self.sound.muted else "🔊")

    def reset_timer(self):
        self.qtimer.stop()
        self.running = False
        self.start_timestamp = None
        self.start_btn.setText("▶ start")
        self._style_start_btn("start")
        fam = ensure_fonts_loaded()
        self.timer_status.setText("ready to focus")
        self.timer_status.setStyleSheet(
            f"font-family: '{fam}'; font-size: 10px; color: #7d8ca8; font-weight: 400; background: transparent;"
        )
        self._on_mode_changed(self.mode_combo.currentIndex())

    def toggle_start_pause(self):
        fam = ensure_fonts_loaded()
        if not self.running:
            self.running = True
            if self.start_timestamp is None:
                self.start_timestamp = time.time()
            self.start_btn.setText("⏸ pause")
            self._style_start_btn("pause")
            self.timer_status.setText("focusing…")
            self.timer_status.setStyleSheet(
                f"font-family: '{fam}'; font-size: 10px; color: #5FA8A3; font-weight: 500; background: transparent;"
            )
            self.sound.play_start()
            self.qtimer.start(1000)
            self._update_display()
            if self.on_synced:
                self.on_synced()
        else:
            self.running = False
            self.start_btn.setText("▶ resume")
            self._style_start_btn("start")
            self.timer_status.setText("paused")
            self.timer_status.setStyleSheet(
                f"font-family: '{fam}'; font-size: 10px; color: #8B7FB8; font-weight: 500; background: transparent;"
            )
            self.qtimer.stop()
            self._update_display()

    def _on_tick(self):
        if not self.running:
            return

        if self.mode == "stopwatch":
            self.elapsed_seconds += 1
            self._update_display()
        else:
            self.elapsed_seconds -= 1
            self._update_display()
            if self.elapsed_seconds <= 0:
                self.qtimer.stop()
                self.running = False
                self.sound.play_chime(repeat=3)
                self.stop_and_sync()

    def stop_and_sync(self):
        fam = ensure_fonts_loaded()
        self.qtimer.stop()
        self.running = False

        duration_sec = 0
        now = time.time()
        if self.start_timestamp:
            duration_sec = int(now - self.start_timestamp)
        elif self.mode == "stopwatch" and self.elapsed_seconds > 0:
            duration_sec = int(self.elapsed_seconds)
        elif self.mode == "countdown" and self.target_seconds > self.elapsed_seconds:
            duration_sec = int(self.target_seconds - self.elapsed_seconds)

        self.start_btn.setText("▶ start")
        self._style_start_btn("start")

        if duration_sec < 5:
            self.timer_status.setText("session too short to sync (<5s)")
            self.timer_status.setStyleSheet(
                f"font-family: '{fam}'; font-size: 10px; color: #7d8ca8; font-weight: 400; background: transparent;"
            )
            self.start_timestamp = None
            self._on_mode_changed(self.mode_combo.currentIndex())
            return

        self.sound.play_chime(repeat=3)

        duration_ms = duration_sec * 1000
        start_ts = self.start_timestamp or (now - duration_sec)
        start_iso = _iso_from_timestamp(start_ts)
        end_iso = _iso_from_timestamp(now)

        session = {
            "habitId": "anki",
            "habitName": "Anki",
            "startTime": start_iso,
            "endTime": end_iso,
            "durationMs": duration_ms,
            "createdAt": _iso_now(),
            "source": "nous-anki-timer"
        }

        self.timer_status.setText(f"syncing {self._format_time(duration_sec)} to nous…")
        self.timer_status.setStyleSheet(
            f"font-family: '{fam}'; font-size: 10px; color: #8B7FB8; font-weight: 500; background: transparent;"
        )

        self.sync_service.enqueue_session(session)

        def on_done(ok: bool, count: int):
            if ok:
                self.timer_status.setText(f"synced {self._format_time(duration_sec)} to habit dashboard")
                self.timer_status.setStyleSheet(
                    f"font-family: '{fam}'; font-size: 10px; color: #5FA8A3; font-weight: 500; background: transparent;"
                )
            else:
                self.timer_status.setText(f"queued {self._format_time(duration_sec)} · sign in below to sync")
                self.timer_status.setStyleSheet(
                    f"font-family: '{fam}'; font-size: 10px; color: #d97706; font-weight: 500; background: transparent;"
                )
                if self.on_auth_needed:
                    self.on_auth_needed()
            if self.on_synced:
                self.on_synced()

        self.sync_service.process_and_sync(habit_name="Anki", min_ms=1000, on_done=on_done)

        self.start_timestamp = None
        self._on_mode_changed(self.mode_combo.currentIndex())
