import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SkillContractTest(unittest.TestCase):
    def test_package_has_one_discoverable_entrypoint(self) -> None:
        entries = [path.relative_to(ROOT).as_posix() for path in ROOT.rglob("SKILL.md")]
        self.assertEqual(entries, ["SKILL.md"])

    def test_required_governed_artifacts_exist(self) -> None:
        required = (
            "README.md",
            "LICENSE",
            "manifest.json",
            "agents/interface.yaml",
            "templates/launch-report.template.json",
            "evals/trigger_cases.json",
            "evals/output_cases.json",
            "reports/prior-art-research.md",
            "reports/output-eval.json",
            "reports/output-evidence.json",
            "reports/creation-handoff.md",
        )
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_skill_preserves_permission_and_evidence_boundaries(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "pages_deploy",
            "vercel_deploy",
            "custom_domain_binding",
            "dns_record_change",
            "nameserver_change",
            "dnssec_change",
            "agents_md_writeback",
            "formal_domain_before",
            "按 ID、类型、名称、内容精确匹配",
            "至少两个验证递归解析器返回 `ad`",
            "不直接篡改其中央状态",
        ):
            self.assertIn(required, skill)
        self.assertIn("provider 状态、公共 dns、https 内容、本机缓存", skill.lower())

    def test_manifest_declares_governed_release_gates(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "nemo-domain-launch")
        self.assertEqual(manifest["version"], "0.2.0")
        self.assertEqual(manifest["owner"], "Nemo")
        self.assertEqual(manifest["maturity_tier"], "governed")
        for gate in (
            "formal_domain_absence",
            "deployment_mode_routing",
            "exact_external_authorization",
            "dns_before_snapshot",
            "vercel_live_dns_values",
            "dnssec_migration_order",
            "multi_resolver_public_dns_readback",
            "agents_md_writeback",
            "public_claim_guard",
            "secret_scan",
        ):
            self.assertIn(gate, manifest["release_gates"])

    def test_entry_surfaces_share_the_first_domain_dual_route_contract(self) -> None:
        for relative in ("SKILL.md", "README.md", "agents/interface.yaml", "manifest.json"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertIn("static_pages", text)
                self.assertIn("saas_vercel", text)
                self.assertIn("AGENTS.md", text)
                self.assertNotIn("qiaomu-cf-launch", text)

    def test_output_evidence_does_not_overclaim(self) -> None:
        evidence = json.loads((ROOT / "reports" / "output-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["evidence_kind"], "recorded_fixture")
        self.assertTrue(evidence["ok"])
        self.assertFalse(evidence["provider_backed"])
        self.assertFalse(evidence["human_blind_review"])
        self.assertIn("provider-backed comparison", evidence["missing_evidence"])
        self.assertIn("human blind review", evidence["missing_evidence"])


if __name__ == "__main__":
    unittest.main()
