"""
app.py
======
Streamlit Web UI for the Research Assistant.

Run with:
    streamlit run app.py

Features:
  - Premium dark-theme UI with gradient header
  - Live agent step display via st.status()
  - Full report rendered as Markdown
  - One-click report download (.md)
  - Clickable source cards with snippets
  - Sidebar settings (max results, search rounds)
  - Comprehensive error handling
"""

import os
import sys
import traceback

import streamlit as st

# ── Page config (MUST be the very first Streamlit call) ───────────────────────
st.set_page_config(
    page_title="Research Assistant — Agentic AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com",
        "About":    "# Research Assistant\nPowered by Agentic AI + DuckDuckGo + Google Gemini",
    },
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Google Font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global ── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0d0d1a 0%, #0f1229 40%, #0a1628 100%);
        min-height: 100vh;
    }

    /* ── Hide default Streamlit chrome ── */
    #MainMenu  { visibility: hidden; }
    footer     { visibility: hidden; }

    /* ── Gradient hero header ── */
    .hero {
        background: linear-gradient(135deg,
            rgba(108, 99, 255, 0.18) 0%,
            rgba(79,  172, 254, 0.12) 60%,
            rgba(108,  99, 255, 0.08) 100%);
        border: 1px solid rgba(108, 99, 255, 0.25);
        border-radius: 20px;
        padding: 2.2rem 2.5rem 1.8rem;
        margin-bottom: 2rem;
        backdrop-filter: blur(12px);
    }
    .hero h1 {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 0.3rem 0;
        line-height: 1.2;
    }
    .hero p {
        color: #94a3b8;
        font-size: 1rem;
        margin: 0;
        font-weight: 400;
    }
    .hero .badge {
        display: inline-block;
        background: rgba(108,99,255,0.2);
        border: 1px solid rgba(108,99,255,0.4);
        border-radius: 20px;
        padding: 0.2rem 0.8rem;
        font-size: 0.75rem;
        color: #a78bfa;
        margin-right: 0.4rem;
        margin-top: 0.6rem;
        font-weight: 500;
    }

    /* ── Text area ── */
    .stTextArea textarea {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(108,99,255,0.3) !important;
        border-radius: 14px !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
        transition: border-color 0.2s ease;
    }
    .stTextArea textarea:focus {
        border-color: rgba(108,99,255,0.7) !important;
        box-shadow: 0 0 0 3px rgba(108,99,255,0.15) !important;
    }
    .stTextArea label {
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* ── Primary button ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6c63ff 0%, #4facfe 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 0.65rem 1.5rem !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        box-shadow: 0 4px 20px rgba(108,99,255,0.35) !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 28px rgba(108,99,255,0.5) !important;
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(0) !important;
    }

    /* ── Download button ── */
    .stDownloadButton > button {
        background: rgba(52, 211, 153, 0.1) !important;
        border: 1px solid rgba(52, 211, 153, 0.4) !important;
        border-radius: 10px !important;
        color: #34d399 !important;
        font-weight: 600 !important;
        transition: all 0.15s ease !important;
    }
    .stDownloadButton > button:hover {
        background: rgba(52, 211, 153, 0.18) !important;
        border-color: rgba(52, 211, 153, 0.7) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Status/progress widget ── */
    [data-testid="stStatusWidget"] {
        border: 1px solid rgba(108,99,255,0.2) !important;
        border-radius: 14px !important;
        background: rgba(108,99,255,0.04) !important;
    }

    /* ── Report container ── */
    .report-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(148,163,184,0.12);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin: 1rem 0;
        color: #e2e8f0;
        line-height: 1.7;
    }
    .report-card h1 { color: #a78bfa; font-size: 1.6rem; font-weight: 700; }
    .report-card h2 { color: #60a5fa; font-size: 1.25rem; font-weight: 600; border-bottom: 1px solid rgba(96,165,250,0.2); padding-bottom: 0.4rem; }
    .report-card h3 { color: #34d399; font-size: 1.05rem; font-weight: 600; }
    .report-card a  { color: #60a5fa; text-decoration: none; }
    .report-card a:hover { text-decoration: underline; }
    .report-card hr { border-color: rgba(148,163,184,0.15); }
    .report-card code { background: rgba(108,99,255,0.15); border-radius: 4px; padding: 0.1rem 0.4rem; color: #a78bfa; }

    /* ── Source card ── */
    .source-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(148,163,184,0.1);
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.7rem;
        transition: border-color 0.2s ease;
    }
    .source-card:hover { border-color: rgba(108,99,255,0.35); }
    .source-card .src-num  { color: #6c63ff; font-weight: 700; font-size: 0.85rem; }
    .source-card .src-title { color: #60a5fa; font-weight: 600; font-size: 0.95rem; }
    .source-card .src-url  { color: #64748b; font-size: 0.75rem; font-family: monospace; }
    .source-card .src-desc { color: #94a3b8; font-size: 0.85rem; margin-top: 0.3rem; line-height: 1.5; }

    /* ── Section heading ── */
    .section-heading {
        display: flex; align-items: center; gap: 0.6rem;
        font-size: 1.15rem; font-weight: 700; color: #e2e8f0;
        margin: 1.5rem 0 0.8rem;
    }
    .section-heading .dot {
        width: 8px; height: 8px; border-radius: 50%;
        background: linear-gradient(135deg, #6c63ff, #4facfe);
        flex-shrink: 0;
    }

    /* ── Sidebar styling ── */
    [data-testid="stSidebar"] {
        background: rgba(13,13,26,0.95) !important;
        border-right: 1px solid rgba(108,99,255,0.15) !important;
    }
    [data-testid="stSidebar"] .stMarkdown h3 { color: #a78bfa; }

    /* ── Metrics ── */
    [data-testid="metric-container"] {
        background: rgba(108,99,255,0.08);
        border: 1px solid rgba(108,99,255,0.2);
        border-radius: 10px;
        padding: 0.6rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Import agent (after page config) ─────────────────────────────────────────
# Use abspath so this works both locally and on Streamlit Cloud,
# where __file__ may be a relative path like "app.py" instead of an absolute one.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

try:
    import config
    from agent import run_research_agent
    _IMPORT_ERROR = None
except Exception as _e:
    _IMPORT_ERROR = str(_e)

# ── Pull API key from Streamlit Cloud secrets (if deployed there) ─────────────
# On Streamlit Cloud, secrets are set via the dashboard (App → Settings → Secrets).
# Locally, they come from .streamlit/secrets.toml  (keep that file out of Git!).
# This overrides config.py so you never need to commit your key to GitHub.
if not _IMPORT_ERROR:
    try:
        _cloud_key = st.secrets.get("GEMINI_API_KEY", "")
        if _cloud_key:
            config.GEMINI_API_KEY = _cloud_key
    except Exception:
        pass   # st.secrets not available in this environment — use config.py


# ── Markdown → HTML helper (defined early so it's available everywhere) ────────

def _md_to_html(md: str) -> str:
    """
    Convert Markdown to HTML for rendering inside a styled <div>.
    Uses the `markdown` package if available, otherwise falls back
    to a basic regex approach for common elements.
    """
    try:
        import markdown  # type: ignore
        return markdown.markdown(
            md,
            extensions=["extra", "nl2br"],
        )
    except ImportError:
        pass

    # Minimal fallback — just preserve newlines as <br>
    import re
    html = md
    # Bold
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    # Italic
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    # Headers
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$",  r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$",   r"<h1>\1</h1>", html, flags=re.MULTILINE)
    # Links
    html = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2" target="_blank">\1</a>', html)
    # Horizontal rules
    html = re.sub(r"^---$", r"<hr>", html, flags=re.MULTILINE)
    # Bullet lists
    html = re.sub(r"^[-•] (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    html = re.sub(r"(<li>.+</li>)", r"<ul>\1</ul>", html, flags=re.DOTALL)
    # Line breaks
    html = html.replace("\n", "<br>")
    return html


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    max_results = st.slider(
        "Results per query",
        min_value=3, max_value=10,
        value=config.MAX_SEARCH_RESULTS if _IMPORT_ERROR is None else 5,
        help="How many web pages to fetch for each search query.",
    )
    max_rounds = st.slider(
        "Max search rounds",
        min_value=1, max_value=5,
        value=config.MAX_SEARCH_ROUNDS if _IMPORT_ERROR is None else 3,
        help="How many times the agent can search for more info.",
    )

    st.divider()
    st.markdown("### 🔑 API Key")
    api_key_override = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="Leave blank to use config.py",
        help="Override the key in config.py for this session.",
    )

    st.divider()
    st.markdown("### 🧠 How It Works")
    st.markdown(
        """
        1. **Planner** breaks your question into focused search queries.
        2. **Search Tool** fetches web pages via DuckDuckGo.
        3. **Summarizer** condenses each page with the LLM.
        4. **Planner** decides if more info is needed.
        5. **Report Generator** writes a full Markdown report.
        """,
        help="The 5-step agentic loop",
    )

    st.divider()
    st.caption("Powered by Google Gemini · DuckDuckGo · Streamlit")


# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
        <h1>🤖 Research Assistant</h1>
        <p>An agentic AI that autonomously searches the web, collects sources, and writes a full research report — all for free.</p>
        <span class="badge">Agentic AI</span>
        <span class="badge">DuckDuckGo Search</span>
        <span class="badge">Google Gemini</span>
        <span class="badge">Multi-round Research</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Import error guard ────────────────────────────────────────────────────────
if _IMPORT_ERROR:
    st.error(
        f"**Failed to import project modules:** `{_IMPORT_ERROR}`\n\n"
        "Make sure you are running `streamlit run app.py` from the project folder "
        "and that all dependencies are installed:\n```\npip install -r requirements.txt\n```"
    )
    st.stop()

# ── Research question input ───────────────────────────────────────────────────
st.markdown(
    '<div class="section-heading"><div class="dot"></div>Your Research Question</div>',
    unsafe_allow_html=True,
)

question = st.text_area(
    label="Research Question",
    label_visibility="collapsed",
    placeholder=(
        "e.g.  How does the immune system fight viruses?\n"
        "      What are the environmental impacts of electric vehicles?\n"
        "      Explain how large language models work."
    ),
    height=110,
    key="question_input",
)

# Centre the run button
col_l, col_btn, col_r = st.columns([2, 3, 2])
with col_btn:
    run_clicked = st.button(
        "🔍  Start Research",
        use_container_width=True,
        type="primary",
        key="run_btn",
    )

# ── Validation ────────────────────────────────────────────────────────────────
if run_clicked:
    if not question.strip():
        st.warning("⚠️ Please enter a research question before clicking Start.")
        st.stop()

    # Apply sidebar overrides
    config.MAX_SEARCH_RESULTS = max_results
    config.MAX_SEARCH_ROUNDS  = max_rounds
    if api_key_override.strip():
        config.GEMINI_API_KEY = api_key_override.strip()

    # Validate API key — use sidebar override, inline entry, or config value
    effective_key = api_key_override.strip() or config.GEMINI_API_KEY
    if effective_key:
        config.GEMINI_API_KEY = effective_key
    else:
        st.warning(
            "**No Gemini API key found.**  "
            "Paste your key in the field above and click **Apply Key**, "
            "or enter it in the sidebar under **API Key**."
        )
        st.stop()

    # ── State containers ──────────────────────────────────────────────────────
    # Use a mutable dict so the nested on_event() callback can write to it
    # without needing 'nonlocal' (which only works inside real functions).
    _state = {
        "report_md": "",
        "sources":   [],
        "error":     "",
    }

    # ── Metrics row ───────────────────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    sources_count   = m1.empty()
    rounds_count    = m2.empty()
    queries_count   = m3.empty()

    _metrics = {"sources": 0, "rounds": 0, "queries": 0}

    def _refresh_metrics():
        sources_count.metric("📄 Sources Collected", _metrics["sources"])
        rounds_count.metric("🔄 Search Rounds",      _metrics["rounds"])
        queries_count.metric("🔎 Queries Run",        _metrics["queries"])

    _refresh_metrics()

    # ── Live progress via st.status() ────────────────────────────────────────
    st.markdown(
        '<div class="section-heading"><div class="dot"></div>Research Progress</div>',
        unsafe_allow_html=True,
    )

    with st.status("🔍 Researching your question …", expanded=True) as status:

        def on_event(event: dict):
            """Translate agent events into Streamlit status updates."""
            etype = event.get("type", "")

            if etype == "plan_created":
                queries = event.get("queries", [])
                _metrics["queries"] += len(queries)
                status.write(f"**📋 Research Plan** — {len(queries)} focused search queries:")
                for q in queries:
                    status.write(f"&nbsp;&nbsp;&nbsp;• *{q}*")

            elif etype == "round_start":
                rnd = event.get("round", "?")
                _metrics["rounds"] = rnd
                status.write(f"---\n**🔄 Search Round {rnd} / {config.MAX_SEARCH_ROUNDS}**")

            elif etype == "query_search":
                status.write(f"&nbsp;&nbsp;🔎 `{event.get('query', '')}`")

            elif etype == "fetch_url":
                url   = event.get("url", "")
                title = event.get("title", url)[:75]
                status.write(f"&nbsp;&nbsp;🌐 Fetching **{title}**")
                _metrics["sources"] += 1

            elif etype == "summarize_source":
                i     = event.get("i", "?")
                total = event.get("total", "?")
                title = event.get("title", "")[:65]
                status.write(f"&nbsp;&nbsp;📝 Summarising {i}/{total}: *{title}*")

            elif etype == "check_sufficient":
                if event.get("sufficient"):
                    status.write("✅ **Sufficient information collected — moving to report generation.**")
                else:
                    fup = event.get("follow_up", "")
                    _metrics["queries"] += 1
                    status.write(f"➕ **Needs more info** — follow-up query: `{fup}`")

            elif etype == "report_start":
                status.write("---\n**✍️ Generating your research report …**")

            elif etype == "report_done":
                _state["report_md"] = event.get("report_md", "")
                _state["sources"]   = event.get("sources", [])

            elif etype == "error":
                _state["error"] = event.get("message", "Unknown error")
                status.write(f"⚠️ {_state['error']}")

            elif etype == "log":
                pass   # suppress generic log lines from the UI

            _refresh_metrics()

        # ── Run the agent ─────────────────────────────────────────────────────
        try:
            report_md, report_path = run_research_agent(
                question.strip(), on_event=on_event
            )

            if report_md:
                _state["report_md"] = report_md
                status.update(
                    label=f"✅ Research complete! {_metrics['sources']} sources · "
                          f"{_metrics['rounds']} round(s)",
                    state="complete",
                    expanded=False,
                )
            else:
                status.update(
                    label="⚠️ Completed but no content was collected. Try a different question.",
                    state="error",
                )

        except EnvironmentError as env_err:
            # Missing API key or environment problem
            status.update(label="❌ Configuration error", state="error")
            st.error(
                f"**Configuration Error:** {env_err}\n\n"
                "Set your Gemini API key in the sidebar or in `config.py`."
            )
            st.stop()

        except ConnectionError as conn_err:
            # Ollama not running / network failure
            status.update(label="❌ Connection error", state="error")
            st.error(
                f"**Connection Error:** {conn_err}\n\n"
                "Check your internet connection and try again."
            )
            st.stop()

        except Exception as exc:
            status.update(label="❌ Unexpected error", state="error")
            st.error(f"**Unexpected Error:** {exc}")
            # Cannot use st.expander here — st.status is itself an expander
            st.code(traceback.format_exc(), language="python")
            st.stop()

    # ── Report ────────────────────────────────────────────────────────────────
    final_report_md = _state["report_md"]
    final_sources   = _state["sources"]

    if final_report_md:
        st.markdown(
            '<div class="section-heading"><div class="dot"></div>Research Report</div>',
            unsafe_allow_html=True,
        )

        # Render report in styled card
        st.markdown(
            f'<div class="report-card">{_md_to_html(final_report_md)}</div>',
            unsafe_allow_html=True,
        )

        # Download button
        import re as _re
        safe_q    = _re.sub(r"[^\w\s-]", "", question[:50]).strip().replace(" ", "_").lower()
        dl_name   = f"research_report_{safe_q}.md"

        st.download_button(
            label="⬇️  Download Report (.md)",
            data=final_report_md.encode("utf-8"),
            file_name=dl_name,
            mime="text/markdown",
            use_container_width=False,
        )

    # ── Sources ───────────────────────────────────────────────────────────────
    if final_sources:
        st.markdown(
            '<div class="section-heading"><div class="dot"></div>'
            f'Sources ({len(final_sources)})</div>',
            unsafe_allow_html=True,
        )
        with st.expander(f"🔗 View all {len(final_sources)} sources", expanded=False):
            for i, src in enumerate(final_sources, 1):
                title   = src.get("title",   "Untitled")
                url     = src.get("url",     "#")
                snippet = src.get("snippet", "")
                if not snippet:
                    snippet = src.get("summary", "")[:200]

                st.markdown(
                    f"""
                    <div class="source-card">
                        <div class="src-num">Source {i}</div>
                        <div class="src-title">
                            <a href="{url}" target="_blank" rel="noopener">{title}</a>
                        </div>
                        <div class="src-url">{url[:80]}</div>
                        <div class="src-desc">{snippet[:220]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ── Welcome state (no search yet) ────────────────────────────────────────────
else:
    st.markdown(
        """
        <div style="
            text-align:center; padding: 3rem 1rem; color: #475569;
        ">
            <div style="font-size:4rem; margin-bottom:1rem;">🔬</div>
            <div style="font-size:1.1rem; font-weight:500; color:#64748b;">
                Enter a research question above and click <strong style="color:#6c63ff">Start Research</strong>.
            </div>
            <div style="font-size:0.9rem; margin-top:0.8rem; color:#475569;">
                The agent will search the web, collect sources, and generate a full report automatically.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



