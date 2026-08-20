import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillContractTest(unittest.TestCase):
    def test_only_root_skill_entrypoint_is_discoverable(self) -> None:
        entries = [path.relative_to(ROOT) for path in ROOT.rglob("SKILL.md")]
        self.assertEqual(entries, [Path("SKILL.md")])

    def test_cross_site_scope_and_independent_outputs_are_present(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "游戏站、SaaS、内容站、文档站",
            "ga4.production_request",
            "ga4.realtime",
            "clarity.tag_loaded",
            "clarity.recording",
            "gsc.public_dns",
            "gsc.indexing",
            "recovery_checkpoint",
            "google_api",
            "ga4.readback_surface",
            "gsc.readback_surface",
        ):
            self.assertIn(required, skill)

    def test_governed_boundaries_are_present(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        governance = (ROOT / "references" / "governance.md").read_text(encoding="utf-8")
        combined = skill + governance
        for required in (
            "production-only 是本 Skill 的治理选择",
            "Consent Mode",
            "两个独立公共解析器",
            "Google 会周期性复查",
            "cookie、session、OAuth access/refresh token",
            "missing evidence",
            "必须单独确认",
        ):
            self.assertIn(required, combined)

    def test_no_runtime_dependency_on_old_gsc_skill(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["dependencies"], [])
        self.assertFalse(
            manifest["release_gates"]["runtime_dependency_on_nemo_gsc_submit"]
        )
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("调用 nemo-gsc-submit", skill)

    def test_google_api_adapter_resources_and_boundaries_are_present(self) -> None:
        for relative in (
            "contracts/google-api-output.schema.json",
            "scripts/google_api_adapter.py",
            "scripts/google_api/auth.py",
            "scripts/google_api/http.py",
            "scripts/google_api/gsc.py",
            "scripts/google_api/ga4.py",
            "scripts/google_api/plans.py",
            "scripts/google_api/output.py",
            "references/google-api.md",
            "tests/test_google_api_contract.py",
            "tests/test_google_api_adapter.py",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)
        combined = "\n".join(
            (ROOT / relative).read_text(encoding="utf-8")
            for relative in ("SKILL.md", "README.md", "references/google-api.md")
        )
        for required in (
            "bootstrap enable-apis",
            "plan → apply → readback",
            "Python 3.11+",
            "webmasters.readonly",
            "analytics.readonly",
            "gsc search-analytics",
            "webmasters.searchanalytics.query",
            "top aggregated rows",
            "missing evidence",
            "GA4 模糊 create 永不自动 replay",
        ):
            self.assertIn(required, combined)

    def test_first_readiness_and_configuration_plan_are_in_skill_prompt(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        interface = (ROOT / "agents" / "interface.yaml").read_text(encoding="utf-8")
        workflow = (ROOT / "references" / "workflow.md").read_text(encoding="utf-8")
        google_api = (ROOT / "references" / "google-api.md").read_text(encoding="utf-8")
        combined = "\n".join((skill, interface, workflow, google_api))
        for required in (
            "readiness_check",
            "configuration_plan",
            "第一项可观察动作必须是只读",
            "先于任何登录、配置、代码修改或外部写入",
            "用户可见",
            "desired_resource",
            "existing_matches",
            "external_write",
            "readback",
            "rollback",
            "google_api_bootstrap",
            "capabilities_and_scopes",
            "required_services",
            "resource_permissions",
            "gcloud auth login",
            "gcloud auth application-default login",
            "Google 浏览器",
            "Microsoft",
        ):
            self.assertIn(required, combined)

        self.assertIn("readiness_check:", skill)
        self.assertIn("configuration_plan:", skill)
        self.assertIn("Do not launch OAuth/login automatically", interface)

    def test_sitemap_intent_matrix_is_present(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        gsc = (ROOT / "references" / "gsc.md").read_text(encoding="utf-8")
        governance = (ROOT / "references" / "governance.md").read_text(encoding="utf-8")
        combined = skill + gsc + governance
        for required in (
            "status_only",
            "manual_readback",
            "submit_once",
            "recovery_readback",
            "sitemap_operation_mode",
            "sitemap_action_taken",
            "not_found",
            "只授权公网检查与精确 GSC Sitemaps list/get 回读",
            "不能替代 Sitemaps list/get 回读",
        ):
            self.assertIn(required, combined)

    def test_output_cases_cover_provider_and_claim_failures(self) -> None:
        payload = json.loads((ROOT / "evals" / "output_cases.json").read_text(encoding="utf-8"))
        ids = {case["id"] for case in payload["cases"]}
        self.assertTrue(
            {
                "only_ga4_requested",
                "production_positive_preview_negative",
                "consent_decision_missing",
                "ga4_request_without_provider_readback",
                "clarity_collect_without_recording",
                "existing_resources_resume",
                "provider_saved_public_dns_pending",
                "sitemap_submitted_processing",
                "sitemap_status_only_missing",
                "sitemap_manual_submit_readback",
                "sitemap_explicit_onboarding_missing",
                "sitemap_submit_interrupted_readback",
                "external_account_mismatch",
                "destructive_cleanup_after_success",
                "local_tests_only",
                "google_api_readback_does_not_enable_services",
                "google_api_generic_403_unknown",
                "gsc_plan_security_failure",
                "gsc_api_submit_ambiguous",
                "ga4_create_ambiguous_never_replayed",
                "ga4_realtime_api_without_debugview",
                "browser_api_evidence_conflict",
                "secret_redaction_provider_error",
                "seo_analysis_never_invokes_google_adapter",
                "browser_fallback_permission_boundary",
                "gsc_search_analytics_read_only_boundary",
                "first_readiness_before_configuration",
                "readiness_partial_configuration_plan",
            }.issubset(ids)
        )

    def test_trigger_cases_cover_sitemap_status_and_manual_readback(self) -> None:
        payload = json.loads((ROOT / "evals" / "trigger_cases.json").read_text(encoding="utf-8"))
        families = {case["family"] for case in payload["should_trigger"]}
        self.assertTrue(
            {
                "cn_gsc_sitemap_status_readonly",
                "cn_gsc_manual_submit_readback",
                "en_gsc_sitemap_status_readonly",
                "cn_gsc_search_analytics_readback",
                "cn_first_telemetry_readiness_plan",
            }.issubset(families)
        )

    def test_official_sources_are_primary_and_current(self) -> None:
        sources = (ROOT / "references" / "official-sources.md").read_text(encoding="utf-8")
        for required in (
            "developers.google.com/tag-platform/gtagjs",
            "support.google.com/analytics/answer/9271392",
            "clarity/setup-and-installation/clarity-consent-api-v2",
            "support.google.com/webmasters/answer/9008080",
            "developers.google.com/search/docs/crawling-indexing/sitemaps/overview",
            "analyticsadmin/v1beta/analyticsadmin-api.json",
            "analyticsdata/v1beta/analyticsdata-api.json",
            "searchconsole/v1/searchconsole-api.json",
            "developers.google.com/webmaster-tools/v1/searchanalytics/query",
            "20260819",
            "Checked on 2026-08-20",
        ):
            self.assertIn(required, sources)


if __name__ == "__main__":
    unittest.main()
