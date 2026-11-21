"""
AI & Web Search Service for Nous Anki
Allows users to provide their own API keys (Gemini, Claude/Anthropic, OpenAI, Perplexity, OpenRouter, Ollama)
to ask questions and explain flashcard concepts in real-time.
Includes smart API key prefix detection, per-provider key storage, fast non-thinking Gemini config,
and automatic fallback from retired Claude 3.5 model slugs to Claude 4.5.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Optional, Tuple
import threading


SYSTEM_STUDY_PROMPT = (
    "You are a helpful, concise medical and academic study assistant embedded inside Anki. "
    "Provide clear, high-yield explanations, key definitions, or useful mnemonics "
    "for the queried concept. Keep replies concise and easy to read during card reviews."
)

POPULAR_MODELS = [
    ("gemini 2.5 flash (free)", "gemini", "gemini-2.5-flash"),
    ("gemini 2.5 pro", "gemini", "gemini-2.5-pro"),
    ("claude 4.5 haiku", "anthropic", "claude-haiku-4-5"),
    ("claude 4.5 sonnet", "anthropic", "claude-sonnet-4-5"),
    ("gpt-4o-mini", "openai", "gpt-4o-mini"),
    ("gpt-4o", "openai", "gpt-4o"),
    ("perplexity sonar", "perplexity", "sonar"),
    ("deepseek chat", "openai", "deepseek-chat"),
    ("local ollama", "openai", "llama3.3"),
    ("custom (any model)", "custom", "")
]

WEB_SEARCH_TEMPLATES = {
    "google": "https://www.google.com/search?q={query}",
    "wikipedia": "https://en.wikipedia.org/wiki/Special:Search?search={query}",
    "pubmed": "https://pubmed.ncbi.nlm.nih.gov/?term={query}",
    "amboss": "https://next.amboss.com/us/search?q={query}",
    "uptodate": "https://www.uptodate.com/contents/search?search={query}",
}


def detect_key_provider(api_key: str) -> Optional[str]:
    """Detects provider from standard API key prefixes."""
    k = (api_key or "").strip()
    if not k:
        return None
    if k.startswith("sk-ant-"):
        return "anthropic"
    if k.startswith("AIza") or k.startswith("AQ."):
        return "gemini"
    if k.startswith("pplx-"):
        return "perplexity"
    if k.startswith("sk-"):
        return "openai"
    return None


def looks_like_model_name(val: str) -> bool:
    """Returns True if val looks like a model name (e.g. 'claude-haiku-5-5') rather than an API key."""
    s = (val or "").strip()
    if not s:
        return False
    if detect_key_provider(s) is not None:
        return False
    low = s.lower()
    model_prefixes = (
        "claude-", "claude_", "claude ",
        "gemini-", "gemini_", "gemini ",
        "gpt-", "gpt4", "gpt3",
        "o1-", "o3-", "o4-",
        "sonar", "deepseek-", "deepseek ",
        "llama-", "llama3", "llama2",
        "mistral-", "mixtral-", "qwen-", "ollama/"
    )
    if low.startswith(model_prefixes):
        return True
    exact_models = {
        "claude", "haiku", "sonnet", "opus",
        "claude haiku", "claude sonnet", "claude opus",
        "gemini", "gemini flash", "gemini pro",
        "gpt-4o", "gpt-4o-mini", "gpt-4", "o1", "o3", "deepseek"
    }
    if low in exact_models:
        return True
    return False


def normalize_model_name(model_name: str, provider: str = "") -> str:
    """Normalizes user-entered or legacy model slugs (e.g. claude-haiku-5-5 -> claude-haiku-4-5)."""
    raw = (model_name or "").strip()
    if not raw:
        return ""
    low = raw.lower()
    prov = (provider or "").lower()

    if "claude" in low or "haiku" in low or "sonnet" in low or "opus" in low or prov in ("anthropic", "claude"):
        if "haiku" in low:
            return "claude-haiku-4-5"
        if "sonnet" in low:
            if any(tag in low for tag in ("5-5", "5.5", "3-5", "3.5", "3-7", "3.7")) or low in ("sonnet", "claude-sonnet", "claude sonnet"):
                return "claude-sonnet-4-5"
            return raw
        if "opus" in low:
            if any(tag in low for tag in ("5-5", "5.5", "3-")) or low in ("opus", "claude-opus", "claude opus"):
                return "claude-opus-4-5"
            return raw
        if low == "claude":
            return "claude-haiku-4-5"

    if low in ("gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash-lite", "gemini", "gemini flash"):
        return "gemini-2.5-flash"

    return raw


def infer_provider_from_model(model_name: str, default_provider: str = "openai") -> str:
    """Infers the API provider from a model name string."""
    m = (model_name or "").strip().lower()
    if "gemini" in m:
        return "gemini"
    if "claude" in m or "haiku" in m or "sonnet" in m or "opus" in m:
        return "anthropic"
    if "sonar" in m or "perplexity" in m:
        return "perplexity"
    if m.startswith("gpt-") or m.startswith("o1") or m.startswith("o3") or "deepseek" in m or "llama" in m:
        return "openai"
    return default_provider


def sanitize_ai_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recovers gracefully if a user typed a model name (like 'claude-haiku-5-5')
    into the API key field or swapped the API Key and Model Name fields.
    """
    cfg = dict(config)
    raw_key = (cfg.get("ai_api_key") or "").strip()
    raw_model = (cfg.get("ai_model") or "").strip()

    # Case 1: User swapped API key and Model Name fields
    if looks_like_model_name(raw_key) and detect_key_provider(raw_model) is not None:
        raw_key, raw_model = raw_model, raw_key
        cfg["ai_api_key"] = raw_key
        cfg["ai_model"] = raw_model

    # Case 2: User typed a model name (e.g. 'claude-haiku-5-5') into the API key field
    if looks_like_model_name(raw_key):
        inferred_prov = infer_provider_from_model(raw_key, cfg.get("ai_provider") or "anthropic")
        cfg["ai_provider"] = inferred_prov
        cfg["ai_model"] = normalize_model_name(raw_key, inferred_prov)
        cfg["_misplaced_model_in_key"] = raw_key
        # Restore any valid saved key for that provider, else clear the bogus key
        saved_prov_key = (cfg.get(f"{inferred_prov}_api_key") or "").strip()
        if saved_prov_key and not looks_like_model_name(saved_prov_key):
            cfg["ai_api_key"] = saved_prov_key
        else:
            cfg["ai_api_key"] = ""

    # Clean per-provider key slots if a model name ever leaked into them
    for field in ("gemini_api_key", "anthropic_api_key", "openai_api_key", "perplexity_api_key"):
        val = (cfg.get(field) or "").strip()
        if looks_like_model_name(val):
            cfg[field] = ""

    # Normalize model name
    prov = (cfg.get("ai_provider") or "gemini").lower()
    if "claude" in prov:
        prov = "anthropic"
        cfg["ai_provider"] = "anthropic"
    if cfg.get("ai_model"):
        cfg["ai_model"] = normalize_model_name(cfg["ai_model"], prov)

    return cfg


