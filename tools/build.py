#!/usr/bin/env python3
"""Build checked-in Rime files from pinned data. SPDX-License-Identifier: GPL-3.0-only"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import urllib.request
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.2.0"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dictionary_rows(path: Path):
    active = False
    with path.open(encoding="utf-8-sig") as stream:
        for line in stream:
            line = line.rstrip("\r\n")
            if line == "...":
                active = True
                continue
            if not active or not line or line.startswith("#"):
                continue
            cells = line.split("\t")
            if len(cells) != 3:
                raise ValueError(f"Invalid dictionary row: {path}: {line!r}")
            word, pinyin, weight = cells
            if not re.fullmatch(r"[a-z]+(?: [a-z]+)*", pinyin):
                raise ValueError(f"Invalid reading: {pinyin!r}")
            yield word, pinyin, int(weight)


def double_codes(pinyin: str, rules: list[str]) -> list[str]:
    states = [pinyin]
    for rule in rules:
        kind, *parts = rule.split("/")
        if kind == "erase":
            states = [s for s in states if not re.search(parts[0], s)]
        elif kind in ("derive", "xform"):
            pattern, replacement = parts[:2]
            replacement = re.sub(r"\$(\d)", r"\\g<\1>", replacement)
            changed = [re.sub(pattern, replacement, s) for s in states]
            states = states + changed if kind == "derive" else changed
        elif kind == "xlit":
            states = [s.translate(str.maketrans(parts[0], parts[1])) for s in states]
        else:
            raise ValueError(f"Unsupported algebra operation: {rule}")
        states = list(dict.fromkeys(states))
    return states


def load_characters():
    with (ROOT / "data/sources/strokes.tsv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if len(rows) != 8105 or {int(r["index"]) for r in rows} != set(range(1, 8106)):
        raise ValueError("The official stroke source must have exactly 8105 indexed characters")
    strokes = {}
    for row in rows:
        if len(row["character"]) != 1 or not re.fullmatch("[12345]+", row["digits"]):
            raise ValueError(f"Invalid stroke row: {row}")
        strokes[row["character"]] = row["digits"].translate(str.maketrans("12345", "hspnz"))
    if len(strokes) != 8105:
        raise ValueError("Duplicate stroke characters")
    entries = {}
    for char, py, weight in dictionary_rows(ROOT / "data/sources/rime_ice_chars.dict.yaml"):
        if char in strokes:
            entries[(char, py)] = max(weight, entries.get((char, py), 0))
    return strokes, entries


def schema(mode: str, rules: list[str]) -> dict:
    double = mode != "pinyin"
    schema_id = "suibi_" + mode
    algebra = rules if double else [
        "erase/^xx$/", "derive/^([jqxy])u$/$1v/", "derive/^([nl])ve$/$1ue/",
        "abbrev/^([a-z]).+$/$1/",
    ]
    return {
        "schema": {"schema_id": schema_id, "name": {"pinyin": "随笔全拼", "double_pinyin": "随笔双拼（自然码）", "mspy": "随笔微软双拼"}[mode],
                   "version": VERSION, "author": ["Suibi contributors"],
                   "description": "简体拼音输入，反引号后按 h/s/p/n/z 补充单字笔画。"},
        "switches": [{"name": "ascii_mode", "reset": 0, "states": ["中文", "西文"]}],
        "engine": {
            "processors": ["lua_processor@*suibi.processor", "ascii_composer", "recognizer",
                           "key_binder", "speller", "punctuator", "selector", "navigator", "express_editor"],
            "segmentors": ["ascii_segmentor", "lua_segmentor@*suibi.segmentor", "matcher",
                           "abc_segmentor", "punct_segmentor", "fallback_segmentor"],
            "translators": ["lua_translator@*suibi.translator", "punct_translator", "script_translator"],
            "filters": ["lua_filter@*suibi.filter", "uniquifier"],
        },
        "suibi": {"mode": mode},
        "menu": {"page_size": 5},
        "speller": {"alphabet": "abcdefghijklmnopqrstuvwxyz`" + (";" if mode == "mspy" else ""), "initials": "abcdefghijklmnopqrstuvwxyz",
                    "delimiter": " '", "algebra": algebra},
        "translator": {"dictionary": "suibi", "prism": schema_id, "user_dict": "suibi",
                       "enable_user_dict": True, "enable_sentence": True,
                       "enable_completion": True, "spelling_hints": 0},
        "ascii_composer": {"good_old_caps_lock": True,
                           "switch_key": {"Shift_L": "commit_code", "Shift_R": "commit_code",
                                          "Control_L": "noop", "Control_R": "noop"}},
        "key_binder": {"bindings": [
            {"when": "has_menu", "accept": "minus", "send": "Page_Up"},
            {"when": "has_menu", "accept": "equal", "send": "Page_Down"},
        ]},
        "recognizer": {"patterns": {"email": "^[A-Za-z][-_.0-9A-Za-z]*@.*$",
                                     "url": "^(www[.]|https?:|ftp:|mailto:).*$"}},
        "punctuator": {"half_shape": {",": "，", ".": "。", "?": "？", "!": "！", ":": "：",
                                     ";": "；", "(": "（", ")": "）", "[": "【", "]": "】",
                                     '"': {"pair": ["“", "”"]}, "'": {"pair": ["‘", "’"]},
                                     "<": "《", ">": "》", "\\": "、", "`": "`"}},
    }


def make_files(fetch: bool = False) -> tuple[dict[str, str], dict]:
    manifest = json.loads((ROOT / "data/sources.json").read_text(encoding="utf-8"))
    for entry in manifest["inputs"]:
        if sha256(ROOT / entry["path"]) != entry["sha256"]:
            raise ValueError(f"Source hash mismatch: {entry['path']}")
    base = ROOT / ".cache/upstream/base.dict.yaml"
    if not base.exists():
        if not fetch:
            raise FileNotFoundError("Base dictionary cache missing. Run: python tools/build.py --fetch")
        base.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(manifest["base_dictionary"]["url"], headers={"User-Agent": "rime-suibi-build"})
        payload = urllib.request.urlopen(request, timeout=90).read()
        if hashlib.sha256(payload).hexdigest() != manifest["base_dictionary"]["sha256"]:
            raise ValueError("Downloaded base dictionary hash mismatch")
        base.write_bytes(payload)
    if sha256(base) != manifest["base_dictionary"]["sha256"]:
        raise ValueError("Cached base dictionary hash mismatch")
    strokes, entries = load_characters()
    rules = json.loads((ROOT / "data/natural_double_pinyin.json").read_text(encoding="utf-8"))
    by_py = defaultdict(list)
    for (char, py), weight in sorted(entries.items()):
        by_py[py].append([char, strokes[char], weight])
    by_code = defaultdict(set)
    for py in sorted(by_py):
        for code in double_codes(py, rules):
            if re.fullmatch("[a-z]{2}", code):
                by_code[code].add(py)
    if "zhong" not in by_code["vs"] or "guo" not in by_code["go"]:
        raise ValueError("Natural-code mapping verification failed")
    q = lambda s: json.dumps(s, ensure_ascii=False)
    lua = ["-- GENERATED by tools/build.py; do not edit. SPDX-License-Identifier: GPL-3.0-only",
           "local data = { pinyin = {}, double_pinyin = {}, mspy = {}, reverse = {}, allowed = {} }"]
    for py, rows in sorted(by_py.items()):
        values = ["{" + ",".join([q(c), q(s), str(w)]) + "}" for c, s, w in sorted(rows, key=lambda r: (-r[2], r[0]))]
        lua.append(f"data.pinyin[{q(py)}] = {{" + ",".join(values) + "}")
    for code, pys in sorted(by_code.items()):
        lua.append(f"data.double_pinyin[{q(code)}] = {{" + ",".join(q(p) for p in sorted(pys)) + "}")
    ms_rules = json.loads((ROOT / "data/microsoft_double_pinyin.json").read_text(encoding="utf-8"))
    ms_codes = defaultdict(set)
    for py in sorted(by_py):
        for code in double_codes(py, ms_rules):
            if re.fullmatch("[a-z;]{2}", code):
                ms_codes[code].add(py)
    for code, pys in sorted(ms_codes.items()):
        lua.append(f"data.mspy[{q(code)}] = {{" + ",".join(q(p) for p in sorted(pys)) + "}")
    reverse_readings = defaultdict(list)
    for char, py in entries:
        reverse_readings[char].append(py)
    for char in sorted(strokes):
        readings = sorted(reverse_readings[char])
        weight = max((entries[(char, py)] for py in readings), default=0)
        lua.append("data.reverse[#data.reverse + 1] = {" + ",".join([q(char), q(strokes[char]), str(weight), q(" / ".join(readings) or "读音未收录")]) + "}")
        lua.append(f"data.allowed[{q(char)}] = true")
    lua.append("return data")
    files = {"lua/suibi/data.lua": "\n".join(lua) + "\n"}
    header = "# GENERATED by tools/build.py; do not edit.\n# GPL-3.0; derived from iDvel/rime-ice. See NOTICE.md.\n"
    for mode in ["pinyin", "double_pinyin", "mspy"]:
        obj = schema(mode, ms_rules if mode == "mspy" else rules)
        files[obj["schema"]["schema_id"] + ".schema.yaml"] = header + yaml.safe_dump(obj, allow_unicode=True, sort_keys=False, width=120)
    def dict_header(name: str):
        return header + f"---\nname: {name}\nversion: '{VERSION}'\nsort: by_weight\n...\n"
    files["suibi.dict.yaml"] = header + f"---\nname: suibi\nversion: '{VERSION}'\nsort: by_weight\nimport_tables:\n  - cn_dicts/suibi_chars\n  - cn_dicts/suibi_words\n...\n"
    files["cn_dicts/suibi_chars.dict.yaml"] = dict_header("suibi_chars") + "".join(
        f"{char}\t{py}\t{weight}\n" for (char, py), weight in sorted(entries.items(), key=lambda e: (e[0][1], -e[1], e[0][0])))
    words, dropped = [], 0
    known_py = set(by_py)
    for word, py, weight in dictionary_rows(base):
        if len(word) >= 2 and all(c in strokes for c in word) and all(p in known_py for p in py.split()):
            words.append(f"{word}\t{py}\t{weight}\n")
        else:
            dropped += 1
    files["cn_dicts/suibi_words.dict.yaml"] = dict_header("suibi_words") + "".join(words)
    stats = {"version": VERSION, "allowed_characters": len(strokes), "characters_with_readings": len({c for c, p in entries}),
             "character_readings": len(entries), "pinyin_syllables": len(by_py), "double_pinyin_codes": len(by_code),
             "words": len(words), "excluded_upstream_words": dropped,
             "missing_readings": sorted(set(strokes) - {c for c, p in entries})}
    files["data/build_stats.json"] = json.dumps(stats, ensure_ascii=False, indent=2) + "\n"
    return files, stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Fetch pinned upstream dictionary when absent")
    parser.add_argument("--check", action="store_true", help="Verify generated files without modifying them")
    args = parser.parse_args()
    files, stats = make_files(args.fetch)
    changed = []
    for name, content in files.items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_bytes() != content.encode("utf-8"):
                changed.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode("utf-8"))
    if changed:
        raise SystemExit("Generated files differ: " + ", ".join(changed))
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
