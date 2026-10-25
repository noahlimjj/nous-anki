"""
Nous Sound Effects System
Procedural sound synthesis matching Nous web audio (Web Audio API port).
Provides two-tone bell on timer start and premium 3-tone harmonic chime on timer stop/complete.
"""

import math
import os
import struct
import subprocess
import threading
import wave
from typing import Optional


class NousSoundPlayer:
    def __init__(self, storage_dir: str):
        self.sound_dir = os.path.join(storage_dir, "sounds")
        os.makedirs(self.sound_dir, exist_ok=True)
        self.bell_path = os.path.join(self.sound_dir, "bell.wav")
        self.chime_path = os.path.join(self.sound_dir, "chime.wav")
        self.muted = False
        self._ensure_sound_files()

    def _ensure_sound_files(self):
        if not os.path.exists(self.bell_path):
            self._generate_bell_wav(self.bell_path)
        if not os.path.exists(self.chime_path):
            self._generate_chime_wav(self.chime_path)

    def _generate_bell_wav(self, path: str):
        """Generates Nous two-tone bell (800 Hz then 600 Hz)."""
        sample_rate = 44100
        duration = 0.8
        num_samples = int(sample_rate * duration)
        with wave.open(path, "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            for i in range(num_samples):
                t = i / sample_rate
                # Note 1: 800 Hz for 0.3s
                # Note 2: 600 Hz starting at 0.15s
                val = 0.0
                if t < 0.35:
                    env1 = math.exp(-7.0 * t)
                    val += math.sin(2 * math.pi * 800 * t) * 0.45 * env1
                if t >= 0.15:
                    t2 = t - 0.15
                    env2 = math.exp(-6.0 * t2)
                    val += math.sin(2 * math.pi * 600 * t2) * 0.45 * env2

                sample = int(val * 32767)
                sample = max(-32768, min(32767, sample))
                wav_file.writeframes(struct.pack("<h", sample))

    def _generate_chime_wav(self, path: str):
        """Generates Nous 3-tone harmonic chime (C6 1047 Hz, E6 1319 Hz, G6 1568 Hz)."""
        sample_rate = 44100
        duration = 1.0
        num_samples = int(sample_rate * duration)
        with wave.open(path, "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            for i in range(num_samples):
                t = i / sample_rate
                env = math.exp(-3.5 * t)
                val = (
                    math.sin(2 * math.pi * 1047 * t) * 0.40 +
                    math.sin(2 * math.pi * 1319 * t) * 0.35 +
                    math.sin(2 * math.pi * 1568 * t) * 0.25
                ) * env

                sample = int(val * 32767 * 0.55)
                sample = max(-32768, min(32767, sample))
                wav_file.writeframes(struct.pack("<h", sample))

    def _play_file(self, path: str):
        if self.muted:
            return
        def run():
            try:
                # Use macOS afplay command (native, low-latency, zero dependencies)
                subprocess.run(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        threading.Thread(target=run, daemon=True).start()

    def play_start(self):
        """Plays timer start / focus begin bell."""
        self._play_file(self.bell_path)

    def play_chime(self, repeat: int = 3, interval: float = 0.8):
        """Plays 3-tone chime repeated like Nous completion chime."""
        if self.muted:
            return
        def run():
            import time
            for _ in range(repeat):
                if self.muted:
                    break
                try:
                    subprocess.run(["afplay", self.chime_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass
                time.sleep(interval)
        threading.Thread(target=run, daemon=True).start()
