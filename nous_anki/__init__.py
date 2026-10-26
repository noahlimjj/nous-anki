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
    from PyQt6.QtGui import QFontDatabase
except ImportError:
    gui_hooks = None
    mw = None
    QAction = None
    QKeySequence = None
    QFontDatabase = None
    class Qt:
        RightDockWidgetArea = None

from .dock_widget import NousDockWidget
from .notes import NotesManager
from .settings_dialog import SettingsDialog
from .sound import NousSoundPlayer
from .sync import NousSyncService
from .theme import ensure_fonts_loaded

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
        "ai_provider": "gemini",
        "ai_api_key": "",
        "ai_model": "gemini-2.5-flash",
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


def open_nous_folder():
    """Opens the Nous Add-on directory in macOS Finder or file manager."""
    try:
        import subprocess
        base_dir = os.path.dirname(os.path.abspath(__file__))
        subprocess.run(["open", base_dir])
    except Exception as e:
        print(f"[Nous Anki] Failed to open folder: {e}")


def toggle_dock():
    global dock_widget
    if not dock_widget:
        setup_addon()
    if dock_widget:
        if dock_widget.isVisible():
            dock_widget.hide()
        else:
            dock_widget.show()
            dock_widget.raise_()
            dock_widget.activateWindow()


def trigger_sync():
    if dock_widget:
        dock_widget.trigger_manual_sync()


def explain_active_card():
    """Immediately opens the AI tab and queries Gemini to explain the current flashcard."""
    global dock_widget
    if not dock_widget:
        setup_addon()
    if dock_widget:
        if not dock_widget.isVisible():
            dock_widget.show()
            dock_widget.raise_()
            dock_widget.activateWindow()
        dock_widget.tabs.setCurrentIndex(0)
        dock_widget.explain_current_card()


def on_profile_will_close():
    """Flushes accumulator and stops & syncs any running focus timer when closing Anki."""
    global sync_service, dock_widget
    if sync_service:
        habit = addon_config.get("nous_habit_name", "Anki")
        sync_service.process_and_sync(habit_name=habit, min_ms=3000)
    if dock_widget and getattr(dock_widget, "timer_widget", None):
        tw = dock_widget.timer_widget
        if getattr(tw, "running", False) or getattr(tw, "start_timestamp", None):
            tw.stop_and_sync()


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

        dock_widget.sync_status_label.setText(f"active: {cur_ms // 1000}s ({cur_cards} cards)")

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


def load_fonts():
    ensure_fonts_loaded()


_addon_initialized = False


def on_top_toolbar_will_set_right_tray_content(content, toolbar):
    """Places the Nous button on the top right tray of Anki toolbar."""
    try:
        toolbar.link_handlers["nous_toggle"] = toggle_dock
        toolbar.link_handlers["nous_folder"] = open_nous_folder
        button_html = (
            '<div style="display:inline-flex;align-items:center;gap:4px;">'
            '<a class="hitem" tabindex="-1" aria-label="nous" '
            'title="nous — toggle sidebar (Ctrl+Shift+N)" '
            'href="#" onclick="return pycmd(\'nous_toggle\')" style="text-decoration:none;">'
            '<span style="display:inline-flex;align-items:center;gap:5px;background:#f1eef8;color:#5f5390;'
            'border:1px solid #e2ddf0;border-radius:14px;padding:3px 10px;font-family:\'Satoshi\',sans-serif;'
            'font-size:11px;font-weight:400;cursor:pointer;">'
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" style="vertical-align:middle;">'
            '<circle cx="12" cy="12" r="9" stroke="#8B7FB8" stroke-width="2" stroke-dasharray="14 6"/>'
            '<text x="12" y="16" text-anchor="middle" font-family="\'Satoshi\',sans-serif" font-size="11" font-weight="bold" fill="#8B7FB8">n</text>'
            '</svg>'
            '<span>nous</span>'
            '</span></a>'
            '<a class="hitem" tabindex="-1" aria-label="nous folder" '
            'title="open nous add-on folder in finder" '
            'href="#" onclick="return pycmd(\'nous_folder\')" style="text-decoration:none;">'
            '<span style="display:inline-flex;align-items:center;padding:3px 7px;background:#ffffff;border:1px solid #e2ddf0;'
            'border-radius:14px;font-size:11px;cursor:pointer;color:#5f5390;" title="open nous folder in finder">📁</span></a>'
            '</div>'
        )
        content.append(button_html)
    except Exception:
        pass


def on_top_toolbar_did_init_links(links, toolbar):
    """Adds a small clean Nous logo & button to the top toolbar."""
    try:
        link = toolbar.create_link(
            "nous_toggle",
            """<span style="display:inline-flex;align-items:center;gap:4px;color:#8B7FB8;font-family:'Satoshi',sans-serif;font-weight:400;font-size:12px;"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" style="vertical-align:middle;margin-right:2px;"><circle cx="12" cy="12" r="9" stroke="#8B7FB8" stroke-width="2" stroke-dasharray="14 6"/><text x="12" y="16" text-anchor="middle" font-family="'Satoshi',sans-serif" font-size="11" font-weight="bold" fill="#8B7FB8">n</text></svg>nous</span>""",
            toggle_dock,
            tip="toggle nous sidebar (Ctrl+Shift+N)",
            id="nous_toolbar_link"
        )
        links.append(link)
    except Exception:
        pass


