"""
Nous Timer Widget for Anki
Implements the Nous focus timer with authentic sound effects (Web Audio port),
Pomodoro/Stopwatch modes, and auto-syncing to the Nous habit dashboard when stopped.
"""

import time
from typing import Any, Callable, Dict, Optional

try:
    from aqt.qt import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QComboBox, QFrame, QTimer, Qt, QCursor
    )
except ImportError:
    try:
        from PyQt6.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
            QComboBox, QFrame
        )
        from PyQt6.QtCore import QTimer, Qt
        from PyQt6.QtGui import QCursor
    except ImportError:
        class QWidget:
            def __init__(self, *args, **kwargs): pass
        class QVBoxLayout:
            def __init__(self, *args, **kwargs): pass
            def addWidget(self, *args): pass
            def addLayout(self, *args): pass
            def setContentsMargins(self, *args): pass
            def setSpacing(self, *args): pass
        class QHBoxLayout:
            def __init__(self, *args, **kwargs): pass
            def addWidget(self, *args): pass
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
        class QPushButton:
            def __init__(self, *args, **kwargs): pass
            def setText(self, t): pass
            def text(self): return ""
            def setFixedWidth(self, w): pass
            def setToolTip(self, t): pass
            def setStyleSheet(self, *args): pass
            clicked = None
        class QComboBox:
            def __init__(self, *args, **kwargs): pass
            def addItems(self, *args): pass
            def currentIndex(self): return 0
            def setCurrentIndex(self, i): pass
            currentIndexChanged = None
        class QFrame:
            def __init__(self, *args, **kwargs): pass
            def setStyleSheet(self, *args): pass
        class QTimer:
            def __init__(self, *args): pass
            def start(self, ms): pass
            def stop(self): pass
            timeout = None
        class Qt:
            class AlignmentFlag:
                AlignCenter = None

from .sound import NousSoundPlayer
from .sync import NousSyncService, _iso_from_timestamp, _iso_now


