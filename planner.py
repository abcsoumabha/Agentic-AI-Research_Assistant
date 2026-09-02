"""
planner.py
==========
Research Planner  –  the "brain" of the agent.

Responsibilities:
  1. Break a research question into focused sub-queries.
  2. Decide (after each search round) whether enough information
     has been collected or if another round is needed.

All decisions are made by the LLM; the planner itself contains
no hard-coded domain knowledge.

Events emitted:
  {"type": "log", "message": "Creating research plan …"}
  {"type": "log", "message": "Checking if research is complete …"}
  {"type": "check_sufficient", "sufficient": bool, "follow_up": str}
"""

from llm_client import ask_llm


def create_research_plan(question: str, on_event=None) -> list[str]:
    """
    Ask the LLM to decompose the research question into a list of
    concrete search queries.

    Args:
        question:  The original research question from the user.
        on_event:  Optional event callback.

    Returns:
        A list of search query strings (typically 3-5 queries).
    """
    _emit(on_event, {"type": "log", "message": "Creating research plan …"})

    prompt = f"""You are a research assistant helping plan how to answer the following question:

QUESTION: {question}

Break this question down into 3 to 5 focused web search queries that together
will give comprehensive coverage of the topic.

Rules:
- Each query must be on its own line.
- Do NOT number the queries.
- Do NOT add any extra explanation — output ONLY the queries.

Example output:
what is quantum entanglement explained simply
quantum entanglement real world applications
history of quantum entanglement discovery
quantum entanglement vs classical physics differences
"""
    raw = ask_llm(prompt)

    # Parse: one query per non-empty line
    queries = [line.strip() for line in raw.splitlines() if line.strip()]
    return queries


def should_continue_research(
    question: str,
    summaries: list[str],
    round_num: int,
    max_rounds: int,
    on_event=None,
) -> tuple[bool, str]:
    """
    Ask the LLM whether the collected summaries are sufficient to
    answer the research question, or if another search round is needed.

    Args:
        question:   The original research question.
        summaries:  List of text summaries collected so far.
        round_num:  Current round number (1-based).
        max_rounds: Maximum allowed rounds.
        on_event:   Optional event callback.

    Returns:
        (continue_flag, follow_up_query)
          continue_flag  – True  → do another round with follow_up_query
                         – False → enough info, stop searching
          follow_up_query – the next search query (empty string if stopping)
    """
    if round_num >= max_rounds:
        _emit(on_event, {
            "type":      "check_sufficient",
            "sufficient": True,
            "follow_up": "",
            "reason":    f"Reached max search rounds ({max_rounds}).",
        })
        return False, ""

    _emit(on_event, {
        "type":    "log",
        "message": f"Evaluating research completeness (round {round_num}) …",
    })

    combined = "\n\n---\n\n".join(summaries)

    prompt = f"""You are a critical research evaluator.

RESEARCH QUESTION: {question}

INFORMATION COLLECTED SO FAR:
{combined}

Evaluate whether the collected information is sufficient to write a complete,
accurate, and well-rounded answer to the research question.

If YES (sufficient): respond with exactly one line:
SUFFICIENT

If NO (gaps remain): respond with exactly two lines:
INSUFFICIENT
<one specific follow-up search query to fill the gap>

Do NOT add any other text.
"""
    raw   = ask_llm(prompt).strip()
    lines = [l.strip() for l in raw.splitlines() if l.strip()]

    if lines and lines[0].upper() == "SUFFICIENT":
        _emit(on_event, {"type": "check_sufficient", "sufficient": True,  "follow_up": ""})
        return False, ""

    follow_up = lines[1] if len(lines) > 1 else "more details about " + question
    _emit(on_event, {"type": "check_sufficient", "sufficient": False, "follow_up": follow_up})
    return True, follow_up


# ── Private helpers ───────────────────────────────────────────────────────────

def _emit(on_event, event: dict) -> None:
    if on_event is not None:
        try:
            on_event(event)
        except Exception:
            pass
