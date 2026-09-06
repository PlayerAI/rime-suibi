"""Installer must preserve unrelated configuration and reject unsafe targets. GPL-3.0-only."""
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import install


class InstallTests(unittest.TestCase):
    def setUp(self):
        (ROOT / ".build").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="install-", dir=ROOT / ".build")
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name) / "rime"

    def test_dry_run_does_not_create_target(self):
        install.install(self.target, enable=True, dry_run=True)
        self.assertFalse(self.target.exists())

    def test_preserves_config_and_backs_up_exact_bytes(self):
        self.target.mkdir()
        original = b"# User comment\npatch:\n  menu/page_size: 9\n  schema_list:\n    - schema: rime_ice\n"
        config = self.target / "default.custom.yaml"
        config.write_bytes(original)
        unrelated = self.target / "rime.lua"
        unrelated.write_text("-- user content", encoding="utf-8")
        result = install.install(self.target, enable=True)
        doc = yaml.safe_load(config.read_text(encoding="utf-8"))
        self.assertEqual(9, doc["patch"]["menu/page_size"])
        self.assertEqual(["rime_ice", *install.SCHEMAS], [x["schema"] for x in doc["patch"]["schema_list"]])
        self.assertEqual(original, (Path(result["backup"]) / "default.custom.yaml").read_bytes())
        self.assertEqual("-- user content", unrelated.read_text())
        self.assertEqual([], install.install(self.target, enable=True)["changed_files"])

    def test_without_enable_does_not_touch_default(self):
        self.target.mkdir()
        config = self.target / "default.custom.yaml"
        config.write_text("# unusual custom config\npatch: {}\n", encoding="utf-8")
        before = config.read_bytes()
        install.install(self.target)
        self.assertEqual(before, config.read_bytes())

    def test_append_patch_preserves_base_schema_list(self):
        doc = yaml.safe_load(install.enabled_config(b"patch:\n  schema_list/+:\n    - schema: another\n"))
        self.assertNotIn("schema_list", doc["patch"])
        self.assertEqual(["another", *install.SCHEMAS], [x["schema"] for x in doc["patch"]["schema_list/+"]])

    def test_invalid_yaml_fails_before_copy(self):
        self.target.mkdir()
        config = self.target / "default.custom.yaml"
        for original in [b"patch: 123", b"patch: {}\npatch: {}\n", b"patch:\n  schema_list: special"]:
            config.write_bytes(original)
            with self.assertRaises(ValueError):
                install.install(self.target, enable=True)
            self.assertEqual(original, config.read_bytes())
            self.assertFalse((self.target / "suibi.dict.yaml").exists())

    def test_selected_scheme_only_and_coexistence(self):
        install.install(self.target, enable=True, scheme="suibi_mspy")
        self.assertTrue((self.target / "suibi_mspy.schema.yaml").exists())
        self.assertFalse((self.target / "suibi_pinyin.schema.yaml").exists())
        config = self.target / "default.custom.yaml"
        self.assertEqual([{"schema": "suibi_mspy"}], yaml.safe_load(config.read_text())["patch"]["schema_list/+"])
        install.install(self.target, enable=True, scheme="suibi_pinyin")
        self.assertEqual([{"schema": "suibi_mspy"}, {"schema": "suibi_pinyin"}], yaml.safe_load(config.read_text())["patch"]["schema_list/+"])

    def test_rejects_source_directory(self):
        with self.assertRaises(ValueError):
            install.install(ROOT)


if __name__ == "__main__":
    unittest.main()