class NousTimerWidget(QFrame):
    def __init__(self, parent, sync_service: NousSyncService, sound_player: NousSoundPlayer, on_synced: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self.sync_service = sync_service
        self.sound = sound_player
        self.on_synced = on_synced

        self.running = False
        self.mode = "stopwatch"  # "stopwatch" or "countdown"
        self.target_seconds = 0
        self.elapsed_seconds = 0
        self.start_timestamp: Optional[float] = None

        self.setup_ui()

        self.qtimer = QTimer(self)
        self.qtimer.timeout.connect(self._on_tick)

    def setup_ui(self):
        self.setStyleSheet("""
        QFrame {
            background-color: #ffffff;
            border: 1px solid #ebe8f3;
            border-radius: 14px;
            padding: 10px;
        }
        QLabel.timeDisplay {
            font-size: 32px;
            font-weight: 300;
            font-family: "Satoshi", sans-serif;
            color: #363f51;
            letter-spacing: 0.04em;
        }
        QComboBox {
            font-family: "Satoshi", sans-serif;
            border: 1px solid #ebe8f3;
            border-radius: 12px;
            padding: 3px 8px;
            font-size: 11px;
            color: #5f5390;
            background-color: #f1eef8;
        }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Header: Mode selector + Mute toggle
        top_row = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Stopwatch", "25m Focus", "45m Focus", "60m Focus"])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)

        self.sound_btn = QPushButton("🔊")
        self.sound_btn.setFixedWidth(32)
        self.sound_btn.setStyleSheet("border: 1px solid #ebe8f3; border-radius: 12px; background: #ffffff;")
        self.sound_btn.setToolTip("Toggle sound effects")
        self.sound_btn.clicked.connect(self._toggle_sound)

        top_row.addWidget(self.mode_combo)
        top_row.addStretch()
        top_row.addWidget(self.sound_btn)
        layout.addLayout(top_row)

        # Big Timer Display
        self.time_label = QLabel("00:00")
        self.time_label.setProperty("class", "timeDisplay")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter if hasattr(Qt, "AlignmentFlag") else Qt.AlignCenter)
        layout.addWidget(self.time_label)

        # Controls row
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(6)

        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setStyleSheet("background-color: #5FA8A3; color: white; font-family: 'Satoshi', sans-serif; font-weight: 500; border-radius: 16px; padding: 5px 14px; border: none;")
        self.start_btn.clicked.connect(self.toggle_start_pause)

        self.stop_btn = QPushButton("⏹ Stop & Sync")
        self.stop_btn.setStyleSheet("background-color: #f1eef8; color: #5f5390; font-family: 'Satoshi', sans-serif; font-weight: 500; border: 1px solid #e2ddf0; border-radius: 16px; padding: 5px 12px;")
        self.stop_btn.clicked.connect(self.stop_and_sync)

        ctrl_row.addWidget(self.start_btn)
        ctrl_row.addWidget(self.stop_btn)
        layout.addLayout(ctrl_row)

        # Status text
        self.timer_status = QLabel("Ready to focus")
        self.timer_status.setAlignment(Qt.AlignmentFlag.AlignCenter if hasattr(Qt, "AlignmentFlag") else Qt.AlignCenter)
        self.timer_status.setStyleSheet("font-size: 11px; color: #6b7280;")
        layout.addWidget(self.timer_status)

    def _on_mode_changed(self, idx: int):
        if self.running:
            return
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
        mins = total_seconds // 60
        secs = total_seconds % 60
        if mins >= 60:
            hrs = mins // 60
            mins = mins % 60
            return f"{hrs:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def _update_display(self):
        self.time_label.setText(self._format_time(self.elapsed_seconds))

    def _toggle_sound(self):
        self.sound.muted = not self.sound.muted
        self.sound_btn.setText("🔇" if self.sound.muted else "🔊")

    def toggle_start_pause(self):
        if not self.running:
            # START
            self.running = True
            if self.start_timestamp is None:
                self.start_timestamp = time.time()
            self.start_btn.setText("⏸ Pause")
            self.start_btn.setStyleSheet("background-color: #f59e0b; color: white; font-weight: bold; border-radius: 6px; padding: 5px 12px;")
            self.timer_status.setText("Focusing...")
            self.timer_status.setStyleSheet("font-size: 11px; color: #10b981; font-weight: 600;")
            self.sound.play_start()
            self.qtimer.start(1000)
        else:
            # PAUSE
            self.running = False
            self.start_btn.setText("▶ Resume")
            self.start_btn.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; border-radius: 6px; padding: 5px 12px;")
            self.timer_status.setText("Paused")
            self.timer_status.setStyleSheet("font-size: 11px; color: #f59e0b;")
            self.qtimer.stop()

    def _on_tick(self):
        if not self.running:
            return

        if self.mode == "stopwatch":
            self.elapsed_seconds += 1
            self._update_display()
        else:  # countdown
            self.elapsed_seconds -= 1
            self._update_display()
            if self.elapsed_seconds <= 0:
                self.qtimer.stop()
                self.running = False
                self.sound.play_chime(repeat=3)
                self.stop_and_sync()

    def stop_and_sync(self):
        self.qtimer.stop()
        was_running = self.running or (self.start_timestamp is not None)
        self.running = False

        duration_sec = 0
        now = time.time()
        if self.start_timestamp:
            duration_sec = int(now - self.start_timestamp)

        # Reset button states
        self.start_btn.setText("▶ Start")
        self.start_btn.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; border-radius: 6px; padding: 5px 12px;")

        if duration_sec < 5:
            self.timer_status.setText("Session too short to sync (<5s)")
            self.timer_status.setStyleSheet("font-size: 11px; color: #9ca3af;")
            self._on_mode_changed(self.mode_combo.currentIndex())
            self.start_timestamp = None
            return

        # Play chime
        self.sound.play_chime(repeat=3)

        duration_ms = duration_sec * 1000
        start_iso = _iso_from_timestamp(self.start_timestamp)
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

        self.timer_status.setText(f"⏳ Syncing {self._format_time(duration_sec)} to Nous...")
        self.timer_status.setStyleSheet("font-size: 11px; color: #3b82f6; font-weight: 600;")

        # Submit session
        self.sync_service.enqueue_session(session)

        def on_done(ok: bool, count: int):
            self.timer_status.setText(f"🎉 Synced {self._format_time(duration_sec)} to Habit Dashboard!")
            self.timer_status.setStyleSheet("font-size: 11px; color: #10b981; font-weight: 700;")
            if self.on_synced:
                self.on_synced()

        self.sync_service.process_and_sync(habit_name="Anki", min_ms=1000, on_done=on_done)

        # Reset timer
        self.start_timestamp = None
        self._on_mode_changed(self.mode_combo.currentIndex())
