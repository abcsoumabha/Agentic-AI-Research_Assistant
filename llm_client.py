"""
llm_client.py
=============
Thin wrapper around supported LLM backends.

Supports:
  - Google Gemini  (google-generativeai)
  - Ollama         (requests to local server)

Usage:
    from llm_client import ask_llm
    response = ask_llm("Explain gravity in simple terms.")
"""

import requests
import config


def ask_llm(prompt: str) -> str:
    """Send a prompt to the configured LLM and return the text response."""

    if config.LLM_BACKEND == "gemini":
        return _ask_gemini(prompt)
    elif config.LLM_BACKEND == "ollama":
        return _ask_ollama(prompt)
    else:
        raise ValueError(
            f"Unknown LLM_BACKEND '{config.LLM_BACKEND}'. "
            "Choose 'gemini' or 'ollama' in config.py."
        )


# ── Gemini backend ────────────────────────────────────────────────────────────

def _ask_gemini(prompt: str) -> str:
    """Call Google Gemini via the google-generativeai SDK."""
    try:
        import google.generativeai as genai  # type: ignore
    except ImportError:
        raise ImportError(
            "google-generativeai is not installed. "
            "Run: pip install google-generativeai"
        )

    if not config.GEMINI_API_KEY:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set.\n"
            "Get a free key at https://aistudio.google.com/app/apikey "
            "and set it with:\n"
            "  set GEMINI_API_KEY=your_key   (Windows CMD)\n"
            "  $env:GEMINI_API_KEY='your_key' (PowerShell)"
        )

    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(config.GEMINI_MODEL)
    response = model.generate_content(prompt)
    return response.text.strip()


# ── Ollama backend ────────────────────────────────────────────────────────────

def _ask_ollama(prompt: str) -> str:
    """Call a locally running Ollama server."""
    url = f"{config.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except requests.ConnectionError:
        raise ConnectionError(
            f"Cannot connect to Ollama at {config.OLLAMA_BASE_URL}.\n"
            "Make sure Ollama is running: https://ollama.com"
        )
