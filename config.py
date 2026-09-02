"""
config.py
=========
Central configuration for the Research Assistant.

Supports two LLM backends (set LLM_BACKEND below):
  - "gemini"  → Google Gemini API (free tier, requires GEMINI_API_KEY env var)
  - "ollama"  → Local Ollama server (completely free, no internet needed for LLM)

Web search always uses DuckDuckGo, which is free and requires no API key.
"""

import os

# ── LLM backend ──────────────────────────────────────────────────────────────
# Choose "gemini" or "ollama"
LLM_BACKEND = "gemini"

# Gemini settings  (ignored when LLM_BACKEND == "ollama")
#
# Option 1 – paste your key directly here (easiest for local dev):
#   GEMINI_API_KEY = "AIza..."
#
# Option 2 – keep it in an environment variable:
#   PowerShell:  $env:GEMINI_API_KEY = "AIza..."
#   CMD:         set GEMINI_API_KEY=AIza...
#
# Using `or` means an empty env var ("") won't silently override the fallback.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or ""  # set via env var or Streamlit Cloud secrets
GEMINI_MODEL   = "gemini-3.6-flash"                 # current free-tier model

# Ollama settings  (ignored when LLM_BACKEND == "gemini")
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL    = "llama3"                           # any model pulled locally

# ── Search settings ───────────────────────────────────────────────────────────
MAX_SEARCH_RESULTS  = 5    # how many URLs to fetch per search query
MAX_CONTENT_CHARS   = 3000 # max characters extracted from each webpage
MAX_SEARCH_ROUNDS   = 3    # max rounds of additional searching

# ── Report settings ───────────────────────────────────────────────────────────
REPORTS_DIR = "reports"    # folder where Markdown reports are saved

# ── Request headers (polite scraping) ────────────────────────────────────────
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}
HTTP_TIMEOUT = 10   # seconds
