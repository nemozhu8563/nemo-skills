import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nemo_supabase_auth_validate_report", ROOT / "scripts" / "validate_report.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load validate_report.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def load_template():
    return json.loads((ROOT / "templates" / "oauth-report.template.json").read_text(encoding="utf-8"))


def make_configuration_ready():
    report = load_template()
    for name in VALIDATOR.CONFIGURATION_ACTIONS:
        action = report["actions"][name]
        action["authorization"] = {"status": "authorized", "evidence": "current scoped instruction"}
        action["before"] = {"state": "redacted", "observed_at": "2026-08-21T00:00:00Z"}
        action["execution"] = {"status": "succeeded", "evidence": f"evidence/{name}"}
        action["readback"] = {"status": "verified", "evidence": f"readback/{name}"}

    report["observations"]["official_sources"].update(
        {
            "supabase_google_guide_current": True,
            "supabase_redirect_guide_current": True,
            "supabase_changelog_reviewed": True,
        }
    )
    report["observations"]["application"].update(
        {
            "login_initiation_verified": True,
            "pkce_exchange_verified": True,
            "safe_relative_next_verified": True,
            "trusted_server_check_present": True,
            "project_native_checks": "passed",
        }
    )
    report["observations"]["google"].update(
        {
            "exact_project_verified": True,
            "web_client_type_verified": True,
            "origins_match": True,
            "redirect_uris_match": True,
            "audience_and_publication_verified": True,
            "minimum_scopes_only": True,
        }
    )
    report["observations"]["supabase"].update(
        {
            "exact_project_verified": True,
            "provider_enabled": True,
            "client_identifier_matches": True,
            "credential_present": True,
            "site_url_matches": True,
            "redirect_urls_match": True,
            "preview_patterns_reviewed": True,
        }
    )
    report["claims"]["configuration_ready"] = True
    report["missing_evidence"] = ["authorized real browser login"]
    return report


