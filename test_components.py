"""
test_components.py
==================
Basic unit-style tests for individual components.

These tests do NOT call the LLM or the internet — they only verify
that the non-LLM logic works correctly (parsing, file I/O, helpers).

Run with:
    python test_components.py
"""

import os
import sys
import tempfile
import unittest


# ── Test: config loads without errors ─────────────────────────────────────────
class TestConfig(unittest.TestCase):
    def test_import_config(self):
        import config
        self.assertIn(config.LLM_BACKEND, ("gemini", "ollama"))
        self.assertGreater(config.MAX_SEARCH_RESULTS, 0)
        self.assertGreater(config.MAX_CONTENT_CHARS, 0)
        self.assertEqual(config.REPORTS_DIR, "reports")

    def test_http_headers_present(self):
        import config
        self.assertIn("User-Agent", config.HTTP_HEADERS)


# ── Test: report_generator helper functions ────────────────────────────────────
class TestReportGenerator(unittest.TestCase):
    def setUp(self):
        """Patch the LLM call so we don't make real API requests."""
        import report_generator
        self._orig_ask = report_generator.ask_llm
        report_generator.ask_llm = lambda prompt: (
            "## Executive Summary\nTest summary.\n"
            "## Key Findings\n### Finding 1\nDetails here.\n"
            "## Conclusion\nAll good."
        )

    def tearDown(self):
        import report_generator
        report_generator.ask_llm = self._orig_ask

    def test_generate_report_contains_question(self):
        import report_generator
        sources = [{"url": "https://example.com", "title": "Example", "summary": "- bullet"}]
        report = report_generator.generate_report("What is AI?", sources)
        self.assertIn("What is AI?", report)
        self.assertIn("## References", report)
        self.assertIn("https://example.com", report)

    def test_save_report_creates_file(self):
        import report_generator, config
        # Use a temp directory instead of the real reports folder
        orig_dir = config.REPORTS_DIR
        with tempfile.TemporaryDirectory() as tmpdir:
            config.REPORTS_DIR = tmpdir
            path = report_generator.save_report("Test question", "# Hello\nContent.")
            self.assertTrue(os.path.isfile(path))
            with open(path, encoding="utf-8") as f:
                content = f.read()
            self.assertIn("Hello", content)
        config.REPORTS_DIR = orig_dir


# ── Test: search_tool text extraction (offline) ───────────────────────────────
class TestSearchToolOffline(unittest.TestCase):
    def test_fetch_page_text_handles_bad_url(self):
        from tools.search_tool import fetch_page_text
        result = fetch_page_text("http://this-url-does-not-exist-xyz.invalid")
        self.assertTrue(result.startswith("[Could not fetch page:"))

    def test_fetch_page_text_truncates(self):
        """Mock requests.get to return a very long page and verify truncation."""
        import unittest.mock as mock
        import config
        from tools.search_tool import fetch_page_text

        long_html = "<html><body>" + ("word " * 10_000) + "</body></html>"
        fake_response = mock.Mock()
        fake_response.text = long_html
        fake_response.raise_for_status = mock.Mock()

        with mock.patch("tools.search_tool.requests.get", return_value=fake_response):
            result = fetch_page_text("http://example.com/long")

        self.assertLessEqual(len(result), config.MAX_CONTENT_CHARS + 20)
        self.assertIn("truncated", result)


# ── Test: planner output parsing (offline) ────────────────────────────────────
class TestPlannerOffline(unittest.TestCase):
    def setUp(self):
        import planner
        self._orig_ask = planner.ask_llm
        # Return three fake queries
        planner.ask_llm = lambda p: "what is machine learning\nML applications in healthcare\nhistory of machine learning"

    def tearDown(self):
        import planner
        planner.ask_llm = self._orig_ask

    def test_create_plan_returns_list(self):
        from planner import create_research_plan
        plan = create_research_plan("What is machine learning?")
        self.assertIsInstance(plan, list)
        self.assertEqual(len(plan), 3)
        self.assertIn("what is machine learning", plan)

    def test_should_continue_false_when_max_reached(self):
        from planner import should_continue_research
        cont, query = should_continue_research("Q", ["some info"], 3, 3)
        self.assertFalse(cont)
        self.assertEqual(query, "")

    def test_should_continue_false_on_sufficient(self):
        import planner
        planner.ask_llm = lambda p: "SUFFICIENT"
        from planner import should_continue_research
        cont, query = should_continue_research("Q", ["lots of info"], 1, 3)
        self.assertFalse(cont)

    def test_should_continue_true_on_insufficient(self):
        import planner
        planner.ask_llm = lambda p: "INSUFFICIENT\nmore details about X"
        from planner import should_continue_research
        cont, query = should_continue_research("Q", ["limited info"], 1, 3)
        self.assertTrue(cont)
        self.assertEqual(query, "more details about X")


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[TEST] Running Research Assistant component tests ...\n")
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    # Add test cases
    for cls in [TestConfig, TestReportGenerator, TestSearchToolOffline, TestPlannerOffline]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {len(result.failures)} test(s) failed.")
        sys.exit(1)
