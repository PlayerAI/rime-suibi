"""Check Lua lookup against an independent candidate-set reference. GPL-3.0-only."""
import json
import sys
import unittest
from collections import defaultdict
from pathlib import Path

from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lua = LuaRuntime(unpack_returned_tuples=True)
        cls.lua.globals().package.path = (ROOT / "lua/?.lua").as_posix() + ";" + cls.lua.globals().package.path
        cls.core = cls.lua.eval("(require('suibi.core'))")
        cls.strokes, cls.entries = build.load_characters()
        cls.by_py = defaultdict(dict)
        for (char, py), weight in cls.entries.items():
            cls.by_py[py][char] = cls.strokes[char]
        rules = json.loads((ROOT / "data/natural_double_pinyin.json").read_text(encoding="utf-8"))
        cls.by_code = defaultdict(dict)
        for py, chars in cls.by_py.items():
            for code in build.double_codes(py, rules):
                if len(code) == 2:
                    cls.by_code[code].update(chars)

    def lookup(self, sound, prefix, mode):
        result = self.core.lookup(sound, prefix, mode)
        return [result[i] for i in range(1, len(result) + 1)]

    def test_all_character_prefixes_in_both_modes(self):
        # All distinct queries from all characters, 0..5 strokes. Catches
        # truncation, polyphonic omissions, aliases, duplicates and short words.
        for mode, groups in [("pinyin", self.by_py), ("double_pinyin", self.by_code)]:
            for sound, chars in groups.items():
                prefixes = {stroke[:n] for stroke in chars.values() for n in range(6)}
                for prefix in prefixes:
                    expected = {c for c, s in chars.items() if s.startswith(prefix)}
                    actual = self.lookup(sound, prefix, mode)
                    self.assertEqual(expected, {r["text"] for r in actual}, (mode, sound, prefix))
                    self.assertEqual(len(expected), len(actual), "Duplicate character")
                    self.assertEqual([r["weight"] for r in actual], sorted([r["weight"] for r in actual], reverse=True))

    def test_reverse_lookup_all_full_strokes_and_common_prefixes(self):
        self.assertEqual(("", "szhs"), self.core.parse("`szhs", "pinyin"))
        self.assertEqual([], self.lookup("", "", "pinyin"))
        for prefix in set(self.strokes.values()) | {"h", "s", "p", "n", "z", "szhs"}:
            expected = {c for c, stroke in self.strokes.items() if stroke.startswith(prefix)}
            rows = self.lookup("", prefix, "pinyin")
            self.assertEqual(expected, {r["text"] for r in rows})
            self.assertEqual(len(expected), len(rows))
        rows = self.lookup("", self.strokes["重"], "pinyin")
        reading = next(r["pinyin"] for r in rows if r["text"] == "重")
        self.assertIn("zhong", reading)
        self.assertIn("chong", reading)

    def test_microsoft_mapping_all_prefixes(self):
        rules = json.loads((ROOT / "data/microsoft_double_pinyin.json").read_text(encoding="utf-8"))
        groups = defaultdict(dict)
        for py, chars in self.by_py.items():
            for code in build.double_codes(py, rules):
                if len(code) == 2:
                    groups[code].update(chars)
        self.assertIn("应", groups["y;"])
        for sound, chars in groups.items():
            for prefix in {stroke[:n] for stroke in chars.values() for n in range(6)}:
                expected = {c for c, stroke in chars.items() if stroke.startswith(prefix)}
                rows = self.lookup(sound, prefix, "mspy")
                self.assertEqual(expected, {r["text"] for r in rows}, (sound, prefix))
                self.assertEqual(len(expected), len(rows))

    def test_simplified_and_shared_characters(self):
        for text in ["中国", "乾坤", "你好，OpenAI！", "𬭸"]:
            self.assertTrue(self.core.is_simplified(text), text)
        for text in ["中國", "鐘", "你好國", "㐀", "𠮷"]:
            self.assertFalse(self.core.is_simplified(text), text)

    def test_syntax_and_aliases(self):
        self.assertEqual(("zhong", "phh"), self.core.parse("zhong`phh", "pinyin"))
        self.assertEqual(("vs", "phh"), self.core.parse("vs`phh", "double_pinyin"))
        for code in ["zhongguo`ph", "zhong`a", "zhong``p", "Zhong`p"]:
            self.assertIsNone(self.core.parse(code, "pinyin"), code)
        self.assertEqual({r["text"] for r in self.lookup("nue", "", "pinyin")},
                         {r["text"] for r in self.lookup("nve", "", "pinyin")})
        self.assertEqual([], self.lookup("zhong", "xxx", "pinyin"))
        self.assertEqual([], self.lookup("zzzz", "", "pinyin"))


if __name__ == "__main__":
    unittest.main()
