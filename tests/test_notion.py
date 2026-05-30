"""Unit tests for notion.py

Run with:
  pytest tests/
"""

import datetime
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import notion


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_response(status_code=200, json_body=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body or {"object": "page", "id": "fake-id"}
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        import requests
        resp.raise_for_status.side_effect = requests.HTTPError(response=resp)
    return resp


# ── Tests: get_credentials ────────────────────────────────────────────────────

class TestGetCredentials(unittest.TestCase):
    def test_reads_env_vars(self):
        with patch.dict(os.environ, {"NOTION_TOKEN": "tok", "NOTION_DATABASE_ID": "db"}):
            token, db_id = notion.get_credentials()
        self.assertEqual(token, "tok")
        self.assertEqual(db_id, "db")

    def test_raises_when_token_missing(self):
        env = {"NOTION_DATABASE_ID": "db"}
        with patch.dict(os.environ, env, clear=True):
            os.environ.pop("NOTION_TOKEN", None)
            with self.assertRaises(EnvironmentError) as ctx:
                notion.get_credentials()
        self.assertIn("NOTION_TOKEN", str(ctx.exception))

    def test_raises_when_db_id_missing(self):
        env = {"NOTION_TOKEN": "tok"}
        with patch.dict(os.environ, env, clear=True):
            os.environ.pop("NOTION_DATABASE_ID", None)
            with self.assertRaises(EnvironmentError) as ctx:
                notion.get_credentials()
        self.assertIn("NOTION_DATABASE_ID", str(ctx.exception))


# ── Tests: save_entry ─────────────────────────────────────────────────────────

class TestSaveEntry(unittest.TestCase):
    @patch("notion.requests.post")
    def test_posts_to_notion_pages_endpoint(self, mock_post):
        mock_post.return_value = _mock_response()
        notion.save_entry("robot", "1923, from Czech robota",
                          related=["automaton", "android"],
                          token="tok", database_id="db123")
        mock_post.assert_called_once()
        url, = mock_post.call_args.args
        self.assertIn("/pages", url)

    @patch("notion.requests.post")
    def test_payload_structure(self, mock_post):
        mock_post.return_value = _mock_response()
        notion.save_entry("galaxy", "late 14c., from Greek",
                          related=["nebula"],
                          token="tok", database_id="db")

        payload = mock_post.call_args.kwargs["json"]
        props = payload["properties"]

        self.assertEqual(props["Word"]["title"][0]["text"]["content"], "galaxy")
        self.assertIn("Greek", props["Etymology"]["rich_text"][0]["text"]["content"])
        self.assertIn("nebula", props["Related Words"]["rich_text"][0]["text"]["content"])
        # Date Looked Up should be today's ISO date
        today = datetime.date.today().isoformat()
        self.assertEqual(props["Date Looked Up"]["date"]["start"], today)

    @patch("notion.requests.post")
    def test_related_capped_at_ten(self, mock_post):
        mock_post.return_value = _mock_response()
        many = [f"word{i}" for i in range(20)]
        notion.save_entry("test", "etym", related=many,
                          token="tok", database_id="db")

        payload = mock_post.call_args.kwargs["json"]
        related_val = payload["properties"]["Related Words"]["rich_text"][0]["text"]["content"]
        self.assertEqual(related_val.count(","), 9)  # 10 items → 9 commas

    @patch("notion.requests.post")
    def test_etymology_truncated_to_2000_chars(self, mock_post):
        mock_post.return_value = _mock_response()
        long_etym = "x" * 3000
        notion.save_entry("word", long_etym, token="tok", database_id="db")

        payload = mock_post.call_args.kwargs["json"]
        etym_val = payload["properties"]["Etymology"]["rich_text"][0]["text"]["content"]
        self.assertLessEqual(len(etym_val), 2000)

    @patch("notion.requests.post")
    def test_notion_version_header_set(self, mock_post):
        mock_post.return_value = _mock_response()
        notion.save_entry("foo", "bar", token="tok", database_id="db")
        headers = mock_post.call_args.kwargs["headers"]
        self.assertIn("Notion-Version", headers)

    @patch("notion.requests.post")
    def test_uses_env_credentials_when_not_passed(self, mock_post):
        mock_post.return_value = _mock_response()
        with patch.dict(os.environ, {"NOTION_TOKEN": "env_tok",
                                     "NOTION_DATABASE_ID": "env_db"}):
            notion.save_entry("foo", "bar")
        headers = mock_post.call_args.kwargs["headers"]
        self.assertIn("env_tok", headers["Authorization"])

    @patch("notion.requests.post")
    def test_http_error_propagates(self, mock_post):
        mock_post.return_value = _mock_response(status_code=401)
        import requests as req
        with self.assertRaises(req.HTTPError):
            notion.save_entry("foo", "bar", token="bad", database_id="db")


# ── Tests: save_entries ───────────────────────────────────────────────────────

class TestSaveEntries(unittest.TestCase):
    @patch("notion.requests.post")
    def test_saves_all_valid_entries(self, mock_post):
        mock_post.return_value = _mock_response()
        entries = [
            {"word": "galaxy", "etymology": "from Greek"},
            {"word": "nebula", "etymology": "from Latin"},
        ]
        count = notion.save_entries(entries, token="tok", database_id="db")
        self.assertEqual(count, 2)
        self.assertEqual(mock_post.call_count, 2)

    @patch("notion.requests.post")
    def test_skips_entries_without_word(self, mock_post):
        mock_post.return_value = _mock_response()
        entries = [
            {"word": "", "etymology": "something"},
            {"etymology": "no word key"},
            {"word": "valid", "etymology": "ok"},
        ]
        count = notion.save_entries(entries, token="tok", database_id="db")
        self.assertEqual(count, 1)
        mock_post.assert_called_once()

    @patch("notion.requests.post")
    def test_empty_list_returns_zero(self, mock_post):
        mock_post.return_value = _mock_response()
        count = notion.save_entries([], token="tok", database_id="db")
        self.assertEqual(count, 0)
        mock_post.assert_not_called()

    @patch("notion.requests.post")
    def test_missing_etymology_is_fine(self, mock_post):
        mock_post.return_value = _mock_response()
        entries = [{"word": "foo"}]
        count = notion.save_entries(entries, token="tok", database_id="db")
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
