"""
agent.py
========
The Agentic Loop  –  orchestrates all components into a single pipeline.

Flow:
  User question
      ↓
  [Planner]       creates search queries
      ↓
  [Search Tool]   fetches URLs + page text
      ↓
  [Summarizer]    condenses each page into bullet points
      ↓
  [Planner]       decides if more searching is needed
      ↓  (loop back if yes, up to MAX_SEARCH_ROUNDS)
  [Report Gen]    writes a Markdown report
      ↓
  Save to reports/

Event Callback System
─────────────────────
Every function accepts an optional `on_event` callable.
When provided (e.g. by the Streamlit UI), events are forwarded there.
When None (CLI mode), events are pretty-printed to the console.

Event dict shapes:
  {"type": "plan_created",     "queries": [...]}
  {"type": "round_start",      "round": N}
  {"type": "query_search",     "query": "..."}
  {"type": "fetch_url",        "url": "...", "title": "..."}
  {"type": "summarize_source", "i": N, "total": N, "title": "..."}
  {"type": "check_sufficient", "sufficient": bool, "follow_up": "..."}
  {"type": "report_start"}
  {"type": "report_done",      "report_md": "...", "path": "...", "sources": [...]}
  {"type": "error",            "message": "..."}
  {"type": "log",              "message": "..."}
"""

import config
from planner           import create_research_plan, should_continue_research
from tools.search_tool import search, fetch_page_text
from summarizer        import summarize_all_sources
from report_generator  import generate_report, save_report


def run_research_agent(
    question: str,
    on_event=None,
) -> tuple[str, str]:
    """
    Run the full agentic research pipeline for the given question.

    Args:
        question:  The user's research question.
        on_event:  Optional callback(event_dict) for UI/logging integration.
                   If None, events are printed to the console.

    Returns:
        (report_markdown, report_file_path)
        Both are empty strings if the agent fails to collect any sources.
    """
    _emit(on_event, {"type": "log", "message": f"Starting research: {question}"})

    all_summarized: list[dict] = []   # accumulates summaries across rounds

    # ── Round 0: initial plan ─────────────────────────────────────────────────
    queries = create_research_plan(question, on_event=on_event)
    _emit(on_event, {"type": "plan_created", "queries": queries})

    # ── Search + summarise loop ───────────────────────────────────────────────
    round_num = 0
    while True:
        round_num += 1
        _emit(on_event, {"type": "round_start", "round": round_num})

        # 1. Run each query through the search tool
        raw_sources = _run_queries(queries, on_event=on_event)

        if not raw_sources:
            _emit(on_event, {"type": "log", "message": "No results found in this round."})
        else:
            # 2. Summarise the fetched pages
            summaries = summarize_all_sources(question, raw_sources, on_event=on_event)
            all_summarized.extend(summaries)

        # 3. Ask the planner if we have enough information
        summary_texts = [s["summary"] for s in all_summarized]
        keep_going, follow_up = should_continue_research(
            question, summary_texts, round_num,
            config.MAX_SEARCH_ROUNDS, on_event=on_event,
        )

        if not keep_going:
            break

        # 4. Prepare the next round with the follow-up query
        queries = [follow_up]

    # ── Guard: nothing collected ──────────────────────────────────────────────
    if not all_summarized:
        _emit(on_event, {
            "type": "error",
            "message": "No sources were collected. Cannot generate a report.",
        })
        return "", ""

    # ── Generate & save report ────────────────────────────────────────────────
    _emit(on_event, {"type": "report_start"})
    report_md   = generate_report(question, all_summarized, on_event=on_event)
    report_path = save_report(question, report_md)
    _emit(on_event, {
        "type":      "report_done",
        "report_md": report_md,
        "path":      report_path,
        "sources":   all_summarized,
    })

    return report_md, report_path


# ── Event helpers ─────────────────────────────────────────────────────────────

def _emit(on_event, event: dict) -> None:
    """
    Safely dispatch an event to the callback (if provided) or fall back
    to a console pretty-printer for CLI mode.
    """
    if on_event is not None:
        try:
            on_event(event)
        except Exception:
            pass   # never let UI errors crash the agent
    else:
        _print_event(event)


def _print_event(event: dict) -> None:
    """Pretty-print an event to the console (used when no UI callback given)."""
    etype = event.get("type", "")

    if etype == "log":
        print(f"  {event.get('message', '')}")
    elif etype == "plan_created":
        queries = event.get("queries", [])
        print(f"\n📋 Research plan ({len(queries)} queries):")
        for i, q in enumerate(queries, 1):
            print(f"   {i}. {q}")
    elif etype == "round_start":
        print(f"\n{'─'*50}")
        print(f"🔄 Search round {event['round']} / {config.MAX_SEARCH_ROUNDS}")
    elif etype == "query_search":
        print(f"  🔎 Searching: \"{event.get('query', '')}\"")
    elif etype == "fetch_url":
        print(f"  🌐 Fetching: {event.get('url', '')[:70]} …")
    elif etype == "summarize_source":
        title = event.get("title", "")[:60]
        print(f"  📝 Summarising {event.get('i')}/{event.get('total')}: {title} …")
    elif etype == "check_sufficient":
        if event.get("sufficient"):
            print("✅ [Planner] Sufficient information collected.")
        else:
            print(f"➕ [Planner] Needs more info. Follow-up: '{event.get('follow_up', '')}'")
    elif etype == "report_start":
        print("\n✍️  [Report Generator] Generating report …")
    elif etype == "report_done":
        print(f"\n✅ Report saved to: {event.get('path', '')}")
        print(f"{'='*60}\n")
    elif etype == "error":
        print(f"\n❌ Error: {event.get('message', '')}")


# ── Private helpers ───────────────────────────────────────────────────────────

def _run_queries(queries: list[str], on_event=None) -> list[dict]:
    """
    Run each search query and fetch the text of each result page.

    Returns:
        List of source dicts with keys: url, title, snippet, text.
    """
    seen_urls:   set[str]   = set()
    raw_sources: list[dict] = []

    for query in queries:
        _emit(on_event, {"type": "query_search", "query": query})
        results = search(query)

        for result in results:
            url = result.get("url", "")
            if not url or url in seen_urls:
                continue          # skip duplicates
            seen_urls.add(url)

            title = result.get("title", "Untitled")
            _emit(on_event, {"type": "fetch_url", "url": url, "title": title})
            page_text = fetch_page_text(url)

            raw_sources.append({
                "url":     url,
                "title":   title,
                "snippet": result.get("snippet", ""),
                "text":    page_text,
            })

    return raw_sources
