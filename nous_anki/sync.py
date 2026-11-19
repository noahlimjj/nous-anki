"""
Nous Study Tracking & Sync Service
Tracks review time in Anki and syncs hours immediately to Nous (Firestore REST API).
Supports Firebase Email/Password Auth, Embedded Web/Google Auth token capture,
habit resolution/creation, offline queue, and real-time profile stats sync.
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


def _local_date_str(ts: Optional[float] = None) -> str:
    dt = datetime.fromtimestamp(ts) if ts else datetime.now()
    return dt.strftime("%Y-%m-%d")


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

            bounded_ms = min(int(self.max_card_seconds * 1000), max(100, int(time_taken_ms)))
            self.total_ms += bounded_ms
            self.cards_count += 1

    def drain_session(self, min_ms: int = 10000) -> Optional[Dict[str, Any]]:
        """Drains accumulated study time into a session dict if above min_ms."""
        with self.lock:
            if self.total_ms < min_ms or self.session_start is None:
                return None

            end_ts = self.session_end or time.time()
            session = {
                "startTime": _iso_from_timestamp(self.session_start),
                "endTime": _iso_from_timestamp(end_ts),
                "localDate": _local_date_str(end_ts),
                "durationMs": self.total_ms,
                "cardsCount": self.cards_count,
                "createdAt": _iso_now(),
                "source": "nous-anki-reviews",
            }
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
    """Handles authentication, stats fetching, habit resolution, and session writes to Nous."""

    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.queue_file = os.path.join(storage_dir, "pending_sessions.json")
        self.state_file = os.path.join(storage_dir, "nous_state.json")
        self.lock = threading.Lock()
        self.accumulator = TimeAccumulator()
        self.cached_state: Dict[str, Any] = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        default = {
            "userId": "",
            "email": "",
            "idToken": "",
            "refreshToken": "",
            "tokenExpiry": 0,
            "totalHours": 0.0,
            "bonusGrowthHours": 0.0,
            "tapGrowthHours": 0.0,
            "treeBoxesOpened": 0,
            "treePath": None,
            "habitId": "",
            "lastSyncedAt": "",
        }
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    default.update(loaded)
            except Exception:
                pass
        return default

    def _save_state(self):
        with self.lock:
            try:
                with open(self.state_file, "w", encoding="utf-8") as f:
                    json.dump(self.cached_state, f, indent=2)
            except Exception as e:
                print(f"[NousAnki] Failed to save state: {e}")

    def is_authenticated(self) -> bool:
        """Returns True if a userId and a valid idToken or refreshToken exist."""
        uid = (self.cached_state.get("userId") or "").strip()
        tok = (self.cached_state.get("idToken") or "").strip()
        ref = (self.cached_state.get("refreshToken") or "").strip()
        return bool(uid and (tok or ref))

    def set_web_auth(
        self,
        user_id: str,
        email: str = "",
        id_token: str = "",
        refresh_token: str = "",
        expiry_epoch: float = 0.0
    ):
        """Stores Firebase Auth credentials captured from the embedded Nous WebView (Google/Web login)."""
        if not user_id or not (id_token or refresh_token):
            return
        if expiry_epoch > 1e11:  # convert milliseconds to seconds
            expiry_epoch = expiry_epoch / 1000.0
        if expiry_epoch <= time.time():
            expiry_epoch = time.time() + 3300

        self.cached_state.update({
            "userId": user_id.strip(),
            "email": (email or self.cached_state.get("email") or "").strip(),
            "idToken": id_token.strip(),
            "refreshToken": refresh_token.strip(),
            "tokenExpiry": expiry_epoch,
        })
        self._save_state()

    def sign_out(self):
        """Signs out of the Nous account while preserving offline queued sessions."""
        self.cached_state.update({
            "idToken": "",
            "refreshToken": "",
            "tokenExpiry": 0,
            "email": "",
            "habitId": "",
        })
        self._save_state()

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
                user_email = data.get("email", email.strip())
                id_token = data.get("idToken", "")
                refresh_token = data.get("refreshToken", "")
                expires_in = int(data.get("expiresIn", "3600"))

                self.cached_state.update({
                    "userId": user_id,
                    "email": user_email,
                    "idToken": id_token,
                    "refreshToken": refresh_token,
                    "tokenExpiry": time.time() + expires_in - 60,
                })
                self._save_state()
                return {"success": True, "userId": user_id, "email": user_email}
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
                user_id = data.get("user_id") or self.cached_state.get("userId", "")

                self.cached_state.update({
                    "userId": user_id,
                    "idToken": new_token,
                    "refreshToken": new_refresh,
                    "tokenExpiry": time.time() + expires_in - 60,
                })
                self._save_state()
                return new_token
        except Exception as e:
            print(f"[NousAnki] Token refresh failed: {e}")
            return token or None

    # ---------------- Firestore Helpers ----------------

    @staticmethod
    def _parse_num(field_dict: Optional[Dict[str, Any]], default: float = 0.0) -> float:
        if not field_dict or not isinstance(field_dict, dict):
            return default
        if "doubleValue" in field_dict:
            return float(field_dict["doubleValue"])
        if "integerValue" in field_dict:
            return float(field_dict["integerValue"])
        return default

    @classmethod
    def _parse_tree_path(cls, tp_field: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not tp_field or not isinstance(tp_field, dict):
            return None
        fields = tp_field.get("mapValue", {}).get("fields", {})
        if not fields:
            return None
        v = int(cls._parse_num(fields.get("v"), 1))
        base = float(cls._parse_num(fields.get("base"), 0.0))
        prefix_vals = fields.get("prefix", {}).get("arrayValue", {}).get("values", [])
        prefix = [item.get("stringValue") for item in prefix_vals if isinstance(item, dict) and item.get("stringValue")]
        return {"v": v, "base": base, "prefix": prefix}

    # ---------------- Firestore REST API ----------------

    def fetch_user_stats(self) -> Dict[str, Any]:
        """Fetches latest totalHours, treeBoxesOpened, and treePath from Nous /users/{userId}."""
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

                stats = fields.get("stats", {}).get("mapValue", {}).get("fields", {})
                total_hours = self._parse_num(stats.get("totalHours"), 0.0)
                bonus_hours = self._parse_num(stats.get("bonusGrowthHours"), 0.0)
                tap_hours = self._parse_num(stats.get("tapGrowthHours"), 0.0)
                tree_boxes = int(self._parse_num(fields.get("treeBoxesOpened"), 0.0))
                tree_path = self._parse_tree_path(fields.get("treePath"))

                email_or_name = (
                    fields.get("email", {}).get("stringValue")
                    or fields.get("username", {}).get("stringValue")
                    or fields.get("displayName", {}).get("stringValue")
                    or self.cached_state.get("email", "")
                )

                update_dict: Dict[str, Any] = {
                    "totalHours": total_hours,
                    "bonusGrowthHours": bonus_hours,
                    "tapGrowthHours": tap_hours,
                    "treeBoxesOpened": tree_boxes,
                    "lastSyncedAt": _iso_now(),
                }
                if tree_path is not None:
                    update_dict["treePath"] = tree_path
                if email_or_name:
                    update_dict["email"] = email_or_name

                self.cached_state.update(update_dict)
                self._save_state()
                return {
                    "success": True,
                    "totalHours": total_hours,
                    "treeBoxesOpened": tree_boxes,
                    "treePath": tree_path,
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "totalHours": self.cached_state.get("totalHours", 0.0)
            }

    def resolve_or_create_habit(self, habit_name: str = "Anki") -> str:
        """
        Finds the user's matching habit in /artifacts/study-tracker-app/users/{userId}/habits
        or creates one if none exists, returning its document ID.
        """
        user_id = self.cached_state.get("userId")
        token = self.ensure_valid_token()
        if not user_id or not token:
            return "anki"

        url = f"{FIRESTORE_BASE}/artifacts/{DEFAULT_APP_ID}/users/{user_id}/habits"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        target_lower = (habit_name or "Anki").strip().lower()

        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                docs = data.get("documents", [])
                for doc in docs:
                    doc_name = doc.get("name", "")
                    doc_id = doc_name.rsplit("/", 1)[-1] if "/" in doc_name else "anki"
                    flds = doc.get("fields", {})
                    title = (
                        flds.get("title", {}).get("stringValue")
                        or flds.get("name", {}).get("stringValue")
                        or ""
                    ).strip().lower()
                    if title == target_lower or doc_id.lower() == target_lower:
                        self.cached_state["habitId"] = doc_id
                        self._save_state()
                        return doc_id

                # No matching habit exists yet: create it so it appears on the Nous Habit Dashboard
                new_id = "anki"
                create_url = f"{url}/{new_id}"
                body = {
                    "fields": {
                        "id": {"stringValue": new_id},
                        "title": {"stringValue": (habit_name or "Anki").lower()},
                        "icon": {"stringValue": "reading"},
                        "color": {"stringValue": "#111827"},
                        "tracking_type": {"stringValue": "timed"},
                        "difficulty": {"stringValue": "medium"},
                        "daily_goal_mins": {"integerValue": "30"},
                        "target_duration_sec": {"integerValue": "1500"},
                        "totalHours": {"doubleValue": 0.0},
                        "streak": {"integerValue": "0"},
                        "completionDates": {"arrayValue": {"values": []}},
                    }
                }
                creq = urllib.request.Request(
                    create_url,
                    data=json.dumps(body).encode("utf-8"),
                    method="PATCH",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {token}",
                    }
                )
                with urllib.request.urlopen(creq, timeout=8):
                    self.cached_state["habitId"] = new_id
                    self._save_state()
                    return new_id
        except Exception:
            pass

        return self.cached_state.get("habitId") or "anki"

    def _update_remote_habit_and_user_totals(self, habit_id: str, hours_added: float, local_date: str):
        """Best-effort update of habit doc and /users/{userId}.stats.totalHours after a session sync."""
        user_id = self.cached_state.get("userId")
        token = self.ensure_valid_token()
        if not user_id or not token:
            return

        # 1. Update /users/{userId} stats.totalHours via field mask
        try:
            new_total = float(self.cached_state.get("totalHours", 0.0))
            user_url = (
                f"{FIRESTORE_BASE}/users/{user_id}"
                "?updateMask.fieldPaths=stats.totalHours&updateMask.fieldPaths=stats.lastUpdated"
            )
            user_body = {
                "fields": {
                    "stats": {
                        "mapValue": {
                            "fields": {
                                "totalHours": {"doubleValue": new_total},
                                "lastUpdated": {"timestampValue": _iso_now()},
                            }
                        }
                    }
                }
            }
            ureq = urllib.request.Request(
                user_url,
                data=json.dumps(user_body).encode("utf-8"),
                method="PATCH",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                }
            )
            urllib.request.urlopen(ureq, timeout=8).close()
        except Exception:
            pass

        # 2. Update habit doc lastStudied & completionDates
        try:
            habit_url = f"{FIRESTORE_BASE}/artifacts/{DEFAULT_APP_ID}/users/{user_id}/habits/{habit_id}"
            hreq = urllib.request.Request(habit_url, headers={"Authorization": f"Bearer {token}"})
            with urllib.request.urlopen(hreq, timeout=6) as hresp:
                hdoc = json.loads(hresp.read().decode("utf-8"))
                hflds = hdoc.get("fields", {})
                cur_habit_hours = self._parse_num(hflds.get("totalHours"), 0.0)
                cur_dates_vals = hflds.get("completionDates", {}).get("arrayValue", {}).get("values", [])
                cur_dates = [v.get("stringValue") for v in cur_dates_vals if isinstance(v, dict) and v.get("stringValue")]
                if local_date and local_date not in cur_dates:
                    cur_dates.append(local_date)

                patch_url = (
                    f"{habit_url}?updateMask.fieldPaths=totalHours"
                    "&updateMask.fieldPaths=lastStudied&updateMask.fieldPaths=completionDates"
                )
                patch_body = {
                    "fields": {
                        "totalHours": {"doubleValue": round(cur_habit_hours + hours_added, 4)},
                        "lastStudied": {"timestampValue": _iso_now()},
                        "completionDates": {
                            "arrayValue": {
                                "values": [{"stringValue": d} for d in cur_dates]
                            }
                        }
                    }
                }
                preq = urllib.request.Request(
                    patch_url,
                    data=json.dumps(patch_body).encode("utf-8"),
                    method="PATCH",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {token}",
                    }
                )
                urllib.request.urlopen(preq, timeout=6).close()
        except Exception:
            pass

    def sync_session_to_nous(self, session: Dict[str, Any], habit_name: str = "Anki") -> bool:
        """Sends a single session document to Nous Firestore and updates totals."""
        user_id = self.cached_state.get("userId")
        token = self.ensure_valid_token()

        if not user_id or not token:
            return False

        habit_id = self.cached_state.get("habitId") or "anki"
        url = f"{FIRESTORE_BASE}/artifacts/{DEFAULT_APP_ID}/users/{user_id}/sessions"

        duration_ms = int(session.get("durationMs", 0))
        local_date = session.get("localDate") or _local_date_str()
        body = {
            "fields": {
                "habitId": {"stringValue": habit_id},
                "habitName": {"stringValue": habit_name},
                "startTime": {"timestampValue": session.get("startTime", _iso_now())},
                "endTime": {"timestampValue": session.get("endTime", _iso_now())},
                "duration": {"integerValue": str(duration_ms)},
                "localDate": {"stringValue": local_date},
                "isManual": {"booleanValue": False},
                "createdAt": {"timestampValue": session.get("createdAt", _iso_now())},
                "source": {"stringValue": session.get("source", "nous-anki-addon")},
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
                    hours_added = duration_ms / (1000.0 * 3600.0)
                    self.cached_state["totalHours"] = round(
                        self.cached_state.get("totalHours", 0.0) + hours_added, 3
                    )
                    self.cached_state["lastSyncedAt"] = _iso_now()
                    self._save_state()
                    self._update_remote_habit_and_user_totals(habit_id, hours_added, local_date)
                    return True
        except Exception as e:
            print(f"[NousAnki] Sync error: {e}")
        return False

    def flush_pending(self, habit_name: str = "Anki") -> int:
        """Drains local pending sessions and sends them to Nous."""
        queue = self.get_pending_queue()
        if not queue:
            return 0

        if self.is_authenticated() and not self.cached_state.get("habitId"):
            self.resolve_or_create_habit(habit_name)

        synced_count = 0
        remaining = []

        for session in queue:
            if self.sync_session_to_nous(session, habit_name):
                synced_count += 1
            else:
                remaining.append(session)

        self.save_pending_queue(remaining)
        return synced_count

    def process_and_sync(
        self,
        habit_name: str = "Anki",
        min_ms: int = 10000,
        on_done: Optional[Callable[[bool, int], None]] = None
    ):
        """Flushes accumulator and syncs queue in a background thread."""
        def run():
            session = self.accumulator.drain_session(min_ms=min_ms)
            if session:
                self.enqueue_session(session)

            pending_before = len(self.get_pending_queue())
            flushed = self.flush_pending(habit_name)
            stats_res = self.fetch_user_stats()
            pending_after = len(self.get_pending_queue())

            ok = bool(stats_res.get("success")) or (flushed > 0 and pending_after == 0)
            if pending_before > 0 and flushed == 0 and not self.is_authenticated():
                ok = False

            if on_done:
                on_done(ok, flushed)

        threading.Thread(target=run, daemon=True).start()
