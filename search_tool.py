"""
tools/search_tool.py
====================
Web Search Tool  –  uses DuckDuckGo (free, no API key needed).

Two-stage process:
  1. search()   → get a list of URLs from DuckDuckGo
  2. fetch_page_text() → download and extract plain text from each URL

The tool is intentionally simple so beginners can understand it easily.
"""

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

import config


# ── Public interface ──────────────────────────────────────────────────────────

def search(query: str, max_results: int | None = None) -> list[dict]:
    """
    Search DuckDuckGo and return a list of result dicts.

    Each dict has:
        - title (str)
        - url   (str)
        - snippet (str)  ← short description from DuckDuckGo

    Args:
        query:       Search string.
        max_results: How many results to return (default from config).

    Returns:
        List of result dicts (may be shorter than max_results if DDG
        returns fewer hits).
    """
    n = max_results or config.MAX_SEARCH_RESULTS
    print(f"  🔎 Searching DuckDuckGo: \"{query}\"")

    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=n):
                results.append({
                    "title":   r.get("title", ""),
                    "url":     r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
    except Exception as e:
        print(f"  ⚠️  DuckDuckGo search failed: {e}")

    print(f"  📄 Found {len(results)} result(s).")
    return results


def fetch_page_text(url: str) -> str:
    """
    Download a webpage and return its main text content.

    Uses BeautifulSoup to strip HTML tags, scripts, and styles.
    Truncates to MAX_CONTENT_CHARS to avoid overloading the LLM.

    Args:
        url: Full URL of the page to fetch.

    Returns:
        Plain-text content of the page (or an error message string).
    """
    try:
        resp = requests.get(
            url,
            headers=config.HTTP_HEADERS,
            timeout=config.HTTP_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        return f"[Could not fetch page: {e}]"

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove non-content tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)

    # Collapse whitespace
    import re
    text = re.sub(r"\s+", " ", text)

    # Truncate to avoid token explosion
    if len(text) > config.MAX_CONTENT_CHARS:
        text = text[: config.MAX_CONTENT_CHARS] + " … [truncated]"

    return text
