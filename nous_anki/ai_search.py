"""
AI & Web Search Service for Nous Anki
Allows users to provide their own API key (OpenAI, Claude, Gemini, Perplexity, OpenRouter, Ollama)
to ask questions and explain flashcard concepts in real-time.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Optional
import threading


SYSTEM_STUDY_PROMPT = (
    "You are a helpful, concise medical and academic study assistant embedded inside Anki. "
    "Provide clear, high-yield explanations, key definitions, or useful mnemonics "
    "for the queried concept. Keep replies concise and easy to read during card reviews."
)

POPULAR_MODELS = [
    ("gemini 2.5 flash (free)", "gemini", "gemini-2.5-flash"),
    ("gemini 2.5 flash-lite", "gemini", "gemini-2.5-flash-lite"),
    ("gemini 2.5 pro", "gemini", "gemini-2.5-pro"),
    ("gpt-4o-mini", "openai", "gpt-4o-mini"),
    ("gpt-4o", "openai", "gpt-4o"),
    ("claude 3.5 haiku", "anthropic", "claude-3-5-haiku-20241022"),
    ("claude 3.5 sonnet", "anthropic", "claude-3-5-sonnet-20241022"),
    ("perplexity sonar", "perplexity", "sonar"),
    ("deepseek chat", "openai", "deepseek-chat"),
    ("local ollama", "openai", "llama3.3"),
    ("custom model…", "custom", "")
]

WEB_SEARCH_TEMPLATES = {
    "google": "https://www.google.com/search?q={query}",
    "wikipedia": "https://en.wikipedia.org/wiki/Special:Search?search={query}",
    "pubmed": "https://pubmed.ncbi.nlm.nih.gov/?term={query}",
    "amboss": "https://next.amboss.com/us/search?q={query}",
    "uptodate": "https://www.uptodate.com/contents/search?search={query}",
}


class AISearchClient:
    def __init__(self, provider: str = "openai", api_key: str = "", model: str = "", base_url: str = ""):
        self.provider = (provider or "openai").lower()
        self.api_key = (api_key or "").strip()
        self.model = (model or "").strip()
        self.base_url = (base_url or "").strip()

    def search_query(self, query: str, override_model: Optional[str] = None, override_provider: Optional[str] = None) -> Dict[str, Any]:
        """Executes AI search / Q&A query synchronously."""
        if not self.api_key:
            return {
                "success": False,
                "error": "No API key configured. Open Tools -> Nous Anki Settings to add your API key."
            }

        query = query.strip()
        if not query:
            return {"success": False, "error": "Query cannot be empty."}

        prov = (override_provider or self.provider).lower()
        model_name = override_model or self.model

        try:
            if "gemini" in prov:
                return self._call_gemini(query, model_name or "gemini-2.5-flash")
            elif "perplexity" in prov:
                return self._call_perplexity(query, model_name or "sonar")
            elif "anthropic" in prov or "claude" in prov:
                return self._call_anthropic(query, model_name or "claude-3-5-sonnet-20241022")
            else:  # default openai / openai-compatible (Ollama, DeepSeek, OpenRouter)
                return self._call_openai(query, model_name or "gpt-4o-mini")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            try:
                err_data = json.loads(body)
                msg = err_data.get("error", {}).get("message", body)
            except Exception:
                msg = body
            return {"success": False, "error": f"API error ({e.code}): {msg}"}
        except Exception as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}

    def search_query_async(self, query: str, callback: Callable[[Dict[str, Any]], None], override_model: Optional[str] = None, override_provider: Optional[str] = None):
        """Runs AI search in background thread to never block Anki's main thread."""
        def run():
            result = self.search_query(query, override_model, override_provider)
            callback(result)

        threading.Thread(target=run, daemon=True).start()

    def _call_openai(self, query: str, model_name: str) -> Dict[str, Any]:
        endpoint = self.base_url or "https://api.openai.com/v1/chat/completions"

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_STUDY_PROMPT},
                {"role": "user", "content": query}
            ],
            "temperature": 0.4,
            "max_tokens": 800
        }

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )

        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            answer = data["choices"][0]["message"]["content"].strip()
            return {"success": True, "answer": answer, "provider": "OpenAI/Compatible", "model": model_name}

    def _call_gemini(self, query: str, model_name: str) -> Dict[str, Any]:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{SYSTEM_STUDY_PROMPT}\n\nUser Question:\n{query}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 800
            }
        }

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                answer = "".join(p.get("text", "") for p in parts).strip()
                return {"success": True, "answer": answer, "provider": "Gemini", "model": model_name}
            return {"success": False, "error": "No response candidates returned from Gemini."}

    def _call_anthropic(self, query: str, model_name: str) -> Dict[str, Any]:
        endpoint = "https://api.anthropic.com/v1/messages"

        payload = {
            "model": model_name,
            "system": SYSTEM_STUDY_PROMPT,
            "messages": [
                {"role": "user", "content": query}
            ],
            "max_tokens": 800,
            "temperature": 0.3
        }

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
        )

        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            blocks = data.get("content", [])
            answer = "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
            return {"success": True, "answer": answer, "provider": "Anthropic", "model": model_name}

    def _call_perplexity(self, query: str, model_name: str) -> Dict[str, Any]:
        endpoint = "https://api.perplexity.ai/chat/completions"

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_STUDY_PROMPT},
                {"role": "user", "content": query}
            ],
            "temperature": 0.2
        }

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )

        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            answer = data["choices"][0]["message"]["content"].strip()
            citations = data.get("citations", [])
            return {
                "success": True,
                "answer": answer,
                "citations": citations,
                "provider": "Perplexity",
                "model": model_name
            }

    @staticmethod
    def get_web_search_url(provider: str, query: str) -> str:
        tmpl = WEB_SEARCH_TEMPLATES.get(provider.lower(), WEB_SEARCH_TEMPLATES["google"])
        return tmpl.format(query=urllib.parse.quote_plus(query))
