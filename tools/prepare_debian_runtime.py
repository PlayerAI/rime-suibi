#!/usr/bin/env python3
"""Download/extract missing Debian libraries inside .cache; never install system packages.

Run within Debian (or its WSL instance). SPDX-License-Identifier: GPL-3.0-only
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/debian"


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    # An old host package index may reference removed .deb files. Refresh a
    # project-local index without touching /var/lib/apt or installing packages.
    lists = CACHE / "lists"
    (lists / "partial").mkdir(parents=True, exist_ok=True)
    options = ["-o", f"Dir::State::lists={lists}", "-o", "Debug::NoLocking=1"]
    subprocess.run(["apt-get", *options, "update"], check=True)
    packages, pending = set(), ["librime1t64", "librime-plugin-lua", "librime-bin", "lua5.4"]
    while pending:
        name = pending.pop()
        if name in packages:
            continue
        status = subprocess.run(["dpkg-query", "-W", "-f=${Status}", name], capture_output=True, text=True)
        if status.returncode == 0 and "install ok installed" in status.stdout:
            continue
        packages.add(name)
        output = subprocess.check_output(["apt-cache", *options, "depends", name], text=True)
        for dep in re.findall(r"^\s*(?:Pre)?Depends:\s+([^\s<>]+)", output, re.M):
            pending.append(dep)
    for name in sorted(packages):
        subprocess.run(["apt-get", *options, "download", name], cwd=CACHE, check=True)
    dest = CACHE / "root"
    dest.mkdir(exist_ok=True)
    for package in sorted(CACHE.glob("*.deb")):
        subprocess.run(["dpkg-deb", "-x", str(package), str(dest)], check=True)
    (CACHE / "packages.json").write_text(json.dumps(sorted(packages), indent=2), encoding="utf-8")
    print("Portable Debian runtime:", dest)


if __name__ == "__main__":
    main()
