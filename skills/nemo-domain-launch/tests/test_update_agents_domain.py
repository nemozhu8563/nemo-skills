import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import update_agents_domain  # noqa: E402


def ready_payload(project_dir: Path) -> dict:
    payload = json.loads((ROOT / "templates" / "launch-report.template.json").read_text(encoding="utf-8"))
    payload["scope"].update(
        {
            "project_dir": str(project_dir),
            "output_dir": str(project_dir / "dist"),
            "formal_domain_before": {"status": "absent", "evidence": "project inventory"},
        }
    )

    def passed(action_name: str) -> None:
        action = payload["actions"][action_name]
        action["authorization"] = {"status": "granted", "evidence": f"authorized {action_name}"}
        action["execution"] = {"status": "passed", "evidence": f"executed {action_name}"}
        action["readback"] = {"status": "passed", "evidence": f"read back {action_name}"}

    passed("pages_deploy")
    for action_name in ("custom_domain_binding", "dns_record_change", "nameserver_change", "dnssec_change"):
        passed(action_name)
    payload["actions"]["agents_md_writeback"]["target"] = str(project_dir / "AGENTS.md")
    payload["actions"]["agents_md_writeback"]["authorization"] = {
        "status": "granted",
        "evidence": "user requested post-launch writeback",
    }
    payload["observations"]["provider"].update(
        {
            "pages_deployment": "passed",
            "vercel_deployment": "not_required",
            "cloudflare_zone": "passed",
            "custom_domain": "passed",
            "certificate": "passed",
            "hosting_dns": "passed",
            "cloudflare_dnssec": "passed",
        }
    )
    payload["observations"]["public_dns"].update(
        {
            "resolvers": ["1.1.1.1", "8.8.8.8"],
            "cloudflare_nameservers": True,
            "hosting_records_match": True,
            "ds_present": True,
            "dnssec_ad_resolvers": ["1.1.1.1", "8.8.8.8"],
        }
    )
    payload["observations"]["public_http"].update(
        {
            "hosting_default_url": "passed",
            "root": "passed",
            "representative_path": "passed",
            "canonical": "passed",
            "robots": "passed",
            "sitemap": "passed",
            "tls": "passed",
        }
    )
    payload["claims"] = {"domain_ready": True, "launch_complete": False, "dnssec_complete": True}
    payload["missing_evidence"] = []
    return payload


class AgentsDomainWritebackTest(unittest.TestCase):
    def write_report(self, project_dir: Path, payload: dict) -> Path:
        report = project_dir / "launch-report.json"
        report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return report

    def test_creates_project_root_agents_and_completes_report(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory)
            report = self.write_report(project, ready_payload(project))
            result = update_agents_domain.execute_writeback(report)
            agents_text = (project / "AGENTS.md").read_text(encoding="utf-8")
            updated = json.loads(report.read_text(encoding="utf-8"))
        self.assertTrue(result["ok"])
        self.assertTrue(result["changed"])
        self.assertIn("Formal domain: https://example.com", agents_text)
        self.assertIn("Deployment mode: `static_pages`", agents_text)
        self.assertTrue(updated["claims"]["launch_complete"])
        self.assertEqual(updated["observations"]["agents_md"]["status"], "passed")

    def test_preserves_existing_content_and_second_run_is_noop(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory)
            prefix = "# Project rules\n\n- Keep this line unchanged.\n"
            (project / "AGENTS.md").write_text(prefix, encoding="utf-8")
            report = self.write_report(project, ready_payload(project))
            first = update_agents_domain.execute_writeback(report)
            after_first = (project / "AGENTS.md").read_text(encoding="utf-8")
            second = update_agents_domain.execute_writeback(report)
            after_second = (project / "AGENTS.md").read_text(encoding="utf-8")
        self.assertTrue(first["changed"])
        self.assertFalse(second["changed"])
        self.assertTrue(after_first.startswith(prefix))
        self.assertEqual(after_first, after_second)
        self.assertEqual(after_second.count(update_agents_domain.BEGIN_MARKER), 1)

    def test_rejects_writeback_before_domain_ready(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory)
            payload = ready_payload(project)
            payload["claims"]["domain_ready"] = False
            report = self.write_report(project, payload)
            with self.assertRaisesRegex(ValueError, "domain_ready"):
                update_agents_domain.execute_writeback(report)
            self.assertFalse((project / "AGENTS.md").exists())

    def test_conflicting_managed_block_is_not_overwritten(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory)
            existing = update_agents_domain.managed_block("https://other.example", "static_pages") + "\n"
            agents = project / "AGENTS.md"
            agents.write_text(existing, encoding="utf-8")
            report = self.write_report(project, ready_payload(project))
            with self.assertRaisesRegex(ValueError, "different"):
                update_agents_domain.execute_writeback(report)
            self.assertEqual(agents.read_text(encoding="utf-8"), existing)

    def test_symlinked_agents_file_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory)
            outside = project / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            (project / "AGENTS.md").symlink_to(outside)
            report = self.write_report(project, ready_payload(project))
            with self.assertRaisesRegex(ValueError, "symlink"):
                update_agents_domain.execute_writeback(report)
            self.assertEqual(outside.read_text(encoding="utf-8"), "outside\n")

    def test_saas_mode_records_the_vercel_route(self) -> None:
        block = update_agents_domain.managed_block("https://saas.example", "saas_vercel")
        self.assertIn("Deployment mode: `saas_vercel`", block)
        self.assertIn("Route: Spaceship → Cloudflare DNS → Vercel", block)


if __name__ == "__main__":
    unittest.main()
