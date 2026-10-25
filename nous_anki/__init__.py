"""
Nous Anki Add-on
Automatically logs Anki study hours to Nous, shows live tree growth,
links to Nous City, provides AI & web search with custom API key, and card notes.
"""

import os
from typing import Any, Dict

try:
    from aqt import gui_hooks, mw
    from aqt.qt import QAction, QKeySequence, Qt
except ImportError:
    gui_hooks = None
    mw = None
    QAction = None
    QKeySequence = None
    class Qt:
        RightDockWidgetArea = None

from .dock_widget import NousDockWidget
from .notes import NotesManager
from .settings_dialog import SettingsDialog
from .sync import NousSyncService

ADDON_NAME = "nous_anki"
dock_widget: Any = None
sync_service: Any = None
notes_mgr: Any = None
addon_config: Dict[str, Any] = {}


def load_configuration() -> Dict[str, Any]:
    global addon_config
    default_config = {
        "nous_email": "",
        "nous_password": "",
        "nous_user_id": "",
        "nous_habit_name": "Anki",
        "nous_city_url": "https://nous.study/city",
        "sync_interval_seconds": 60,
        "ai_provider": "openai",
        "ai_api_key": "",
        "ai_model": "gpt-4o-mini",
        "ai_base_url": "",
        "show_dock_on_startup": True,
    }
    loaded = mw.addonManager.getConfig(__name__) if mw else None
    if loaded:
        default_config.update(loaded)
    addon_config = default_config
    return addon_config


def save_configuration(new_config: Dict[str, Any]):
    global addon_config
    addon_config.update(new_config)
    if mw:
        mw.addonManager.writeConfig(__name__, addon_config)
    if dock_widget:
        dock_widget.config = addon_config
        dock_widget.ai_client.provider = addon_config.get("ai_provider", "openai")
        dock_widget.ai_client.api_key = addon_config.get("ai_api_key", "")
        dock_widget.ai_client.model = addon_config.get("ai_model", "")
        dock_widget.ai_client.base_url = addon_config.get("ai_base_url", "")
        dock_widget.refresh_tree_display()


def get_user_storage_dir() -> str:
    """Returns persistent directory for add-on state and pending sessions."""
    base_dir = mw.pm.addonFolder() if mw and hasattr(mw, "pm") else os.path.dirname(__file__)
    user_dir = os.path.join(base_dir, ADDON_NAME, "user_files")
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def open_settings_dialog():
    if not mw:
        return
    dialog = SettingsDialog(mw, addon_config, sync_service, on_saved=save_configuration)
    dialog.exec()


def toggle_dock():
    if dock_widget:
        if dock_widget.isVisible():
            dock_widget.hide()
        else:
            dock_widget.show()
            dock_widget.raise_()


def trigger_sync():
    if dock_widget:
        dock_widget.trigger_manual_sync()


def on_card_answered(reviewer: Any, card: Any, ease: int):
    """Fires every time a card is answered during review."""
    global sync_service, dock_widget
    if not sync_service:
        return

    # card.time_taken() gives millisecond duration spent on card
    duration_ms = getattr(card, "time_taken", lambda: 5000)()
    sync_service.accumulator.add_card_time(duration_ms)

    if dock_widget:
        # Check if accumulated time exceeds configured sync interval
        interval_ms = int(addon_config.get("sync_interval_seconds", 60)) * 1000
        cur_ms = sync_service.accumulator.current_duration_ms
        cur_cards = sync_service.accumulator.current_cards

        dock_widget.sync_status_label.setText(f"🟢 Active: {cur_ms // 1000}s ({cur_cards} cards)")

        if cur_ms >= interval_ms:
            habit = addon_config.get("nous_habit_name", "Anki")
            sync_service.process_and_sync(
                habit_name=habit,
                min_ms=interval_ms,
                on_done=lambda ok, cnt: dock_widget.refresh_tree_display()
            )


def on_card_will_show(text: str, card: Any, kind: str) -> str:
    """Passes active card reference to dock widget."""
    global dock_widget
    if dock_widget:
        dock_widget.on_card_will_show(card)
    return text


def on_review_finished():
    """Flushes active accumulator and syncs when reviewer ends."""
    global sync_service, dock_widget
    if sync_service:
        habit = addon_config.get("nous_habit_name", "Anki")
        sync_service.process_and_sync(
            habit_name=habit,
            min_ms=5000,
            on_done=lambda ok, cnt: dock_widget.refresh_tree_display() if dock_widget else None
        )


def setup_addon():
    global sync_service, notes_mgr, dock_widget

    load_configuration()
    storage_dir = get_user_storage_dir()
    sync_service = NousSyncService(storage_dir)
    notes_mgr = NotesManager(storage_dir)

    # Initial stats fetch in background
    sync_service.fetch_user_stats()

    # Create dock widget
    if mw:
        dock_widget = NousDockWidget(mw, sync_service, notes_mgr, addon_config)
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_widget)

        if not addon_config.get("show_dock_on_startup", True):
            dock_widget.hide()

        # Menu items under Tools
        tools_menu = mw.form.menuTools

        # Settings action
        settings_action = QAction("Nous Anki Settings...", mw)
        settings_action.triggered.connect(open_settings_dialog)
        tools_menu.addAction(settings_action)

        # Toggle dock action
        toggle_action = QAction("Toggle Nous Sidebar", mw)
        toggle_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        toggle_action.triggered.connect(toggle_dock)
        tools_menu.addAction(toggle_action)

        # Sync action
        sync_action = QAction("Sync Hours to Nous", mw)
        sync_action.triggered.connect(trigger_sync)
        tools_menu.addAction(sync_action)

        # City action
        city_action = QAction("Visit Nous City 🏙️", mw)
        city_action.triggered.connect(lambda: dock_widget.open_city_link() if dock_widget else None)
        tools_menu.addAction(city_action)

    # Register Anki hooks
    if gui_hooks:
        gui_hooks.reviewer_did_answer_card.append(on_card_answered)
        gui_hooks.card_will_show.append(on_card_will_show)
        gui_hooks.reviewer_will_end.append(on_review_finished)
        gui_hooks.sync_will_start.append(on_review_finished)


# Initialize when profile is loaded
if mw and gui_hooks:
    gui_hooks.profile_did_open.append(setup_addon)
