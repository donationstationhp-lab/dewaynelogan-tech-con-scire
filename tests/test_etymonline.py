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

# Page without __NEXT_DATA__ — tests the HTML-scraping fallback
HTML_FALLBACK = """
<html><body>
  <section>
    <span class="word__name--XYZ">serendipity (n.)</span>
    <div class="word__deftext--ABC">1754, coined by Horace Walpole.</div>
  </section>
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


class TestParseHtmlFallback(unittest.TestCase):
    def test_fallback_entries(self):
        entries = ety._parse_html(HTML_FALLBACK)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["word"], "serendipity (n.)")
        self.assertIn("Walpole", entries[0]["etymology"])

    def test_parse_entries_prefers_next_data(self):
        # HTML_WORD_PAGE has __NEXT_DATA__ — should use it, not HTML fallback
        entries = ety.parse_entries(HTML_WORD_PAGE)
        self.assertEqual(entries[0]["word"], "robot (n.)")

    def test_parse_entries_falls_back_to_html(self):
        entries = ety.parse_entries(HTML_FALLBACK)
        self.assertEqual(entries[0]["word"], "serendipity (n.)")


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
    def test_explore_includes_root_and_related(self, _mock_fetch):
        explored = ety.explore("robot", depth=1)
        self.assertIn("robot", explored)
        # Should have fetched some related entries too
        self.assertGreater(len(explored), 1)

    @patch("etymonline.fetch", return_value=HTML_WORD_PAGE)
    def test_explore_depth_zero_only_root(self, mock_fetch):
        explored = ety.explore("robot", depth=0)
        self.assertEqual(list(explored.keys()), ["robot"])
        mock_fetch.assert_called_once()


if __name__ == "__main__":
    unittest.main()
