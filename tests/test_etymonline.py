"""Unit tests for etymonline.py

Run with:
  pip install pytest
  pytest tests/
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Make the project root importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import etymonline as ety

# ── HTML fixtures ─────────────────────────────────────────────────────────────

# Minimal page that uses hashed CSS class names (mirrors etymonline's real structure)
HTML_WORD_PAGE = """
<html><body>
  <script id="__NEXT_DATA__" type="application/json">
    {"props":{"pageProps":{"entries":[
      {"name":"robot (n.)","meaning":"1923, from Czech <em>robota</em> 'forced labor'"},
      {"name":"robot (adj.)","meaning":"1930, from the noun."}
    ]}}}
  </script>
  <a href="/word/automaton">automaton</a>
  <a href="/word/android">android</a>
  <a href="/word/robot">robot</a>
</body></html>
"""

# Page without __NEXT_DATA__ — tests the broad-section HTML-scraping fallback
HTML_FALLBACK = """
<html><body>
  <section>
    <span class="word__name--XYZ">serendipity (n.)</span>
    <div class="word__deftext--ABC">1754, coined by Horace Walpole.</div>
  </section>
</body></html>
"""

# Page without __NEXT_DATA__ — tests the *primary* HTML path (word__deflist container)
HTML_PRIMARY_CONTAINER = """
<html><body>
  <div class="word__deflist--HASH">
    <span class="word__name--Q1">ephemeral (adj.)</span>
    <div class="word__deftext--Q2">1560s, from Greek ephemeros.</div>
  </div>
</body></html>
"""

# __NEXT_DATA__ present but with an empty entries list (zero-hit search)
HTML_EMPTY_NEXT_DATA = """
<html><body>
  <script id="__NEXT_DATA__" type="application/json">
    {"props":{"pageProps":{"entries":[]}}}
  </script>
  <nav><a href="/word/unrelated-nav-link">home</a></nav>
</body></html>
"""

# __NEXT_DATA__ present but with none of the recognised result keys
HTML_UNKNOWN_STRUCTURE = """
<html><body>
  <script id="__NEXT_DATA__" type="application/json">
    {"props":{"pageProps":{"someFutureKey":[{"name":"x","meaning":"y"}]}}}
  </script>
  <section>
    <span class="word__name--Z">fallback (n.)</span>
    <div class="word__deftext--Z">used when JSON structure is unrecognised.</div>
  </section>
</body></html>
"""

# A second word page whose related links point to unique words not in HTML_WORD_PAGE
HTML_AUTOMATON_PAGE = """
<html><body>
  <script id="__NEXT_DATA__" type="application/json">
    {"props":{"pageProps":{"entries":[
      {"name":"automaton (n.)","meaning":"1640s, from Greek automatos 'self-moving'"}
    ]}}}
  </script>
  <a href="/word/mechanical">mechanical</a>
  <a href="/word/clockwork">clockwork</a>
</body></html>
"""

# A search results page using __NEXT_DATA__
HTML_SEARCH = """
<html><body>
  <script id="__NEXT_DATA__" type="application/json">
    {"props":{"pageProps":{"results":[
      {"name":"galaxy (n.)","meaning":"late 14c., from Greek <i>galaxias</i>."},
      {"name":"nebula (n.)","meaning":"1660s, from Latin <em>nebula</em> 'mist'."}
    ]}}}
  </script>