def on_deck_browser_will_render_content(deck_browser, content):
    """Renders an authentic, minimal Nous badge on Anki's main deck browser page."""
    try:
        hours = 0.0
        cur_tree = "tree"
        if sync_service and sync_service.cached_state:
            hours = float(sync_service.cached_state.get("totalHours", 0.0))
        if dock_widget and hasattr(dock_widget, "tree_name_label"):
            cur_tree = dock_widget.tree_name_label.text()

        badge = f"""
        <div style="margin: 24px auto 12px auto; max-width: 360px; padding: 9px 14px; background: #ffffff; border: 1px solid #ebe8f3; border-radius: 14px; display: flex; align-items: center; justify-content: space-between; font-family: 'Satoshi', -apple-system, sans-serif; font-size: 11px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); cursor: pointer;" onclick="pycmd('nous_toggle');" title="click to toggle nous sidebar">
            <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="9" stroke="#8B7FB8" stroke-width="2" stroke-dasharray="14 6"/>
                    <text x="12" y="16" text-anchor="middle" font-family="'Satoshi',sans-serif" font-size="12" font-weight="bold" fill="#8B7FB8">n</text>
                </svg>
                <span style="font-weight: 400; color: #363f51;">nous anki sync</span>
                <span style="color: #7d8ca8; font-weight: 300;">·</span>
                <span style="color: #5FA8A3; font-weight: 400;">{hours:.1f}h logged</span>
            </div>
            <span style="color: #5f5390; background-color: #f1eef8; border: 1px solid #e2ddf0; border-radius: 999px; padding: 2px 8px; font-size: 10px; font-weight: 400;">open sidebar →</span>
        </div>
        """
        if hasattr(content, "stats"):
            content.stats += badge
    except Exception:
        pass


def on_webview_message(handled: tuple, message: str, context: Any):
    """Handles bridge commands like pycmd('nous_toggle') and pycmd('nous_folder') from Anki webviews."""
    if message == "nous_toggle":
        toggle_dock()
        return (True, None)
    elif message == "nous_folder":
        open_nous_folder()
        return (True, None)
    return handled


def setup_addon():
    global _addon_initialized, sync_service, notes_mgr, dock_widget
    if _addon_initialized:
        return
    _addon_initialized = True

    load_fonts()
    load_configuration()
    storage_dir = get_user_storage_dir()
    sync_service = NousSyncService(storage_dir)
    notes_mgr = NotesManager(storage_dir)
    sound_player = NousSoundPlayer(storage_dir)

    # Initial stats fetch in background
    sync_service.fetch_user_stats()

    # Create dock widget
    if mw:
        dock_widget = NousDockWidget(mw, sync_service, notes_mgr, sound_player, addon_config)
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_widget)

        if not addon_config.get("show_dock_on_startup", True):
            dock_widget.hide()

        # Menu items under Tools
        tools_menu = mw.form.menuTools

        # Settings action
        settings_action = QAction("nous anki settings…", mw)
        settings_action.triggered.connect(open_settings_dialog)
        tools_menu.addAction(settings_action)

        # Toggle dock action
        toggle_action = QAction("toggle nous sidebar", mw)
        toggle_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        toggle_action.triggered.connect(toggle_dock)
        tools_menu.addAction(toggle_action)

        # Explain card action
        explain_action = QAction("explain current card with nous ai", mw)
        explain_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        explain_action.triggered.connect(explain_active_card)
        tools_menu.addAction(explain_action)

        # Sync action
        sync_action = QAction("sync hours to nous", mw)
        sync_action.triggered.connect(trigger_sync)
        tools_menu.addAction(sync_action)

        # City action
        city_action = QAction("visit nous city 🏙️", mw)
        city_action.triggered.connect(lambda: dock_widget.open_city_link() if dock_widget else None)
        tools_menu.addAction(city_action)

        # Open folder action
        folder_action = QAction("open nous folder in finder 📁", mw)
        folder_action.triggered.connect(open_nous_folder)
        tools_menu.addAction(folder_action)

    # Register Anki hooks
    if gui_hooks:
        gui_hooks.reviewer_did_answer_card.append(on_card_answered)
        gui_hooks.card_will_show.append(on_card_will_show)
        gui_hooks.reviewer_will_end.append(on_review_finished)
        gui_hooks.sync_will_start.append(on_review_finished)
        gui_hooks.profile_will_close.append(on_profile_will_close)


# Initialize hooks and startup
if mw and gui_hooks:
    gui_hooks.profile_did_open.append(setup_addon)
    gui_hooks.top_toolbar_will_set_right_tray_content.append(on_top_toolbar_will_set_right_tray_content)
    gui_hooks.top_toolbar_did_init_links.append(on_top_toolbar_did_init_links)
    gui_hooks.deck_browser_will_render_content.append(on_deck_browser_will_render_content)
    gui_hooks.webview_did_receive_js_message.append(on_webview_message)
    # If profile is already opened
    if hasattr(mw, "pm") and mw.pm and getattr(mw.pm, "name", None):
        setup_addon()
