"""
Nous Study Tracking & Sync Service
Tracks review time in Anki and syncs hours to Nous (Firestore REST API).
Includes offline queue, session batching, and background threading.
"""

import json
import os
import threading
import time
from datetime import datetime, timezone
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional

FIREBASE_API_KEY = "AIzaSyAk5qHtY3Y_988RBWprbKMiiRc63IECsbg"
FIREBASE_PROJECT_ID = "study-d2678"
DEFAULT_APP_ID = "study-tracker-app"
AUTH_SIGNIN_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
AUTH_REFRESH_URL = f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}"
FIRESTORE_BASE = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso_from_timestamp(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class TimeAccumulator:
    """Accumulates active flashcard study time into batched sessions."""

    def __init__(self, max_card_seconds: float = 60.0):
        self.max_card_seconds = max_card_seconds
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        with self.lock:
            self.session_start: Optional[float] = None
            self.session_end: Optional[float] = None
            self.total_ms: int = 0
            self.cards_count: int = 0

    def add_card_time(self, time_taken_ms: int):
        with self.lock:
            now = time.time()
            if self.session_start is None:
                self.session_start = now - (time_taken_ms / 1000.0)
            self.session_end = now

            # Enforce max duration per card to avoid runaway timers if user leaves card open
            bounded_ms = min(int(self.max_card_seconds * 1000), max(100, int(time_taken_ms)))
            self.total_ms += bounded_ms
            self.cards_count += 1

    def drain_session(self, min_ms: int = 10000) -> Optional[Dict[str, Any]]:
        """Drains accumulated study time into a session dict if above min_ms."""
        with self.lock:
            if self.total_ms < min_ms or self.session_start is None:
                return None

            session = {
                "startTime": _iso_from_timestamp(self.session_start),
                "endTime": _iso_from_timestamp(self.session_end or time.time()),
                "durationMs": self.total_ms,
                "cardsCount": self.cards_count,
                "createdAt": _iso_now(),
            }
            # Reset accumulator for next batch
            self.session_start = None
            self.session_end = None
            self.total_ms = 0
            self.cards_count = 0
            return session

    @property
    def current_duration_ms(self) -> int:
        with self.lock:
            return self.total_ms

    @property
    def current_cards(self) -> int:
        with self.lock:
            return self.cards_count


class NousSyncService:
    """Handles authentication, stats fetching, and session writes to Nous."""

    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.queue_file = os.path.join(storage_dir, "pending_sessions.json")
        self.state_file = os.path.join(storage_dir, "nous_state.json")
        self.lock = threading.Lock()
        self.accumulator = TimeAccumulator()
        self.cached_state: Dict[str, Any] = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "userId": "",
            "idToken": "",
            "refreshToken": "",
            "tokenExpiry": 0,
            "totalHours": 0.0,
            "treeBoxesOpened": 0,
            "treePath": None,
            "lastSyncedAt": "",
        }

    def _save_state(self):
        with self.lock:
            try:
                with open(self.state_file, "w", encoding="utf-8") as f:
                    json.dump(self.cached_state, f, indent=2)
            except Exception as e:
                print(f"[NousAnki] Failed to save state: {e}")

    def get_pending_queue(self) -> List[Dict[str, Any]]:
        with self.lock:
            if os.path.exists(self.queue_file):
                try:
                    with open(self.queue_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
            return []

    def save_pending_queue(self, queue: List[Dict[str, Any]]):
        with self.lock:
            try:
                with open(self.queue_file, "w", encoding="utf-8") as f:
                    json.dump(queue, f, indent=2)
            except Exception as e:
                print(f"[NousAnki] Failed to save queue: {e}")

    def enqueue_session(self, session: Dict[str, Any]):
        queue = self.get_pending_queue()
        queue.append(session)
        self.save_pending_queue(queue)

    # ---------------- Authentication ----------------

    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Signs in via Firebase Auth and caches idToken + refreshToken."""
        payload = json.dumps({
            "email": email.strip(),
            "password": password,
            "returnSecureToken": True
        }).encode("utf-8")

        req = urllib.request.Request(
            AUTH_SIGNIN_URL,
            data=payload,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                user_id = data.get("localId", "")
                id_token = data.get("idToken", "")
                refresh_token = data.get("refreshToken", "")
                expires_in = int(data.get("expiresIn", "3600"))

                self.cached_state.update({
                    "userId": user_id,
                    "idToken": id_token,
                    "refreshToken": refresh_token,
                    "tokenExpiry": time.time() + expires_in - 60,
                })
                self._save_state()
                return {"success": True, "userId": user_id}
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            try:
                err_json = json.loads(err_msg)
                message = err_json.get("error", {}).get("message", str(e))
            except Exception:
                message = str(e)
            return {"success": False, "error": message}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def ensure_valid_token(self) -> Optional[str]:
        """Returns a valid idToken, refreshing if expired."""
        token = self.cached_state.get("idToken")
        expiry = self.cached_state.get("tokenExpiry", 0)
        refresh_token = self.cached_state.get("refreshToken")

        if token and time.time() < expiry:
            return token

        if not refresh_token:
            return token or None

        # Refresh token
        payload = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }).encode("utf-8")

        req = urllib.request.Request(
            AUTH_REFRESH_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                new_token = data.get("id_token")
                new_refresh = data.get("refresh_token")
                expires_in = int(data.get("expires_in", "3600"))

                self.cached_state.update({
                    "idToken": new_token,
                    "refreshToken": new_refresh,
                    "tokenExpiry": time.time() + expires_in - 60,
                })
                self._save_state()
                return new_token
        except Exception as e:
            print(f"[NousAnki] Token refresh failed: {e}")
            return token or None

    # ---------------- Firestore REST API ----------------

    def fetch_user_stats(self) -> Dict[str, Any]:
        """Fetches latest totalHours and treePath from Nous /users/{userId}."""
        user_id = self.cached_state.get("userId")
        if not user_id:
            return {"success": False, "error": "No User ID configured"}

        token = self.ensure_valid_token()
        url = f"{FIRESTORE_BASE}/users/{user_id}"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                doc = json.loads(resp.read().decode("utf-8"))
                fields = doc.get("fields", {})

                # Extract totalHours from stats map
                stats = fields.get("stats", {}).get("mapValue", {}).get("fields", {})
                total_hours = float(
                    stats.get("totalHours", {}).get("doubleValue")
                    or stats.get("totalHours", {}).get("integerValue")
                    or 0.0
                )
                tree_boxes = int(fields.get("treeBoxesOpened", {}).get("integerValue", 0))

                self.cached_state.update({
                    "totalHours": total_hours,
                    "treeBoxesOpened": tree_boxes,
                    "lastSyncedAt": _iso_now(),
                })
                self._save_state()
                return {"success": True, "totalHours": total_hours, "treeBoxesOpened": tree_boxes}
        except Exception as e:
            return {"success": False, "error": str(e), "totalHours": self.cached_state.get("totalHours", 0.0)}

    def sync_session_to_nous(self, session: Dict[str, Any], habit_name: str = "Anki") -> bool:
        """Sends a single session document to Nous Firestore."""
        user_id = self.cached_state.get("userId")
        token = self.ensure_valid_token()

        if not user_id or not token:
            return False

        url = f"{FIRESTORE_BASE}/artifacts/{DEFAULT_APP_ID}/users/{user_id}/sessions"

        duration_ms = session.get("durationMs", 0)
        body = {
            "fields": {
                "habitId": {"stringValue": "anki"},
                "habitName": {"stringValue": habit_name},
                "startTime": {"timestampValue": session.get("startTime", _iso_now())},
                "endTime": {"timestampValue": session.get("endTime", _iso_now())},
                "duration": {"integerValue": str(duration_ms)},
                "createdAt": {"timestampValue": session.get("createdAt", _iso_now())},
                "source": {"stringValue": "nous-anki-addon"},
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 201):
                    # Also credit to local cached total hours immediately
                    hours_added = duration_ms / (1000.0 * 3600.0)
                    self.cached_state["totalHours"] = round(self.cached_state.get("totalHours", 0.0) + hours_added, 3)
                    self.cached_state["lastSyncedAt"] = _iso_now()
                    self._save_state()
                    return True
        except Exception as e:
            print(f"[NousAnki] Sync error: {e}")
        return False

    def flush_pending(self, habit_name: str = "Anki") -> int:
        """Drains local pending sessions and sends them to Nous."""
        queue = self.get_pending_queue()
        if not queue:
            return 0

        synced_count = 0
        remaining = []

        for session in queue:
            if self.sync_session_to_nous(session, habit_name):
                synced_count += 1
            else:
                remaining.append(session)

        self.save_pending_queue(remaining)
        return synced_count

    def process_and_sync(self, habit_name: str = "Anki", min_ms: int = 10000, on_done: Optional[Callable[[bool, int], None]] = None):
        """Flushes accumulator and syncs queue in a background thread."""
        def run():
            # Check accumulator
            session = self.accumulator.drain_session(min_ms=min_ms)
            if session:
                self.enqueue_session(session)

            flushed = self.flush_pending(habit_name)
            # Refresh stats
            self.fetch_user_stats()

            if on_done:
                on_done(True, flushed)

        threading.Thread(target=run, daemon=True).start()
