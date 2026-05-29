"""Unit tests for suprememath.lexicon"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from suprememath.lexicon import Lexicon

_REAL_LEXICON = Path(__file__).parent.parent / "data" / "sm_lexicon.json"


class TestLexiconFromFile(unittest.TestCase):
    def setUp(self):
        self.lex = Lexicon(_REAL_LEXICON)

    def test_all_ten_positions_present(self):
        for n in range(10):
            entry = self.lex.get(n)
            self.assertIn("name", entry)

    def test_name_returns_string(self):
        self.assertEqual(self.lex.name(1), "Knowledge")
        self.assertEqual(self.lex.name(0), "Cipher")
        self.assertEqual(self.lex.name(9), "Born")

    def test_pie_root_is_string(self):
        for n in range(10):
            self.assertIsInstance(self.lex.pie_root(n), str)

    def test_instruction_is_non_empty(self):
        for n in range(10):
            self.assertTrue(self.lex.instruction(n))

    def test_key_words_is_list(self):
        for n in range(10):
            kw = self.lex.key_words(n)
            self.assertIsInstance(kw, list)
            self.assertGreater(len(kw), 0)

    def test_labels_present(self):
        self.assertTrue(self.lex.label_attention)
        self.assertTrue(self.lex.label_intention)
        self.assertTrue(self.lex.label_purpose)
        self.assertTrue(self.lex.label_cipher)

    def test_positions_property(self):
        pos = self.lex.positions
        self.assertEqual(len(pos), 10)
        self.assertIn(7, pos)

    def test_missing_position_raises(self):
        with self.assertRaises(KeyError):
            self.lex.get(10)

    def test_get_returns_copy(self):
        # Mutating the returned dict should not affect the lexicon
        entry = self.lex.get(1)
        entry["name"] = "MUTATED"
        self.assertEqual(self.lex.name(1), "Knowledge")


class TestLexiconCustomData(unittest.TestCase):
    """Verify Lexicon works with arbitrary JSON (not just the real file)."""

    def _make_minimal_lexicon(self, extra_labels=None):
        data = {
            "positions": {
                str(n): {
                    "name": f"Name{n}",
                    "key_words": [f"word{n}"],
                    "instruction": f"Instruction {n}",
                    "pie_root": f"*root{n}-",
                }
                for n in range(10)
            },
            "reading_labels": extra_labels or {
                "attention": "Attention",
                "intention": "Intention",
                "purpose": "Purpose",
                "cipher": "Cipher",
            },
        }
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        json.dump(data, tmp)
        tmp.close()
        return tmp.name

    def test_custom_names_loaded(self):
        path = self._make_minimal_lexicon()
        try:
            lex = Lexicon(path)
            self.assertEqual(lex.name(5), "Name5")
        finally:
            os.unlink(path)

    def test_custom_labels(self):
        path = self._make_minimal_lexicon({"attention": "Focus", "intention": "Direction",
                                           "purpose": "Why", "cipher": "Vibration"})
        try:
            lex = Lexicon(path)
            self.assertEqual(lex.label_attention, "Focus")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
