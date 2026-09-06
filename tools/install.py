#!/usr/bin/env python3
"""Install only Suibi-owned files; back up replacements. SPDX-License-Identifier: GPL-3.0-only"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import sys
import uuid
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ("suibi_pinyin", "suibi_double_pinyin", "suibi_mspy")
RUNTIME_FILES = ["suibi.dict.yaml", "suibi_pinyin.schema.yaml", "suibi_double_pinyin.schema.yaml", "suibi_mspy.schema.yaml",
                 "cn_dicts/suibi_chars.dict.yaml", "cn_dicts/suibi_words.dict.yaml"] + [
    f"lua/suibi/{name}.lua" for name in ("core", "data", "filter", "processor", "segmentor", "translator")]


def default_target(system: str | None = None) -> Path:
    system = system or sys.platform
    if system == "win32":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise ValueError("APPDATA is unset; supply --target with the actual Rime user directory")
        return Path(appdata) / "Rime"
    if system.startswith("linux"):
        return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "fcitx5/rime"
    raise ValueError("Supported platforms: Windows, CachyOS and Debian; use --target for an explicit test directory")


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"Duplicate YAML key in existing configuration: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def enabled_config(original: bytes | None, selected=SCHEMAS) -> bytes:
    doc = yaml.load(original.decode("utf-8-sig"), Loader=UniqueLoader) if original else {}
    if doc is None:
        doc = {}
    if not isinstance(doc, dict):
        raise ValueError("default.custom.yaml must be a mapping; enable the schemas manually")
    patch = doc.setdefault("patch", {})
    if not isinstance(patch, dict):
        raise ValueError("Existing patch is not a mapping; enable the schemas manually")
    key = "schema_list" if "schema_list" in patch else "schema_list/+"
    schemas = patch.setdefault(key, [])
    if not isinstance(schemas, list) or any(not isinstance(x, dict) or "schema" not in x for x in schemas):
        raise ValueError("Existing schema list uses an unsupported structure; enable the schemas manually")
    existing = {x["schema"] for x in schemas}
    additions = [s for s in selected if s not in existing]
    if not additions and original is not None:
        return original  # Idempotent updates preserve the exact original bytes.
    schemas.extend({"schema": s} for s in additions)
    return yaml.safe_dump(doc, allow_unicode=True, sort_keys=False).encode("utf-8")


def within(target: Path, relative: str) -> Path:
    path = target / relative
    if not path.resolve().is_relative_to(target):
        raise ValueError(f"Path escapes the selected Rime directory (symlink?): {path}")
    if path.exists() and not path.is_file():
        raise ValueError(f"Expected file, found another object: {path}")
    return path


def install(target: Path, *, enable=False, dry_run=False, source: Path = ROOT, scheme: str | None = None) -> dict:
    target = target.expanduser().resolve()
    if target == source.resolve():
        raise ValueError("The installation directory cannot be the source repository")
    # Preflight everything, including config parsing, before the first write.
    if scheme is None and (source / "package.json").exists():
        scheme = json.loads((source / "package.json").read_text(encoding="utf-8"))["scheme"]
    if scheme is not None and scheme not in SCHEMAS:
        raise ValueError("Unknown scheme: " + scheme)
    selected = (scheme,) if scheme else SCHEMAS
    names = [n for n in RUNTIME_FILES if not n.endswith(".schema.yaml") or n.removesuffix(".schema.yaml") in selected]
    payloads = {name: (source / name).read_bytes() for name in names}
    for name in payloads:
        within(target, name)
    config = within(target, "default.custom.yaml")
    if enable:
        payloads["default.custom.yaml"] = enabled_config(config.read_bytes() if config.exists() else None, selected)
    changed = [name for name, content in payloads.items()
               if not (target / name).exists() or (target / name).read_bytes() != content]
    backup_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
    backup = target / ".suibi-backups" / backup_id
    if not backup.resolve().is_relative_to(target):
        raise ValueError("Backup directory escapes the selected Rime directory")
    result = {"target": str(target), "changed_files": changed, "enabled": enable,
              "dry_run": dry_run, "backup": str(backup) if changed else None}
    if dry_run or not changed:
        return result
    target.mkdir(parents=True, exist_ok=True)
    backup.mkdir(parents=True, exist_ok=False)
    # Save all existing bytes before replacing any file.
    existed = []
    for name in changed:
        destination = within(target, name)
        if destination.exists():
            archived = backup / name
            archived.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, archived)
            existed.append(name)
    (backup / "manifest.json").write_text(json.dumps({"replaced": existed,
        "created": [name for name in changed if name not in existed]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name in changed:
        destination = within(target, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payloads[name])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, help="Actual Rime user data directory")
    parser.add_argument("--enable", action="store_true", help="Append selected schemas to default.custom.yaml; preserve values and back up original formatting")
    parser.add_argument("--scheme", choices=SCHEMAS, help="Install one scheme; independent packages select it automatically")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changing files")
    args = parser.parse_args()
    result = install(args.target or default_target(), enable=args.enable, dry_run=args.dry_run, scheme=args.scheme)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not args.dry_run:
        print("请在小狼毫/Fcitx5-Rime 中重新部署，然后选择安装的随笔方案。")
        if not args.enable:
            print("未更改方案选单；请按 docs/INSTALL.md 启用方案，或使用 --enable。")


if __name__ == "__main__":
    main()
