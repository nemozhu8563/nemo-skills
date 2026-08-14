import sys
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import preflight  # noqa: E402


class PreflightTest(unittest.TestCase):
    def make_site(self, root: Path, origin: str = "https://example.com") -> None:
        output = root / "dist"
        (output / "guide").mkdir(parents=True)
        (output / "index.html").write_text(
            f'<html><head><link rel="canonical" href="{origin}/"></head><body>Home</body></html>',
            encoding="utf-8",
        )
        (output / "guide" / "index.html").write_text(
            f'<html><head><link rel="canonical" href="{origin}/guide/"></head><body>Guide</body></html>',
            encoding="utf-8",
        )
        (output / "robots.txt").write_text(
            f"User-agent: *\nAllow: /\nSitemap: {origin}/sitemap.xml\n",
            encoding="utf-8",
        )
        (output / "sitemap.xml").write_text(
            f'<?xml version="1.0"?><urlset><url><loc>{origin}/</loc></url><url><loc>{origin}/guide/</loc></url></urlset>',
            encoding="utf-8",
        )

    def test_valid_static_output_passes(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory)
            self.make_site(project)
            report = preflight.run_preflight(
                project,
                "dist",
                "https://example.com",
                ["/guide/"],
            )
        self.assertTrue(report["summary"]["ok"], report["summary"])
        self.assertEqual(report["production_origin"], "https://example.com")

    def test_stale_origin_and_missing_route_fail(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory)
            self.make_site(project, "https://preview.example.net")
            report = preflight.run_preflight(
                project,
                "dist",
                "https://example.com",
                ["/missing/"],
            )
        self.assertFalse(report["summary"]["ok"])
        self.assertIn("canonicals", report["summary"]["failures"])
        self.assertIn("robots_sitemap", report["summary"]["failures"])
        self.assertIn("sitemap", report["summary"]["failures"])
        self.assertIn("representative_paths", report["summary"]["failures"])

    def test_robots_rejects_sitemap_prefix_trick(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory)
            self.make_site(project)
            (project / "dist" / "robots.txt").write_text(
                "Sitemap: https://example.com/sitemap.xml.evil\n",
                encoding="utf-8",
            )
            report = preflight.run_preflight(project, "dist", "https://example.com", ["/guide/"])
        self.assertIn("robots_sitemap", report["summary"]["failures"])

    def test_origin_rejects_local_credentials_and_paths(self) -> None:
        for value in (
            "http://example.com",
            "https://localhost",
            "https://name:credential@example.com",
            "https://example.com/path",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                preflight.normalize_origin(value)

    def test_report_exposes_script_names_not_command_bodies(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory)
            self.make_site(project)
            (project / "package.json").write_text(
                json.dumps({"scripts": {"build": "opaque-sensitive-command", "check": "tool check"}}),
                encoding="utf-8",
            )
            report = preflight.run_preflight(project, "dist", "https://example.com", ["/guide/"])
        self.assertEqual(report["package_scripts"], ["build", "check"])
        self.assertNotIn("opaque-sensitive-command", json.dumps(report))

    def test_representative_route_cannot_escape_output(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "dist"
            output.mkdir()
            (output.parent / "outside.html").write_text("outside", encoding="utf-8")
            self.assertFalse(preflight.path_exists_for_route(output, "/../outside.html"))
            self.assertFalse(preflight.path_exists_for_route(output, "https://other.example/page"))

    def test_external_output_directory_is_not_scanned(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            external = root / "external"
            self.make_site(external)
            report = preflight.run_preflight(
                project,
                str(external / "dist"),
                "https://example.com",
                ["/guide/"],
            )
        self.assertIn("output_within_project", report["summary"]["failures"])
        self.assertIn("output_directory", report["summary"]["failures"])
        self.assertEqual(next(item for item in report["checks"] if item["name"] == "html_output")["detail"]["count"], 0)


if __name__ == "__main__":
    unittest.main()
