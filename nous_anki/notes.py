"""
Notes Manager for Nous Anki
Supports session scratchpad and appending notes directly to the active Anki flashcard.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional


class NotesManager:
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.notes_file = os.path.join(storage_dir, "study_notes.json")

    def load_scratchpad(self) -> str:
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("scratchpad", "")
            except Exception:
                pass
        return ""

    def save_scratchpad(self, text: str):
        data = {"scratchpad": text, "updatedAt": time.time()}
        try:
            with open(self.notes_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[NousAnki] Failed to save scratchpad: {e}")

    @staticmethod
    def append_note_to_card(card: Any, note_text: str) -> bool:
        """Appends note text into the current card's Extra or Notes field in Anki."""
        if not card or not note_text.strip():
            return False

        try:
            anki_note = card.note()
            model_fields = [f["name"] for f in anki_note.note_type()["flds"]]

            # Prefer fields named Extra, Notes, Lecture Notes, Comment, or the last field
            preferred = ["Extra", "Notes", "Lecture Notes", "Comments", "Explanation"]
            target_field = None
            for p in preferred:
                for field in model_fields:
                    if p.lower() == field.lower():
                        target_field = field
                        break
                if target_field:
                    break

            if not target_field and model_fields:
                target_field = model_fields[-1]

            if not target_field:
                return False

            existing = anki_note[target_field]
            clean_text = note_text.strip().replace("\n", "<br>")
            timestamp = time.strftime("%b %d, %H:%M")
            formatted_entry = (
                f'<div style="border-left: 3px solid #8b5cf6; padding-left: 8px; margin-top: 8px; '
                f'font-size: 0.9em; color: #4b5563;">'
                f'<span style="font-weight: 600; color: #7c3aed;">[Nous Note • {timestamp}]</span><br>'
                f'{clean_text}</div>'
            )

            if existing.strip():
                anki_note[target_field] = f"{existing}<br>{formatted_entry}"
            else:
                anki_note[target_field] = formatted_entry

            from aqt import mw
            mw.col.update_note(anki_note)
            if hasattr(mw.reviewer, "_redraw_current_card"):
                mw.reviewer._redraw_current_card()
            return True
        except Exception as e:
            print(f"[NousAnki] Error appending note to card: {e}")
            return False
