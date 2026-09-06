#!/usr/bin/env python3
"""Fetch a pinned, Lua-enabled librime for tests; no system installation. GPL-3.0-only."""
import hashlib
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "rime-33e7814-Windows-msvc-x64.7z"
URL = "https://github.com/rime/librime/releases/download/1.17.0/" + NAME
SHA256 = "7478c7caa4ff6b37de86daba1f7ce4a994a4f5ba24872a820fb2b3a9b01fed15"


def main():
    cache = ROOT / ".cache/runtime"
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / NAME
    if not archive.exists():
        archive.write_bytes(urllib.request.urlopen(URL, timeout=90).read())
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Official runtime archive hash mismatch")
    subprocess.run(["tar", "-xf", str(archive), "-C", str(cache)], check=True)
    print(cache / "dist/lib/rime.dll")


if __name__ == "__main__":
    main()