</body></html>
"""

# ── Tests: parsing ────────────────────────────────────────────────────────────

class TestParseNextData(unittest.TestCase):
    def test_word_page_entries(self):
        entries = ety._parse_next_data(HTML_WORD_PAGE)
        self.assertIsNotNone(entries)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["word"], "robot (n.)")
        self.assertIn("Czech", entries[0]["etymology"])

    def test_search_page_entries(self):
        entries = ety._parse_next_data(HTML_SEARCH)
        self.assertIsNotNone(entries)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["word"], "galaxy (n.)")

    def test_html_stripped_from_etymology(self):
        entries = ety._parse_next_data(HTML_WORD_PAGE)
        # <em> tags should be stripped
        self.assertNotIn("<em>", entries[0]["etymology"])

    def test_missing_embed_returns_none(self):
        result = ety._parse_next_data("<html><body>no script here</body></html>")
        self.assertIsNone(result)

    def test_malformed_json_returns_none(self):
        html = '<script id="__NEXT_DATA__">{not valid json}</script>'
        self.assertIsNone(ety._parse_next_data(html))

    def test_empty_entries_list_returns_empty_list_not_none(self):
        # An authoritative zero-hit page should yield [] not None, so that
        # parse_entries() does NOT fall back to HTML and return spurious hits.
        result = ety._parse_next_data(HTML_EMPTY_NEXT_DATA)
        self.assertIsNotNone(result)
        self.assertEqual(result, [])

    def test_unrecognised_key_returns_none_so_html_fallback_runs(self):
        result = ety._parse_next_data(HTML_UNKNOWN_STRUCTURE)
        self.assertIsNone(result)


class TestParseHtmlFallback(unittest.TestCase):
    def test_broad_fallback_section(self):
        # HTML_FALLBACK has no container class — hits the broad <section> branch
        entries = ety._parse_html(HTML_FALLBACK)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["word"], "serendipity (n.)")
        self.assertIn("Walpole", entries[0]["etymology"])

    def test_primary_container_path(self):
        # HTML_PRIMARY_CONTAINER has a word__deflist container — exercises the
        # primary branch in _parse_html that the broad fallback never reaches.
        entries = ety._parse_html(HTML_PRIMARY_CONTAINER)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["word"], "ephemeral (adj.)")
        self.assertIn("Greek", entries[0]["etymology"])

    def test_parse_entries_prefers_next_data(self):
        # HTML_WORD_PAGE has __NEXT_DATA__ — should use it, not HTML fallback
        entries = ety.parse_entries(HTML_WORD_PAGE)
        self.assertEqual(entries[0]["word"], "robot (n.)")

    def test_parse_entries_falls_back_to_html(self):
        entries = ety.parse_entries(HTML_FALLBACK)
        self.assertEqual(entries[0]["word"], "serendipity (n.)")

    def test_parse_entries_empty_next_data_does_not_fall_back(self):
        # Embed present, zero results → authoritative empty; must NOT fall back
        # to HTML (which would pick up the nav link as a spurious entry).
        entries = ety.parse_entries(HTML_EMPTY_NEXT_DATA)
        self.assertEqual(entries, [])

    def test_parse_entries_unknown_structure_falls_back_to_html(self):
        # Unrecognised JSON key → None → HTML fallback should run
        entries = ety.parse_entries(HTML_UNKNOWN_STRUCTURE)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["word"], "fallback (n.)")


class TestParseRelated(unittest.TestCase):
    def test_extracts_related_links(self):
        related = ety.parse_related(HTML_WORD_PAGE, exclude="robot")
        self.assertIn("automaton", related)
        self.assertIn("android", related)
        # The excluded word must not appear
        self.assertNotIn("robot", related)

    def test_deduplicates(self):
        html = '<a href="/word/foo">foo</a><a href="/word/foo">foo again</a>'
        related = ety.parse_related(html)
        self.assertEqual(related.count("foo"), 1)


# ── Tests: cache ─────────────────────────────────────────────────────────────

class TestCache(unittest.TestCase):
    def setUp(self):
        self._orig_cache_dir = ety.CACHE_DIR
        self._tmpdir = tempfile.mkdtemp()
        ety.CACHE_DIR = self._tmpdir

    def tearDown(self):
        ety.CACHE_DIR = self._orig_cache_dir
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_set_and_get(self):
        ety.cache_set("mykey", {"x": 1})
        result = ety.cache_get("mykey")
        self.assertEqual(result, {"x": 1})

    def test_get_missing_returns_none(self):
        self.assertIsNone(ety.cache_get("does_not_exist"))

    def test_list(self):
        ety.cache_set("alpha", [])
        ety.cache_set("beta", [])
        keys = ety.cache_list()
        self.assertIn("alpha", keys)
        self.assertIn("beta", keys)

    def test_clear(self):
        ety.cache_set("a", [])
        ety.cache_set("b", [])
        removed = ety.cache_clear()
        self.assertEqual(removed, 2)
        self.assertEqual(ety.cache_list(), [])

    def test_cache_key_stable(self):
        k1 = ety._cache_key("word", "Robot")
        k2 = ety._cache_key("word", "robot")
        self.assertEqual(k1, k2)   # case-insensitive

    def test_cache_key_whitespace_normalised(self):
        # Related-word slugs scraped from HTML may carry leading/trailing spaces
        k1 = ety._cache_key("word", "robot")
        k2 = ety._cache_key("word", " robot ")
        self.assertEqual(k1, k2)

    def test_get_corrupted_cache_returns_none(self):
        # A partially-written cache file must not crash the CLI
        path = ety._cache_path("corrupted_key")
        os.makedirs(ety.CACHE_DIR, exist_ok=True)
        with open(path, "w") as f:
            f.write("this is not valid json {{{{")
        result = ety.cache_get("corrupted_key")
        self.assertIsNone(result)


# ── Tests: search / lookup (mocked network) ───────────────────────────────────

class TestSearch(unittest.TestCase):
    def setUp(self):
        self._orig_cache_dir = ety.CACHE_DIR
        self._tmpdir = tempfile.mkdtemp()
        ety.CACHE_DIR = self._tmpdir

    def tearDown(self):
        ety.CACHE_DIR = self._orig_cache_dir
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    @patch("etymonline.fetch", return_value=HTML_SEARCH)
    def test_search_fetches_and_caches(self, mock_fetch):
        results, from_cache = ety.search("galaxy")
        self.assertFalse(from_cache)
        self.assertEqual(len(results), 2)
        mock_fetch.assert_called_once()

        # Second call should hit cache, not network
        results2, from_cache2 = ety.search("galaxy")
        self.assertTrue(from_cache2)
        mock_fetch.assert_called_once()  # still only called once

    @patch("etymonline.fetch", return_value=HTML_SEARCH)
    def test_no_cache_bypasses_cache(self, mock_fetch):
        ety.search("galaxy")
        ety.search("galaxy", no_cache=True)
        self.assertEqual(mock_fetch.call_count, 2)

    def test_offline_with_no_cache_returns_empty(self):
        results, from_cache = ety.search("galaxy", offline=True)
        self.assertEqual(results, [])
        self.assertFalse(from_cache)

    def test_offline_with_cache_returns_cached(self):
        ety.cache_set(ety._cache_key("search", "galaxy"), [{"word": "galaxy", "etymology": "test"}])
        results, from_cache = ety.search("galaxy", offline=True)
        self.assertTrue(from_cache)
        self.assertEqual(results[0]["word"], "galaxy")


class TestLookup(unittest.TestCase):
    def setUp(self):
        self._orig_cache_dir = ety.CACHE_DIR
        self._tmpdir = tempfile.mkdtemp()
        ety.CACHE_DIR = self._tmpdir

    def tearDown(self):
        ety.CACHE_DIR = self._orig_cache_dir
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    @patch("etymonline.fetch", return_value=HTML_WORD_PAGE)
    def test_lookup_returns_entries_and_related(self, mock_fetch):
        result, from_cache = ety.lookup("robot")
        self.assertFalse(from_cache)
        self.assertEqual(result["word"], "robot")
        self.assertGreater(len(result["entries"]), 0)
        self.assertIn("automaton", result["related"])

    @patch("etymonline.fetch", return_value=HTML_WORD_PAGE)
    def test_lookup_caches_result(self, mock_fetch):
        ety.lookup("robot")
        _, from_cache = ety.lookup("robot")
        self.assertTrue(from_cache)
        mock_fetch.assert_called_once()


class TestExplore(unittest.TestCase):
    def setUp(self):
        self._orig_cache_dir = ety.CACHE_DIR
        self._tmpdir = tempfile.mkdtemp()
        ety.CACHE_DIR = self._tmpdir

    def tearDown(self):
        ety.CACHE_DIR = self._orig_cache_dir
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    @patch("etymonline.fetch", return_value=HTML_WORD_PAGE)
    def test_explore_depth1_includes_related(self, mock_fetch):
        explored = ety.explore("robot", depth=1)
        self.assertIn("robot", explored)
        # automaton and android are linked from HTML_WORD_PAGE
        self.assertIn("automaton", explored)
        self.assertIn("android", explored)
        # Entries for related words must be stored under their own key
        self.assertIsInstance(explored["automaton"].get("entries"), list)

    @patch("etymonline.fetch", return_value=HTML_WORD_PAGE)
    def test_explore_depth_zero_only_root(self, mock_fetch):
        explored = ety.explore("robot", depth=0)
        self.assertEqual(list(explored.keys()), ["robot"])
        mock_fetch.assert_called_once()

    def test_explore_depth2_follows_second_hop(self):
        # depth=2 should follow related words of the depth-1 words.
        # Provide distinct HTML per URL so we can verify the second hop fires.
        pages = {
            "https://www.etymonline.com/word/robot":    HTML_WORD_PAGE,
            "https://www.etymonline.com/word/automaton": HTML_AUTOMATON_PAGE,
            "https://www.etymonline.com/word/android":   HTML_WORD_PAGE,
        }
        def fake_fetch(url):
            return pages.get(url, HTML_WORD_PAGE)

        with patch("etymonline.fetch", side_effect=fake_fetch):
            explored = ety.explore("robot", depth=2)

        # Root + depth-1 words (automaton, android) + depth-2 words from
        # automaton's page (mechanical, clockwork)
        self.assertIn("robot", explored)
        self.assertIn("automaton", explored)
        self.assertIn("mechanical", explored)
        self.assertIn("clockwork", explored)
        self.assertGreater(len(explored), 3)


# ── Tests: DKL_LOOP ───────────────────────────────────────────────────────────

class TestDKLLoop(unittest.TestCase):
    def setUp(self):
        self._orig_cache_dir = ety.CACHE_DIR
        self._tmpdir = tempfile.mkdtemp()
        ety.CACHE_DIR = self._tmpdir

    def tearDown(self):
        ety.CACHE_DIR = self._orig_cache_dir
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    @patch("etymonline.fetch", return_value=HTML_WORD_PAGE)
    def test_loop_b_returns_seven_steps(self, _mock):
        steps, _ = ety.run_dkl_loop("robot", variant="b")
        self.assertEqual(len(steps), 7)

    @patch("etymonline.fetch", return_value=HTML_WORD_PAGE)
    def test_loop_a_returns_seven_steps(self, _mock):
        steps, _ = ety.run_dkl_loop("robot", variant="a")
        self.assertEqual(len(steps), 7)

    @patch("etymonline.fetch", return_value=HTML_WORD_PAGE)
    def test_loop_b_step3_is_leading(self, _mock):
        steps, _ = ety.run_dkl_loop("robot", variant="b")
        letter, name, root, body = steps[2]
        self.assertEqual(letter, "L")
        self.assertEqual(name, "LEADING")

    @patch("etymonline.fetch", return_value=HTML_WORD_PAGE)
    def test_loop_a_step3_is_equality(self, _mock):
        steps, _ = ety.run_dkl_loop("robot", variant="a")
        letter, name, root, body = steps[2]
        self.assertEqual(letter, "E")
        self.assertEqual(name, "EQUALITY")

    @patch("etymonline.fetch", return_value=HTML_WORD_PAGE)
    def test_loop_step1_depth_contains_etymology(self, _mock):
        steps, _ = ety.run_dkl_loop("robot", variant="b")
        _, _, _, body = steps[0]
        self.assertIn("Czech", body)

    @patch("etymonline.fetch", return_value=HTML_WORD_PAGE)
    def test_loop_a_equality_lists_distinct_senses(self, _mock):
        steps, _ = ety.run_dkl_loop("robot", variant="a")
        _, _, _, body = steps[2]
        # robot (n.) and robot (adj.) are two distinct senses — must not collapse
        self.assertIn("robot (n.)", body)
        self.assertIn("robot (adj.)", body)
        self.assertIn("not interchangeable", body)

    @patch("etymonline.fetch", return_value=HTML_WORD_PAGE)
    def test_loop_b_leading_lists_related(self, _mock):
        steps, _ = ety.run_dkl_loop("robot", variant="b")
        _, _, _, body = steps[2]
        # HTML_WORD_PAGE has links to automaton and android
        self.assertIn("automaton", body)

    @patch("etymonline.fetch", return_value=HTML_WORD_PAGE)
    def test_loop_step7_container_is_cache_path(self, _mock):
        steps, _ = ety.run_dkl_loop("robot", variant="b")
        _, _, _, body = steps[6]
        self.assertIn(self._tmpdir, body)

    @patch("etymonline.fetch", return_value=HTML_WORD_PAGE)
    def test_loop_json_output(self, _mock):
        steps, _ = ety.run_dkl_loop("robot", variant="b")
        data = [{"step": l, "name": n, "root": r, "body": b}
                for l, n, r, b in steps]
        parsed = json.loads(json.dumps(data, indent=2))
        self.assertEqual(len(parsed), 7)
        self.assertEqual(parsed[0]["step"], "D")


if __name__ == "__main__":
    unittest.main()
