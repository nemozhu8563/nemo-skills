import copy
import json
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_launch_report  # noqa: E402


class LaunchReportTest(unittest.TestCase):
    def load_template(self) -> dict:
        return json.loads((ROOT / "templates" / "launch-report.template.json").read_text(encoding="utf-8"))

    def set_passed(self, action: dict, label: str) -> None:
        action["authorization"] = {"status": "granted", "evidence": f"authorized {label}"}
        action["execution"] = {"status": "passed", "evidence": f"executed {label}"}
        action["readback"] = {"status": "passed", "evidence": f"read back {label}"}

    def set_not_required(self, action: dict, reason: str) -> None:
        for phase in ("authorization", "execution", "readback"):
            action[phase] = {"status": "not_required", "evidence": reason}

    def domain_ready_payload(self, mode: str = "static_pages") -> dict:
        payload = copy.deepcopy(self.load_template())
        payload["scope"]["formal_domain_before"] = {
            "status": "absent",
            "evidence": "project docs, config, and provider inventory",
        }
        payload["actions"]["agents_md_writeback"]["authorization"] = {
            "status": "granted",
            "evidence": "user requested final writeback",
        }
        if mode == "static_pages":
            self.set_passed(payload["actions"]["pages_deploy"], "Pages deployment")
            self.set_not_required(payload["actions"]["vercel_deploy"], "deployment_mode=static_pages")
            payload["observations"]["provider"]["pages_deployment"] = "passed"
            payload["observations"]["provider"]["vercel_deployment"] = "not_required"
        else:
            payload["scope"].update(
                {
                    "deployment_mode": "saas_vercel",
                    "output_dir": None,
                    "pages_project": None,
                    "vercel_project": "example-saas",
                }
            )
            self.set_not_required(payload["actions"]["pages_deploy"], "deployment_mode=saas_vercel")
            self.set_passed(payload["actions"]["vercel_deploy"], "Vercel deployment")
            payload["observations"]["provider"]["pages_deployment"] = "not_required"
            payload["observations"]["provider"]["vercel_deployment"] = "passed"
            payload["observations"]["public_http"].update(
                {"canonical": "not_required", "robots": "not_required", "sitemap": "not_required"}
            )
            payload["observations"]["public_dns"]["verification_records_dns_only"] = "passed"

        for action_name in ("custom_domain_binding", "dns_record_change", "nameserver_change", "dnssec_change"):
            self.set_passed(payload["actions"][action_name], action_name)
        payload["observations"]["provider"].update(
            {
                "cloudflare_zone": "passed",
                "custom_domain": "passed",
                "certificate": "passed",
                "hosting_dns": "passed",
                "cloudflare_dnssec": "passed",
            }
        )
        payload["observations"]["public_http"].update(
            {
                "hosting_default_url": "passed",
                "root": "passed",
                "representative_path": "passed",
                "tls": "passed",
            }
        )
        if mode == "static_pages":
            payload["observations"]["public_http"].update(
                {"canonical": "passed", "robots": "passed", "sitemap": "passed"}
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
        payload["claims"] = {"domain_ready": True, "launch_complete": False, "dnssec_complete": True}
        payload["missing_evidence"] = []
        return payload

    def mark_writeback_complete(self, payload: dict) -> None:
        action = payload["actions"]["agents_md_writeback"]
        self.set_passed(action, "project-root AGENTS.md")
        project_dir = payload["scope"]["project_dir"]
        action["target"] = str(Path(project_dir) / "AGENTS.md")
        payload["observations"]["agents_md"] = {
            "status": "passed",
            "path": str(Path(project_dir) / "AGENTS.md"),
            "managed_block": "nemo-domain-launch",
        }
        payload["claims"]["launch_complete"] = True

    def test_unresolved_template_is_valid_but_not_complete(self) -> None:
        result = validate_launch_report.validate_report(self.load_template())
        self.assertTrue(result["ok"], result)
        self.assertIn("domain_ready is not proven", result["warnings"])

    def test_static_pages_domain_ready_claim_requires_all_evidence(self) -> None:
        result = validate_launch_report.validate_report(
            self.domain_ready_payload("static_pages"), require_domain_ready=True
        )
        self.assertTrue(result["ok"], result)

    def test_saas_vercel_domain_ready_accepts_mode_appropriate_seo_noops(self) -> None:
        result = validate_launch_report.validate_report(
            self.domain_ready_payload("saas_vercel"), require_domain_ready=True
        )
        self.assertTrue(result["ok"], result)

    def test_inactive_hosting_route_requires_not_required_triad(self) -> None:
        payload = self.domain_ready_payload("saas_vercel")
        payload["actions"]["pages_deploy"]["readback"]["status"] = "passed"
        result = validate_launch_report.validate_report(payload)
        self.assertFalse(result["ok"])
        self.assertTrue(any("pages_deploy" in failure for failure in result["failures"]))

    def test_existing_dns_resources_can_be_evidenced_noops(self) -> None:
        payload = self.domain_ready_payload()
        for action_name in ("dns_record_change", "nameserver_change"):
            self.set_not_required(payload["actions"][action_name], "already matches target")
        result = validate_launch_report.validate_report(payload)
        self.assertTrue(result["ok"], result)

    def test_formal_domain_present_blocks_domain_ready(self) -> None:
        payload = self.domain_ready_payload()
        payload["scope"]["formal_domain_before"]["status"] = "present"
        result = validate_launch_report.validate_report(payload)
        self.assertFalse(result["ok"])
        self.assertTrue(any("formal_domain_before" in failure for failure in result["failures"]))

    def test_launch_complete_requires_agents_md_readback(self) -> None:
        payload = self.domain_ready_payload()
        payload["claims"]["launch_complete"] = True
        result = validate_launch_report.validate_report(payload)
        self.assertFalse(result["ok"])
        self.assertTrue(any("agents_md" in failure for failure in result["failures"]))

    def test_launch_complete_accepts_verified_agents_md_writeback(self) -> None:
        payload = self.domain_ready_payload("saas_vercel")
        self.mark_writeback_complete(payload)
        result = validate_launch_report.validate_report(payload, require_launch_complete=True)
        self.assertTrue(result["ok"], result)

    def test_execution_without_authorization_is_rejected(self) -> None:
        payload = self.load_template()
        payload["actions"]["pages_deploy"]["execution"]["status"] = "passed"
        result = validate_launch_report.validate_report(payload)
        self.assertFalse(result["ok"])
        self.assertIn("pages_deploy executed without granted authorization", result["failures"])

    def test_secret_like_field_is_rejected(self) -> None:
        payload = self.load_template()
        payload["provider_access_token"] = "fixture-value-that-must-not-be-recorded"
        result = validate_launch_report.validate_report(payload)
        self.assertFalse(result["ok"])
        self.assertTrue(any("secret-like key" in failure for failure in result["failures"]))

    def test_scope_origin_must_be_exact_https_domain_origin(self) -> None:
        for value in (
            "https://name:credential@example.com",
            "https://example.com/path",
            "https://example.com?preview=1",
            "https://other.example",
            "https://example.com:invalid",
        ):
            with self.subTest(value=value):
                payload = self.load_template()
                payload["scope"]["production_origin"] = value
                result = validate_launch_report.validate_report(payload)
                self.assertFalse(result["ok"])
                self.assertTrue(any("production_origin" in failure for failure in result["failures"]))

    def test_provider_default_url_cannot_be_the_formal_domain(self) -> None:
        for domain in ("project.pages.dev", "project.vercel.app"):
            with self.subTest(domain=domain):
                payload = self.load_template()
                payload["scope"]["domain"] = domain
                payload["scope"]["production_origin"] = f"https://{domain}"
                result = validate_launch_report.validate_report(payload)
                self.assertFalse(result["ok"])
                self.assertIn(
                    "scope.domain must be a formal domain, not a provider default domain",
                    result["failures"],
                )


if __name__ == "__main__":
    unittest.main()
