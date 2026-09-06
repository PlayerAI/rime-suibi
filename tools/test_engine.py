#!/usr/bin/env python3
"""Run end-to-end key events against an isolated real librime. GPL-3.0-only."""
import argparse
import json
import platform
import re
import shutil
import statistics
import tempfile
import time
from pathlib import Path

from rime_api import Rime

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--plugin", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    build = ROOT / ".build"
    build.mkdir(exist_ok=True)
    user = Path(tempfile.mkdtemp(prefix="engine-", dir=build)).resolve()
    for path in ROOT.glob("suibi*.yaml"):
        shutil.copyfile(path, user / path.name)
        if path.name.endswith(".schema.yaml"):
            baseline = re.sub(r"^\s*- lua_(?:processor|segmentor|translator|filter)@.*\n", "", path.read_text(encoding="utf-8"), flags=re.M)
            baseline = re.sub(r"(schema_id: suibi_\w+)", r"\1_baseline", baseline)
            (user / path.name.replace(".schema.yaml", "_baseline.schema.yaml")).write_text(baseline, encoding="utf-8")
    for directory in ("cn_dicts", "lua"):
        shutil.copytree(ROOT / directory, user / directory)
    (user / "default.yaml").write_text("config_version: '0.1'\nschema_list:\n  - schema: suibi_pinyin\n  - schema: suibi_double_pinyin\n", encoding="utf-8")
    rime = Rime(args.library, args.plugin)
    rime.initialize(user)
    deployment = time.perf_counter()
    for name in ("suibi_pinyin", "suibi_double_pinyin", "suibi_mspy"):
        rime.deploy(user / f"{name}.schema.yaml")
        rime.deploy(user / f"{name}_baseline.schema.yaml")
    deployment = time.perf_counter() - deployment
    passed, samples = [], []
    try:
        for schema, normal, sound in [("suibi_pinyin", "zhongguo", "zhong"), ("suibi_double_pinyin", "vsgo", "vs"), ("suibi_mspy", "vsgo", "vs")]:
            ordinary_queries = (["zhongguo", "nihao", "zhongwenshurufa", "womenxuexizhongwen", "shi", "n"]
                                if schema == "suibi_pinyin" else ["vsgo", "nihk", "vswfuurufa", "womfxtextvswf", "ui", "ni"])
            references = {}
            rime.select(schema + "_baseline")
            for query in ordinary_queries:
                rime.clear()
                rime.type(query)
                references[query] = [t for t, c in rime.candidates(20)]
            rime.select(schema)
            for query in ordinary_queries:
                rime.clear()
                rime.type(query)
                assert [t for t, c in rime.candidates(20)] == references[query], (schema, query)
            passed.append(schema + ": ordinary candidates equal unmodified Rime pipeline")
            rime.clear()
            rime.type(normal)
            assert "中国" in [t for t, _ in rime.candidates(30)], (schema, rime.input(), rime.candidates(10))
            rime.key(32)
            assert rime.commit() == "中国", schema
            passed.append(schema + ": normal phrase + Space commit")

            rime.type(sound + "`phh")
            candidates = rime.candidates()
            assert "钟" in [t for t, _ in candidates], (schema, rime.input(), candidates)
            assert all(len(t) == 1 and " · phh" in c for t, c in candidates), candidates
            assert "中" not in [t for t, _ in candidates] and "鐘" not in [t for t, _ in candidates]
            passed.append(schema + ": hard stroke filter + simplified only")
            rime.key(0xff0d)
            assert rime.commit() == candidates[0][0] and rime.input() == ""
            passed.append(schema + ": Return confirms auxiliary candidate")

            rime.type(sound + "`")
            candidates = rime.candidates()
            assert len(candidates) > 5
            rime.key(ord("2"))
            assert rime.commit() == candidates[1][0]
            rime.type(sound + "`")
            rime.key(ord("="))
            rime.key(ord("1"))
            assert rime.commit() == candidates[5][0]
            rime.type(sound + "`phhhzszhs")
            assert "钟" in [t for t, c in rime.candidates()]
            rime.key(0xffe1)
            rime.key(0xffe1, 1 << 30)
            assert not rime.commit() and rime.input() == sound + "`phhhzszhs"
            selected = rime.candidates()[0][0]
            rime.key(32)
            assert rime.commit() == selected
            passed.append(schema + ": digit selection, paging, long prefixes, Shift safety, Space")

            rime.type(sound + "`phh")
            rime.key(ord("a"))
            assert rime.input() == sound + "`phh", rime.input()
            rime.key(0xff51)
            rime.key(0xff08)
            assert rime.input() == sound + "`ph", rime.input()
            for _ in range(3):
                rime.key(0xff08)
            assert rime.input() == sound, rime.input()
            assert "中" in [t for t, _ in rime.candidates(30)]
            passed.append(schema + ": invalid stroke ignored; BackSpace restores normal sound")

            rime.clear()
            rime.type(sound + "`zzzzzzzzzz")
            assert not rime.candidates(), rime.candidates()
            for key in [32, 49, 0xff0d]:
                rime.key(key)
                assert not rime.commit(), "No-match input leaked to application"
            rime.key(0xff1b)
            assert rime.input() == ""
            passed.append(schema + ": no-match does not commit raw code; Escape cancels")

            rime.type(normal)
            rime.key(96)
            assert rime.input() == normal, rime.input()
            rime.clear()
            rime.key(96)
            assert rime.input() == "`" and not rime.commit() and not rime.candidates()
            rime.key(96)
            assert not rime.input() and rime.commit() == "`", "Repeated standalone backticks must work"
            rime.type("`szhs")
            rows = rime.candidates()
            assert any(t == "中" and "zhong" in c for t, c in rows), rows
            rime.key(0xff0d)
            assert rime.commit() == rows[0][0]
            rime.type("`zzzzzzzzzz")
            assert not rime.candidates()
            rime.key(32)
            assert not rime.commit()
            rime.key(0xff1b)
            if schema == "suibi_mspy":
                rime.type("y;`n")
                assert "应" in [t for t, c in rime.candidates()]
                rime.clear()
            passed.append(schema + ": stroke reverse lookup, pinyin comments, literal backtick, no-match safety")

            rime.set_option("ascii_mode", True)
            assert not rime.key(ord("a"))
            rime.set_option("ascii_mode", False)
            passed.append(schema + ": ASCII mode passes through")

            for query in [sound, sound + "`p", sound + "`ph", sound + "`phh"] * 10:
                rime.clear()
                start = time.perf_counter()
                rime.type(query)
                rime.candidates(5)
                samples.append((time.perf_counter() - start) * 1000)
            rime.clear()
        # Full-pinyin spelling aliases and polyphonic characters.
        rime.select("suibi_pinyin")
        for sound, char in [("zhong", "重"), ("chong", "重"), ("lv", "吕"), ("nue", "虐")]:
            rime.clear()
            rime.type(sound + "`")
            assert char in [t for t, _ in rime.candidates()], (sound, rime.candidates())
        passed.append("polyphonic readings and full-pinyin aliases")
        result = {"status": "passed", "platform": platform.platform(), "rime_version": rime.version(),
                  "tests": passed, "test_count": len(passed), "deployment_seconds": round(deployment, 3),
                  "query_latency_ms": {"median": round(statistics.median(samples), 3),
                                       "p95": round(sorted(samples)[int(len(samples) * .95) - 1], 3),
                                       "note": "Warm sessions, entire short query + first page; not GUI latency"},
                  "sandbox": str(user)}
        output = args.output or build / "engine-results.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        rime.close()


if __name__ == "__main__":
    main()
