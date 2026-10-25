# Nous Anki 🌲🏙️

The official Anki companion add-on for **[Nous](https://nous.study)**. 

Study your flashcards in Anki while growing your trees, tracking hours, exploring your 3D city, taking notes, and querying AI explanations with your own API key.

---

## Features

1. **Automatic Hours Sync to Nous**
   - Every card reviewed in Anki is tracked and batched into study sessions.
   - Automatically writes to your Nous profile via Firestore REST API under your `"Anki"` habit.
   - Built-in **offline queue**: If you study on an airplane or train without internet, sessions are safely stored locally and automatically synced once you reconnect.

2. **Live Tree Growth & Mystery Boxes**
   - Full port of Nous's deterministic tree system (`tree-path.js`).
   - Displays your active tree (e.g. *Oak, Ancient Sakura, Master Bonsai*), rarity tier (*Rare, Super Rare, Epic, Mythic, Legendary*), and real-time growth percentage.
   - Shows hours remaining to unlock and how many trees you have fully grown.

3. **Visit My City (1-Click)**
   - Click the **"🏙️ Visit My City"** button in the sidebar to jump directly into your 3D Nous world (`https://nous.study/city`).

4. **AI & Web Search (Bring Your Own API Key)**
   - Put your own API key for **OpenAI** (`gpt-4o-mini`, `gpt-4o`), **Google Gemini** (`gemini-2.5-flash`), **Perplexity** (`sonar`), or custom OpenAI-compatible endpoints (Ollama, DeepSeek, OpenRouter).
   - Instant clinical/concept explanations and mnemonics without leaving Anki.
   - 1-click web search buttons for Google, PubMed, Amboss, and Wikipedia.

5. **Study Scratchpad & Card Notes**
   - Quick notepad inside Anki that auto-saves your thoughts.
   - **"Append to Current Card"** button: instantly injects notes or AI explanations into the card's `Extra` or `Notes` field with clean styling and timestamps.

---

## Quick Installation

### Option 1: Install Package File (`.ankiaddon`)
1. Download or locate `nous-anki.ankiaddon`.
2. In Anki, go to **Tools** -> **Add-ons** -> **Install from file...**
3. Select `nous-anki.ankiaddon` and restart Anki.

### Option 2: Manual Directory Copy
Copy the `nous_anki` folder into your Anki add-ons directory:
- **macOS**: `~/Library/Application Support/Anki2/addons21/nous_anki`
- **Windows**: `%APPDATA%\Anki2\addons21\nous_anki`
- **Linux**: `~/.local/share/Anki2/addons21/nous_anki`

---

## Configuration

Open Anki and navigate to **Tools** -> **Nous Anki Settings...**:

1. **Nous Account**:
   - Enter your Nous email and password, then click **"Sign In & Test Connection"** (auto-detects your User ID and fetches your current hours).
   - Alternatively, enter your Nous User ID directly.
   - Set your habit name (defaults to `"Anki"`).
2. **AI Search Key**:
   - Choose your provider: **OpenAI**, **Gemini**, or **Perplexity**.
   - Paste your API key.
   - (Optional) Set custom model name or base URL.

---

## Shortcuts

- `Ctrl+Shift+N` (or `Cmd+Shift+N` on Mac): Toggle the Nous sidebar on/off.

---

## Architecture & Tests

```
nous-anki/
├── nous_anki/            # Anki add-on package
│   ├── __init__.py       # Reviewer hooks & Anki entry point
│   ├── dock_widget.py    # Sidebar dock widget (Tree, Search, Notes)
│   ├── tree.py           # Port of Nous tree-path.js & SVG generator
│   ├── sync.py           # Time accumulator, Firebase REST & offline queue
│   ├── ai_search.py      # OpenAI / Gemini / Perplexity search client
│   ├── notes.py          # Scratchpad & card extra field injector
│   ├── settings_dialog.py# Qt configuration dialog
│   ├── config.json       # Default configuration
│   └── manifest.json     # Anki add-on metadata
├── tests/                # Test suite (9/9 unit tests passing)
│   ├── test_tree.py
│   ├── test_sync.py
│   └── test_ai.py
├── build.py              # Packaging script (.ankiaddon generator)
└── README.md
```

Run test suite:
```bash
python3 -m unittest discover tests
```