class AISearchClient:
    def __init__(
        self,
        provider: str = "openai",
        api_key: str = "",
        model: str = "",
        base_url: str = "",
        api_keys: Optional[Dict[str, str]] = None
    ):
        self.provider = (provider or "openai").lower()
        if "claude" in self.provider:
            self.provider = "anthropic"
        self.api_key = (api_key or "").strip()
        self.model = (model or "").strip()
        self.base_url = (base_url or "").strip()
        self._misplaced_model_in_key: str = ""
        self.api_keys: Dict[str, str] = {}
        if api_keys:
            for k, v in api_keys.items():
                s = str(v).strip() if v else ""
                if s and not looks_like_model_name(s):
                    self.api_keys[k.lower()] = s

    def set_config_keys(self, config: Dict[str, Any]):
        """Updates provider, primary key, and per-provider keys from addon config."""
        clean = sanitize_ai_config(config)
        self._misplaced_model_in_key = clean.get("_misplaced_model_in_key", "")
        self.provider = (clean.get("ai_provider") or self.provider or "gemini").lower()
        if "claude" in self.provider:
            self.provider = "anthropic"
        self.api_key = (clean.get("ai_api_key") or "").strip()
        self.model = (clean.get("ai_model") or "").strip()
        self.base_url = (clean.get("ai_base_url") or "").strip()

        self.api_keys = {}
        for p_name, cfg_field in [
            ("gemini", "gemini_api_key"),
            ("anthropic", "anthropic_api_key"),
            ("openai", "openai_api_key"),
            ("perplexity", "perplexity_api_key"),
        ]:
            val = (clean.get(cfg_field) or "").strip()
            if val and not looks_like_model_name(val):
                self.api_keys[p_name] = val

        # Also classify primary ai_api_key by prefix so switching models never loses it
        detected = detect_key_provider(self.api_key)
        if detected and detected not in self.api_keys:
            self.api_keys[detected] = self.api_key

    def _resolve_execution(
        self,
        override_provider: Optional[str],
        override_model: Optional[str]
    ) -> Tuple[str, str, str, Optional[str]]:
        """
        Resolves (provider, model_name, api_key, error_message).
        Prevents sending a Claude key to Gemini or vice versa, and catches model names
        accidentally typed into the API key field.
        """
        prov = (override_provider or self.provider or "openai").lower()
        if "claude" in prov:
            prov = "anthropic"
        model_name = (override_model or self.model or "").strip()

        # Check if self.api_key and self.model were swapped directly on the client
        primary = (self.api_key or "").strip()
        if looks_like_model_name(primary) and detect_key_provider(model_name) is not None:
            primary, model_name = model_name, primary
            self.api_key = primary
            self.model = model_name

        misplaced_model = self._misplaced_model_in_key
        if looks_like_model_name(primary):
            misplaced_model = primary
            if not model_name or model_name in ("gpt-4o-mini", "gemini-2.5-flash"):
                model_name = primary
            prov = infer_provider_from_model(model_name, prov)
            primary = ""

        if model_name:
            inferred = infer_provider_from_model(model_name, prov)
            if prov == "custom" or inferred in ("anthropic", "gemini", "perplexity"):
                prov = inferred
            model_name = normalize_model_name(model_name, prov)

        # 1. Check if we have a dedicated key for the requested provider
        if prov in self.api_keys and self.api_keys[prov] and not looks_like_model_name(self.api_keys[prov]):
            return prov, model_name, self.api_keys[prov], None

        # 2. Check primary self.api_key
        primary_kind = detect_key_provider(primary)

        if primary:
            # If primary key matches requested provider, or is an unprefixed/custom key
            if primary_kind is None or primary_kind == prov:
                return prov, model_name, primary, None

            # Mismatch between selected dropdown provider and the only configured key!
            # Case A: User only configured a Claude key (sk-ant-...) and dropdown was still on default Gemini
            if primary_kind == "anthropic" and prov == "gemini" and "gemini" not in self.api_keys:
                auto_model = model_name if "claude" in model_name.lower() else "claude-haiku-4-5"
                return "anthropic", normalize_model_name(auto_model, "anthropic"), primary, None

            # Case B: User explicitly selected Claude/OpenAI in dropdown, but only a Gemini key is in config
            p_labels = {
                "anthropic": "Claude (Anthropic, starts with sk-ant-...)",
                "gemini": "Google Gemini (starts with AIza... or AQ....)",
                "openai": "OpenAI (starts with sk-...)",
                "perplexity": "Perplexity (starts with pplx-...)",
            }
            needed_desc = p_labels.get(prov, prov)
            have_desc = p_labels.get(primary_kind, primary_kind)
            return (
                prov,
                model_name,
                "",
                f"You selected a {prov.title()} model ({model_name or prov}), "
                f"but the configured key is for {have_desc}. "
                f"Paste your {needed_desc} key into the 🔑 key box above or in ⚙️ Settings."
            )

        # If a model name (like 'claude-haiku-5-5') was typed into the API key field
        if misplaced_model:
            key_hint = {
                "anthropic": "Claude API key (starts with sk-ant-...)",
                "gemini": "Gemini API key (starts with AIza...)",
                "openai": "OpenAI API key (starts with sk-...)",
                "perplexity": "Perplexity API key (starts with pplx-...)",
            }.get(prov, f"{prov.title()} API key")
            return (
                prov,
                model_name,
                "",
                f"'{misplaced_model}' is a model name, not an API key. "
                f"Paste your {key_hint} in the 🔑 API key box above or in ⚙️ Settings."
            )

        # 3. Check if any key exists in api_keys
        if self.api_keys:
            only_prov, only_key = next(iter(self.api_keys.items()))
            return (
                prov,
                model_name,
                "",
                f"No API key configured for {prov.title()}. "
                f"Paste your {prov.title()} key in the 🔑 box above, or switch the model dropdown to {only_prov.title()}."
            )

        return (
            prov,
            model_name,
            "",
            "No API key configured. Paste your Gemini (AIza...), Claude (sk-ant-...), or OpenAI (sk-...) key in the 🔑 box above or click ⚙️ Settings."
        )

    def search_query(
        self,
        query: str,
        override_model: Optional[str] = None,
        override_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Executes AI search / Q&A query synchronously."""
        prov, model_name, key, err = self._resolve_execution(override_provider, override_model)
        if err:
            return {"success": False, "error": err}

        query = (query or "").strip()
        if not query:
            return {"success": False, "error": "Query cannot be empty."}

        try:
            if "gemini" in prov:
                return self._call_gemini(query, model_name or "gemini-2.5-flash", key)
            elif "perplexity" in prov:
                return self._call_perplexity(query, model_name or "sonar", key)
            elif "anthropic" in prov or "claude" in prov:
                return self._call_anthropic(query, model_name or "claude-haiku-4-5", key)
            else:
                return self._call_openai(query, model_name or "gpt-4o-mini", key)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            try:
                err_data = json.loads(body)
                msg = err_data.get("error", {}).get("message", body)
            except Exception:
                msg = body
            return {"success": False, "error": f"API error ({e.code}): {msg}"}
        except Exception as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}

    def search_query_async(
        self,
        query: str,
        callback: Callable[[Dict[str, Any]], None],
        override_model: Optional[str] = None,
        override_provider: Optional[str] = None
    ):
        """Runs AI search in background thread to never block Anki's main thread."""
        def run():
            result = self.search_query(query, override_model, override_provider)
            callback(result)

        threading.Thread(target=run, daemon=True).start()

    def _call_openai(self, query: str, model_name: str, api_key: str) -> Dict[str, Any]:
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
                "Authorization": f"Bearer {api_key}"
            }
        )

        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            answer = data["choices"][0]["message"]["content"].strip()
            return {"success": True, "answer": answer, "provider": "OpenAI/Compatible", "model": model_name}

    def _call_gemini(self, query: str, model_name: str, api_key: str) -> Dict[str, Any]:
        # Upgrade deprecated gemini-2.0-flash or gemini-1.5-flash to gemini-2.5-flash
        if model_name in ("gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash-lite"):
            model_name = "gemini-2.5-flash"

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        gen_config: Dict[str, Any] = {
            "temperature": 0.4,
            "maxOutputTokens": 900,
        }
        # Disable long internal thinking on gemini-2.5-flash so responses arrive in ~1.5-2s without timing out
        if "2.5-flash" in model_name:
            gen_config["thinkingConfig"] = {"thinkingBudget": 0}

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{SYSTEM_STUDY_PROMPT}\n\nUser Question:\n{query}"}
                    ]
                }
            ],
            "generationConfig": gen_config
        }

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 400 and "thinkingConfig" in gen_config:
                # Fallback without thinkingConfig if model doesn't support it
                del gen_config["thinkingConfig"]
                req2 = urllib.request.Request(
                    endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req2, timeout=25) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            else:
                raise

        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            answer = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
            if not answer:
                answer = "".join(p.get("text", "") for p in parts).strip()
            return {"success": True, "answer": answer, "provider": "Gemini", "model": model_name}
        return {"success": False, "error": "No response candidates returned from Gemini."}

    def _call_anthropic(self, query: str, model_name: str, api_key: str) -> Dict[str, Any]:
        endpoint = "https://api.anthropic.com/v1/messages"
        model_name = normalize_model_name(model_name, "anthropic") or "claude-haiku-4-5"

        def make_req(target_model: str):
            payload = {
                "model": target_model,
                "system": SYSTEM_STUDY_PROMPT,
                "messages": [
                    {"role": "user", "content": query}
                ],
                "max_tokens": 800,
                "temperature": 0.3
            }
            return urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                }
            )

        try:
            with urllib.request.urlopen(make_req(model_name), timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # Automatically upgrade retired or unrecognized Claude model IDs to Claude 4.5 on 404/400
            if e.code in (400, 404) and model_name not in ("claude-haiku-4-5", "claude-sonnet-4-5"):
                fallback_model = "claude-haiku-4-5" if "haiku" in model_name.lower() else "claude-sonnet-4-5"
                model_name = fallback_model
                with urllib.request.urlopen(make_req(fallback_model), timeout=25) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            else:
                raise

        blocks = data.get("content", [])
        answer = "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
        return {"success": True, "answer": answer, "provider": "Anthropic", "model": model_name}

    def _call_perplexity(self, query: str, model_name: str, api_key: str) -> Dict[str, Any]:
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
                "Authorization": f"Bearer {api_key}"
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
