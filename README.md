# 🤖 Research Assistant — Agentic AI

An **agentic AI project** in Python that autonomously researches any question by searching the web, collecting and summarising multiple sources, and generating a polished Markdown report — with a beautiful Streamlit web interface.

---

## 🚀 Quick Start

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your free Gemini API key
$env:GEMINI_API_KEY = "your_key_here"   # PowerShell
# OR: set GEMINI_API_KEY=your_key_here  (CMD)

# 3. Launch the web interface
streamlit run app.py

# 4. (Optional) Run via CLI instead
python main.py "How does the immune system fight viruses?"
```

> Get a **free** Gemini API key at <https://aistudio.google.com/app/apikey>

---

## 🧠 What Is Agentic AI?

A traditional AI program follows a fixed script: you give it input, it returns output, done.

An **agentic AI** is different — it has **goals, tools, and the ability to make decisions**:

| Concept | Meaning |
|---|---|
| **Agent** | An AI that takes sequences of actions to reach a goal |
| **Tools** | Capabilities the agent can use (search, read, write) |
| **Planning** | The agent decides *what* to do next |
| **Loop** | The agent keeps acting until the goal is met |
| **Autonomy** | No human needed between each step |

> Think of it like hiring a research intern who reads the brief, finds sources, decides whether they have enough information, and then writes the report — all without you prompting each step.

---

## 🏗️ Architecture

The project has four specialised components wired together by an agentic loop:

```
┌─────────────────────────────────────────────────────────────┐
│                   USER QUESTION                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │       1. PLANNER             │  planner.py
         │                              │
         │  • Reads the question        │
         │  • Creates 3-5 sub-queries   │
         └──────────────┬───────────────┘
                        │ queries[]
                        ▼
         ┌──────────────────────────────┐
         │     2. WEB SEARCH TOOL       │  tools/search_tool.py
         │                              │
         │  • DuckDuckGo → URL list     │
         │  • Fetches each page         │
         │  • Extracts plain text       │
         └──────────────┬───────────────┘
                        │ raw_sources[]
                        ▼
         ┌──────────────────────────────┐
         │     3. SUMMARIZER            │  summarizer.py
         │                              │
         │  • LLM reads each page       │
         │  • Writes bullet summaries   │
         │  • Filters irrelevant pages  │
         └──────────────┬───────────────┘
                        │ summaries[]
                        ▼
         ┌──────────────────────────────┐  ◄─────────────────────┐
         │    PLANNER (decision)        │  planner.py            │
         │                              │                        │
         │  ? "Is there enough info?"   │                        │
         │                              │                        │
         │  YES ──► continue to report  │                        │
         │  NO  ──► create follow-up    │────── follow-up ───────┘
         │          query & search more │      (up to 3 rounds)
         └──────────────┬───────────────┘
                        │ (enough info)
                        ▼
         ┌──────────────────────────────┐
         │    4. REPORT GENERATOR       │  report_generator.py
         │                              │
         │  • Synthesises all summaries │
         │  • Writes structured report  │
         │  • Saves to reports/ folder  │
         └──────────────┬───────────────┘
                        │
                        ▼
              📄 Markdown Report
         (displayed in UI + downloadable)
```

### The "Agentic" Part — The Loop in `agent.py`

```python
# Simplified pseudocode of the agentic loop (agent.py)

queries = planner.create_plan(question)          # Step 1: plan

for round in range(MAX_ROUNDS):
    sources = search_tool.run(queries)            # Step 2: search
    summaries = summarizer.summarise(sources)     # Step 3: summarise

    enough, follow_up = planner.check(summaries)  # Step 4: decide
    if enough:
        break                                     # ← autonomous stopping
    queries = [follow_up]                         # ← autonomous follow-up

report = report_generator.write(summaries)        # Step 5: report
```

The key insight: **no human decides when to stop** — the Planner LLM evaluates the collected information and makes that call autonomously.

---

## 🔌 Event Callback System

All components communicate with the UI via a thin event system:

```python
# agent.py runs research and fires events to whoever is listening

def run_research_agent(question, on_event=None):
    ...
    _emit(on_event, {"type": "plan_created", "queries": [...]})
    _emit(on_event, {"type": "fetch_url",    "url": "...", "title": "..."})
    _emit(on_event, {"type": "report_done",  "report_md": "..."})
    ...
```

| Listener | Uses events for |
|---|---|
| `main.py` (CLI) | `on_event=None` → pretty-prints to terminal |
| `app.py` (Streamlit) | updates `st.status()` live in the browser |

This design keeps the agent logic **completely UI-agnostic** — you can plug in any interface.

---

## 🗂️ Project Structure

```
research_assistant/
│
├── app.py               ← Streamlit web interface ✨ (run this for the UI)
├── main.py              ← Command-line interface
│
├── agent.py             ← Agentic loop — orchestrates everything
├── planner.py           ← Research Planner (plan + evaluate)
├── summarizer.py        ← Source Summarizer
├── report_generator.py  ← Report Generator
├── llm_client.py        ← LLM backend abstraction (Gemini / Ollama)
├── config.py            ← All settings in one place
│
├── tools/
│   ├── __init__.py
│   └── search_tool.py   ← Web Search Tool (DuckDuckGo + BeautifulSoup)
│
├── reports/             ← Generated Markdown reports saved here
├── test_components.py   ← 10 offline unit tests
├── requirements.txt
└── README.md
```

---

## ⚙️ Configuration (`config.py`)

| Setting | Default | Description |
|---|---|---|
| `LLM_BACKEND` | `"gemini"` | `"gemini"` or `"ollama"` |
| `GEMINI_MODEL` | `"gemini-2.0-flash"` | Free-tier Gemini model |
| `MAX_SEARCH_RESULTS` | `5` | URLs fetched per query |
| `MAX_CONTENT_CHARS` | `3000` | Characters extracted per page |
| `MAX_SEARCH_ROUNDS` | `3` | Max agentic search iterations |
| `REPORTS_DIR` | `"reports"` | Output folder for reports |

All settings can also be changed live from the **Streamlit sidebar**.

---

## 🦙 Using Ollama (Fully Offline — No API Key)

1. Install Ollama: <https://ollama.com>
2. Pull a model: `ollama pull llama3`
3. In `config.py`, set:
   ```python
   LLM_BACKEND  = "ollama"
   OLLAMA_MODEL = "llama3"
   ```
4. Run: `streamlit run app.py`

Web search still uses DuckDuckGo — no keys, no cost.

---

## 🧪 Running Tests

```powershell
python -X utf8 test_components.py
```

Tests are **fully offline** (no LLM / internet). They mock the LLM and network to verify:
- Config loads correctly
- Report generator writes files and builds references
- Search tool truncates long pages and handles bad URLs
- Planner correctly parses LLM output and makes stop/continue decisions

---

## 📄 Report Format

Reports are saved as `reports/<question>_<timestamp>.md` and include:

```markdown
# Research Report: Your Question
*Generated on 2026-09-03 01:00*

## Executive Summary
...

## Key Findings
### Finding Category 1
...

## Conclusion
...

## References & Sources
1. **[Source Title](url)**
   *Brief description from DuckDuckGo snippet*
```

---

## 📋 Requirements

- Python 3.10+
- Internet connection (for DuckDuckGo search)
- A **free** Gemini API key **or** a local Ollama installation
