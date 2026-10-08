import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import (ConfigError, business_onedrive_roots, load_settings,
                   portable_settings, read_settings, resolve_sources)


ROOT = Path(__file__).resolve().parents[1]


def files(root):
    folder = root / "Logistica"
    folder.mkdir(parents=True)
    imports, exports = folder / "imports.xlsx", folder / "exports.xlsx"
    for path, fields in ((imports, ["Items", "Status", "HBL", "Container", "ETA", "ATP"]),
                         (exports, ["Origin", "Reservation", "Container", "Transfer", "Deliver at TTICR"])):
        book = Workbook()
        book.active.title = "Itinerario"
        book.active.append(fields)
        book.save(path)
        book.close()
    return {"demo": False, "imports": {"path": str(imports), "sheet": "Itinerario", "headerRow": 1},
            "exports": {"path": str(exports), "sheet": "*", "headerRow": None}}


class PathTests(unittest.TestCase):
    def test_portable_config_works_under_another_user_without_changing_it(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            first = base / "UsuarioA" / "OneDrive - Empresa"
            second = base / "UsuarioB" / "OneDrive - Empresa"
            settings = files(first)
            files(second)
            portable = portable_settings(settings, base, environ={}, roots=[first])
            self.assertEqual(portable["imports"]["path"], "Logistica/imports.xlsx")
            self.assertNotIn("UsuarioA", json.dumps(portable))
            moved = resolve_sources(portable, base, environ={}, roots=[second])
            self.assertEqual(moved["imports"]["path"], str(second / "Logistica" / "imports.xlsx"))
            self.assertEqual(moved["exports"]["sheet"], "*")
            self.assertEqual(settings["imports"]["path"], str(first / "Logistica" / "imports.xlsx"))

    def test_only_matching_business_account_is_chosen_and_ambiguity_requires_override(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            first, second = base / "BusinessA", base / "BusinessB"
            settings = files(first)
            second.mkdir()
            portable = portable_settings(settings, base, environ={}, roots=[first])
            self.assertEqual(resolve_sources(portable, base, environ={}, roots=[second, first])["imports"]["path"],
                             settings["imports"]["path"])
            files(second)
            with self.assertRaisesRegex(ConfigError, "más de un OneDrive"):
                resolve_sources(portable, base, environ={}, roots=[first, second])
            resolved = resolve_sources(portable, base,
                                       environ={"TECHTOP_ONEDRIVE_ROOT": str(second)}, roots=[first, second])
            self.assertTrue(resolved["imports"]["path"].startswith(str(second)))

    def test_missing_file_or_invalid_override_does_not_fall_back(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            settings = files(base / "Business")
            portable = portable_settings(settings, base, environ={}, roots=[base / "Business"])
            with self.assertRaisesRegex(ConfigError, "TECHTOP_ONEDRIVE_ROOT"):
                resolve_sources(portable, base, environ={"TECHTOP_ONEDRIVE_ROOT": str(base / "Missing")},
                                roots=[base / "Business"])
            Path(settings["exports"]["path"]).unlink()
            with self.assertRaisesRegex(ConfigError, "No se encontró un OneDrive"):
                resolve_sources(portable, base, environ={}, roots=[base / "Business"])

    def test_root_discovery_ignores_personal_and_deduplicates_business_roots(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            business, personal = base / "Business", base / "Personal"
            business.mkdir()
            personal.mkdir()
            with patch("paths._registry_business_roots", return_value=[str(business)]):
                roots = business_onedrive_roots({"OneDriveCommercial": str(business), "OneDrive": str(personal)})
                self.assertEqual(roots, [business])
            with patch("paths._registry_business_roots", return_value=[]):
                self.assertEqual(business_onedrive_roots({"OneDrive": str(personal)}), [])

    def test_onedrive_paths_cannot_escape_authorized_root(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            settings = files(base / "Business")
            portable = portable_settings(settings, base, environ={}, roots=[base / "Business"])
            for value in ("../imports.xlsx", "C:/imports.xlsx", "C:imports.xlsx", r"\\server\share\imports.xlsx",
                          "/imports.xlsx", "Logistica/../../imports.xlsx"):
                with self.subTest(value=value):
                    portable["imports"]["path"] = value
                    with self.assertRaises(ConfigError):
                        resolve_sources(portable, base, environ={}, roots=[base / "Business"])
            outside = base / "Outside"
            outside.mkdir()
            (outside / "imports.xlsx").write_bytes(b"not a workbook")
            try:
                (base / "Business" / "Link").symlink_to(outside, target_is_directory=True)
            except OSError:
                return  # Windows necesita autorización especial para crear symlinks.
            portable["imports"]["path"] = "Link/imports.xlsx"
            with self.assertRaises(ConfigError):
                resolve_sources(portable, base, environ={}, roots=[base / "Business"])

    def test_existing_absolute_and_config_relative_paths_and_bom_remain_supported(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            settings = files(base / "Business")
            settings["exports"]["path"] = "samples/example.xlsx"
            config = base / "config.local.json"
            config.write_text(json.dumps(settings), encoding="utf-8-sig")
            resolved = load_settings(config, environ={}, roots=[])
            self.assertEqual(resolved["imports"]["path"], settings["imports"]["path"])
            self.assertEqual(resolved["exports"]["path"], str(base / "samples/example.xlsx"))

    def test_invalid_json_error_hides_private_content(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "config.local.json"
            config.write_text('{"imports":{"path":"C:\\UsuariosPrivados\\itinerario.xlsx"}}', encoding="utf-8")
            with self.assertRaises(ConfigError) as result:
                read_settings(config)
            self.assertIn("línea", str(result.exception))
            self.assertNotIn("UsuariosPrivados", str(result.exception))

    def test_script_converts_checks_and_repeats_without_touching_workbooks(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            root = base / "Business"
            settings = files(root)
            config = base / "config.local.json"
            config.write_text(json.dumps(settings), encoding="utf-8-sig")
            before = config.read_bytes()
            workbooks = {Path(source["path"]): Path(source["path"]).read_bytes()
                         for source in (settings["imports"], settings["exports"])}
            environ = dict(os.environ, OneDriveCommercial=str(root), TECHTOP_ONEDRIVE_ROOT=str(root))
            command = [sys.executable, str(ROOT / "scripts/configurar_onedrive.py"), "--config", str(config)]
            for arguments in (command, command, command + ["--check"]):
                result = subprocess.run(arguments, env=environ, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn(str(root), result.stdout + result.stderr)
            self.assertEqual(config.with_name("config.local.json.bak").read_bytes(), before)
            self.assertEqual(read_settings(config)["imports"]["pathBase"], "onedrive")
            for path, original in workbooks.items():
                self.assertEqual(path.read_bytes(), original)

    def test_script_leaves_configuration_unchanged_when_workbook_structure_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            root = base / "Business"
            settings = files(root)
            book = Workbook()
            book.active.title = "Itinerario"
            book.active.append(["Items", "Status", "HBL", "Container", "ETA"])
            book.save(settings["imports"]["path"])
            book.close()
            config = base / "config.local.json"
            config.write_text(json.dumps(settings), encoding="utf-8")
            original = config.read_bytes()
            result = subprocess.run([sys.executable, str(ROOT / "scripts/configurar_onedrive.py"),
                                     "--config", str(config)], env=dict(os.environ, TECHTOP_ONEDRIVE_ROOT=str(root)),
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(config.read_bytes(), original)
            self.assertFalse(config.with_name("config.local.json.bak").exists())
            self.assertNotIn(str(root), result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
