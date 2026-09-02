"""
main.py
=======
Entry point for the Research Assistant  (command-line interface).

Run with:
    python main.py
or pass a question directly:
    python main.py "What is quantum computing?"

For the graphical web interface, run:
    streamlit run app.py
"""

import sys
from agent import run_research_agent


BANNER = r"""
 ____                                      _       _            _     _
|  _ \ ___  ___  ___  __ _ _ __ ___  ___ | |__   / \   ___ ___(_)___| |_
| |_) / _ \/ __|/ _ \/ _` | '__/ __|/ __|| '_ \ / _ \ / __/ __| / __| __|
|  _ <  __/\__ \  __/ (_| | | | (__| (__ | | | / ___ \\__ \__ \ \__ \ |_
|_| \_\___||___/\___|\__,_|_|  \___|\___||_| |_/_/   \_\___/___/_|___/\__|

           🤖  Agentic Research Assistant  |  powered by Gemini + DuckDuckGo
           💻  For the web UI run: streamlit run app.py
"""


def main() -> None:
    print(BANNER)

    # ── Get research question ─────────────────────────────────────────────────
    if len(sys.argv) > 1:
        # Question passed as a command-line argument
        question = " ".join(sys.argv[1:]).strip()
    else:
        # Interactive prompt
        print("Ask me any research question and I'll search the web,")
        print("collect information from multiple sources, and generate")
        print("a Markdown report saved in the `reports/` folder.\n")
        question = input("📝 Your research question: ").strip()

    if not question:
        print("❌ No question provided. Exiting.")
        sys.exit(1)

    # ── Run the agent (on_event=None → prints to console) ────────────────────
    try:
        report_md, report_path = run_research_agent(question)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

    if report_path:
        print(f"\n🎉 Done! Open your report here:")
        print(f"   {report_path}\n")
    else:
        print("\n❌ Research failed — no report was generated.")
        sys.exit(1)


if __name__ == "__main__":
    main()
