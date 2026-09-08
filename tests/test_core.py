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

    def test_word_syntax_readings_and_boundaries(self):
        for mode, sound in [("pinyin", "jilu"), ("double_pinyin", "jilu"),
                            ("mspy", "jilu"), ("pinyin", "xi'an"),
                            ("pinyin", "zhongguoren"), ("mspy", "y;gl")]:
            self.assertEqual((sound, "n"), self.core.parse(sound + "`n", mode))
        for mode, sound in [("pinyin", "zhg"), ("pinyin", "zhongg"),
                            ("double_pinyin", "vsg"), ("mspy", "y;g"),
                            ("pinyin", "'jilu"), ("pinyin", "ji''lu"),
                            ("pinyin", "jilu'")]:
            self.assertIsNone(self.core.parse(sound + "`n", mode), (mode, sound))
        for text, sound, mode, preedit in [
                ("记录", "jilu", "pinyin", "ji lu"), ("纪录", "jilu", "mspy", "ji lu"),
                ("西安", "xi'an", "pinyin", "xi an"), ("虐待", "nuedai", "pinyin", "nue dai"),
                ("应该", "y;gl", "mspy", "y; gl"), ("中国人", "vsgorf", "double_pinyin", "vs go rf"),
                ("般若", "bore", "pinyin", "bo re"), ("六安", "luan", "pinyin", "lu an")]:
            self.assertTrue(self.core.matches_word(text, sound, mode, preedit), (text, sound, mode))
        for text, sound, preedit in [("记录", "jl", "j l"), ("记录", "jil", "ji l"),
                                     ("记录仪", "jilu", "ji lu"), ("记", "jilu", "ji lu"),
                                     ("记录", "ji'lu'", "ji lu"), ("西安", "x'ian", "x ian")]:
            self.assertFalse(self.core.matches_word(text, sound, "pinyin", preedit), (text, sound))
        self.assertNotEqual(self.core.first_strokes("记录"), self.core.first_strokes("纪录"))
        self.assertEqual(self.core.first_strokes("权利"), self.core.first_strokes("权力"))

    def test_sampled_dictionary_words_in_all_modes(self):
        rules = {mode: json.loads((ROOT / "data" / name).read_text()) for mode, name in [
            ("double_pinyin", "natural_double_pinyin.json"), ("mspy", "microsoft_double_pinyin.json")]}
        for index, (word, pinyin, _) in enumerate(build.dictionary_rows(ROOT / "cn_dicts/suibi_words.dict.yaml")):
            if index % 997:
                continue
            spellings = {"pinyin": pinyin.split()}
            for mode, algebra in rules.items():
                spellings[mode] = [next(code for code in build.double_codes(py, algebra) if len(code) == 2)
                                   for py in pinyin.split()]
            for mode, codes in spellings.items():
                sound = "".join(codes)
                self.assertTrue(self.core.valid_sound(sound, mode), (word, sound, mode))
                self.assertTrue(self.core.matches_word(word, sound, mode, " ".join(codes)), (word, sound, mode))
            self.assertEqual(self.strokes[word[0]], self.core.first_strokes(word))

    def test_syntax_and_aliases(self):
        self.assertEqual(("zhong", "phh"), self.core.parse("zhong`phh", "pinyin"))
        self.assertEqual(("vs", "phh"), self.core.parse("vs`phh", "double_pinyin"))
        for code in ["zhongg`ph", "zhong`a", "zhong``p", "Zhong`p"]:
            self.assertIsNone(self.core.parse(code, "pinyin"), code)
        self.assertEqual({r["text"] for r in self.lookup("nue", "", "pinyin")},
                         {r["text"] for r in self.lookup("nve", "", "pinyin")})
        self.assertEqual([], self.lookup("zhong", "xxx", "pinyin"))
        self.assertEqual([], self.lookup("zzzz", "", "pinyin"))


if __name__ == "__main__":
    unittest.main()