class PackageContractTest(unittest.TestCase):
    def test_package_has_one_discoverable_entrypoint(self):
        entries = [path.relative_to(ROOT).as_posix() for path in ROOT.rglob("SKILL.md")]
        self.assertEqual(entries, ["SKILL.md"])

    def test_required_governed_artifacts_exist(self):
        required = (
            "README.md",
            "LICENSE",
            "manifest.json",
            "agents/interface.yaml",
            "references/runbook.md",
            "references/evidence-and-rollback.md",
            "references/official-sources.md",
            "templates/oauth-report.template.json",
            "evals/trigger_cases.json",
            "evals/output_cases.json",
            "reports/prior-art-candidates.json",
            "reports/prior-art-research.md",
            "reports/output-eval.json",
            "reports/output-evidence.json",
            "reports/creation-handoff.md",
        )
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_skill_contains_governed_auth_boundaries(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "google_cloud_project",
            "google_auth_configuration",
            "google_oauth_client",
            "supabase_google_provider",
            "supabase_url_configuration",
            "real_login_test",
            "https://<project-ref>.supabase.co/auth/v1/callback",
            "exchangeCodeForSession(code)",
            "configuration_ready",
            "end_to_end_verified",
            "Dashboard `Enabled`",
            "openid",
        ):
            self.assertIn(required, skill)
        self.assertIn("用户直接填入", skill)
        self.assertIn("真实邮箱", skill)

    def test_manifest_declares_governed_release_gates(self):
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "nemo-supabase-auth")
        self.assertEqual(manifest["version"], "0.1.0")
        self.assertEqual(manifest["owner"], "Nemo")
        self.assertEqual(manifest["maturity_tier"], "governed")
        for gate in (
            "existing_resource_reuse_audit",
            "two_callback_url_matrix",
            "pkce_exchange_and_relative_next",
            "credential_and_identity_non_disclosure",
            "real_browser_login_authorization",
            "trusted_user_and_protected_route_verification",
            "secret_scan",
        ):
            self.assertIn(gate, manifest["release_gates"])

    def test_output_evidence_does_not_overclaim(self):
        evidence = json.loads((ROOT / "reports" / "output-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["evidence_kind"], "recorded_fixture")
        self.assertTrue(evidence["recorded_fixture"])
        self.assertFalse(evidence["provider_backed"])
        self.assertFalse(evidence["human_blind_review"])
        self.assertIn("provider-backed comparison", evidence["missing_evidence"])
        self.assertIn("human blind review", evidence["missing_evidence"])


class ReportValidatorTest(unittest.TestCase):
    def test_template_is_valid_without_success_claims(self):
        result = VALIDATOR.validate(load_template())
        self.assertTrue(result["ok"], result["failures"])

    def test_configuration_ready_accepts_mutation_and_reuse_readback(self):
        report = make_configuration_ready()
        reused = report["actions"]["google_cloud_project"]
        reused["authorization"] = {"status": "not_required", "evidence": "existing compatible project"}
        reused["execution"] = {"status": "not_required", "evidence": "existing compatible project"}
        reused["readback"] = {"status": "verified", "evidence": "provider/project-readback"}
        result = VALIDATOR.validate(report)
        self.assertTrue(result["ok"], result["failures"])

    def test_end_to_end_requires_full_authorized_browser_ladder(self):
        report = make_configuration_ready()
        login = report["actions"]["real_login_test"]
        login["authorization"] = {"status": "authorized", "evidence": "current scoped instruction"}
        login["execution"] = {"status": "succeeded", "evidence": "browser/run"}
        login["readback"] = {"status": "verified", "evidence": "application/protected-check"}
        report["observations"]["browser"] = {
            "expected_google_surface": True,
            "callback_chain_completed": True,
            "trusted_user_verified": True,
            "protected_route_verified": True,
            "logout_negative_verified": True,
        }
        report["claims"]["end_to_end_verified"] = True
        report["missing_evidence"] = []
        result = VALIDATOR.validate(report)
        self.assertTrue(result["ok"], result["failures"])

    def test_rejects_google_and_application_callback_conflation(self):
        report = load_template()
        report["url_matrix"]["google_redirect_uris"] = ["https://app.example.com/auth/callback"]
        result = VALIDATOR.validate(report)
        self.assertFalse(result["ok"])
        self.assertTrue(any("provider callback" in item for item in result["failures"]))

    def test_rejects_path_in_google_javascript_origin(self):
        report = load_template()
        report["url_matrix"]["google_javascript_origins"] = ["https://project-ref.supabase.co/auth/callback"]
        result = VALIDATOR.validate(report)
        self.assertFalse(result["ok"])
        self.assertTrue(any("origin only" in item for item in result["failures"]))

    def test_rejects_runtime_oauth_query_and_personal_identity(self):
        report = load_template()
        report["observations"]["browser"]["runtime"] = "https://app.example.com/auth/callback?code=redacted-value"
        report["observations"]["browser"]["email"] = "person@example.com"
        result = VALIDATOR.validate(report)
        self.assertFalse(result["ok"])
        self.assertTrue(any("runtime OAuth query" in item for item in result["failures"]))
        self.assertTrue(any("forbidden sensitive key" in item for item in result["failures"]))
        self.assertTrue(any("email-like personal data" in item for item in result["failures"]))

    def test_rejects_unsupported_configuration_ready_claim(self):
        report = load_template()
        report["claims"]["configuration_ready"] = True
        result = VALIDATOR.validate(report)
        self.assertFalse(result["ok"])
        self.assertTrue(any("terminal action evidence" in item for item in result["failures"]))

    def test_rejects_end_to_end_with_missing_evidence(self):
        report = make_configuration_ready()
        report["claims"]["end_to_end_verified"] = True
        result = VALIDATOR.validate(report)
        self.assertFalse(result["ok"])
        self.assertTrue(any("real_login_test" in item for item in result["failures"]))
        self.assertTrue(any("empty missing_evidence" in item for item in result["failures"]))

    def test_rejects_wildcard_on_production_host(self):
        report = load_template()
        report["url_matrix"]["preview_patterns"] = ["https://*.app.example.com/auth/callback"]
        result = VALIDATOR.validate(report)
        self.assertFalse(result["ok"])
        self.assertTrue(any("production host" in item for item in result["failures"]))

    def test_rejects_non_local_http_callback(self):
        report = load_template()
        report["url_matrix"]["supabase_redirect_urls"].append("http://preview.example.com/auth/callback")
        result = VALIDATOR.validate(report)
        self.assertFalse(result["ok"])
        self.assertTrue(any("insecure HTTP" in item for item in result["failures"]))


if __name__ == "__main__":
    unittest.main()
