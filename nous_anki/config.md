# Nous Anki Configuration

### Nous Account Settings
- **`nous_email`**: Your registered Nous account email.
- **`nous_password`**: Your Nous account password (used to authenticate and get your auth token).
- **`nous_user_id`**: Your Nous Firebase user ID (auto-filled upon signing in, or can be entered manually).
- **`nous_habit_name`**: The habit title in Nous that Anki study time will log under (default: `"Anki"`).
- **`nous_city_url`**: Direct URL to your 3D Nous City (default: `"https://nous.study/city"`).
- **`sync_interval_seconds`**: How often review sessions auto-sync to Nous during study (default: `60`).

### AI Search (Custom API Key)
- **`ai_provider`**: `"openai"`, `"gemini"`, `"perplexity"`, or `"custom"`.
- **`ai_api_key`**: Your private API key for the chosen AI provider.
- **`ai_model`**: Model name to use (e.g., `gpt-4o-mini`, `gemini-2.5-flash`, `sonar`).
- **`ai_base_url`**: Optional custom base URL for OpenAI-compatible endpoints (e.g., Ollama or OpenRouter).

### UI Settings
- **`show_dock_on_startup`**: Whether to automatically show the Nous sidebar when Anki opens (`true` / `false`).
