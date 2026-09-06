#!/usr/bin/env python3
"""Create a source-inclusive cross-platform Suibi ZIP. SPDX-License-Identifier: GPL-3.0-only"""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.2.0"


def main():
    files = [p for p in ROOT.iterdir() if p.is_file() and (p.suffix in (".yaml", ".md", ".txt") or p.name == "LICENSE")]
    for directory in ("cn_dicts", "lua", "data", "docs", "tools", "tests", "LICENSES", ".github"):
        files.extend(p for p in (ROOT / directory).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    dest = ROOT / "dist"
    dest.mkdir(exist_ok=True)
    sums = []
    for scheme in ("suibi_pinyin", "suibi_double_pinyin", "suibi_mspy"):
        label = {"suibi_pinyin": "pinyin", "suibi_double_pinyin": "double-pinyin", "suibi_mspy": "mspy"}[scheme]
        stem = f"rime-suibi-{label}-{VERSION}"
        archive = dest / f"{stem}.zip"
        selected = [p for p in files if not p.name.endswith(".schema.yaml") or p.name == scheme + ".schema.yaml"]
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as stream:
            payloads = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in selected}
            payloads["package.json"] = (json.dumps({"version": VERSION, "scheme": scheme}, indent=2) + "\n").encode()
            for relative, payload in sorted(payloads.items()):
                info = zipfile.ZipInfo(f"{stem}/{relative}", date_time=(2026, 9, 6, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                stream.writestr(info, payload)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        sums.append(f"{digest}  {archive.name}\n")
        print(json.dumps({"archive": str(archive), "files": len(payloads), "bytes": archive.stat().st_size, "sha256": digest}, indent=2))
    (dest / "SHA256SUMS").write_text("".join(sums), encoding="utf-8")


if __name__ == "__main__":
    main()
