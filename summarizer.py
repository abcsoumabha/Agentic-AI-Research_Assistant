"""
summarizer.py
=============
Source Summarizer  –  condenses raw webpage text into concise summaries.

Given a research question and the raw text of a single page, this module
asks the LLM to produce a focused, bullet-point summary that is relevant
to the question.

Why summarize per-source?
  - Keeps LLM context windows manageable.
  - Filters out irrelevant filler content early.
  - Makes the final report generation step easier.

Events emitted:
  {"type": "summarize_source", "i": N, "total": N, "title": "..."}
"""

from llm_client import ask_llm


def summarize_source(question: str, url: str, raw_text: str) -> str:
    """
    Summarise the content of a single webpage relative to the research question.

    Args:
        question: The original research question.
        url:      The source URL (used for attribution in the prompt).
        raw_text: Plain-text content extracted from the page.

    Returns:
        A concise bullet-point summary string, or a note that the page
        was not useful.
    """
    if not raw_text.strip() or raw_text.startswith("[Could not fetch"):
        return f"*Could not extract useful content from {url}*"

    prompt = f"""You are a research assistant. Your job is to read the following
webpage content and extract ONLY the information relevant to the research question.

RESEARCH QUESTION: {question}

SOURCE URL: {url}

WEBPAGE CONTENT:
{raw_text}

Write a concise summary (5-8 bullet points maximum) of the key facts from this
page that are relevant to the research question. Use simple, clear language.
Start each bullet with "- ".

If the page contains no relevant information, respond with exactly:
NO_RELEVANT_CONTENT
"""
    summary = ask_llm(prompt).strip()

    if summary == "NO_RELEVANT_CONTENT":
        return f"*No relevant content found at {url}*"

    return summary


def summarize_all_sources(
    question: str,
    sources: list[dict],
    on_event=None,
) -> list[dict]:
    """
    Summarise a list of fetched sources.

    Args:
        question: The original research question.
        sources:  List of dicts, each with keys:
                    - url     (str)
                    - title   (str)
                    - snippet (str)  ← DuckDuckGo snippet
                    - text    (str)  ← raw fetched content
        on_event: Optional event callback.

    Returns:
        List of dicts, each with:
            - url     (str)
            - title   (str)
            - snippet (str)
            - summary (str)  ← LLM-generated summary
    """
    results = []
    total   = len(sources)

    for i, source in enumerate(sources, 1):
        url     = source.get("url", "unknown")
        title   = source.get("title", "Untitled")
        snippet = source.get("snippet", "")
        text    = source.get("text", "")

        _emit(on_event, {
            "type":  "summarize_source",
            "i":     i,
            "total": total,
            "title": title,
            "url":   url,
        })

        summary = summarize_source(question, url, text)

        results.append({
            "url":     url,
            "title":   title,
            "snippet": snippet,
            "summary": summary,
        })

    return results


# ── Private helpers ───────────────────────────────────────────────────────────

def _emit(on_event, event: dict) -> None:
    if on_event is not None:
        try:
            on_event(event)
        except Exception:
            pass
