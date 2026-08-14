import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LaunchSkillContractTest(unittest.TestCase):
    def test_governed_action_boundaries_are_explicit(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "domain_purchase",
            "dns_change",
            "git_push",
            "deployment",
            "独立授权、实际执行和真实回读",
            "不读取、复制、打印或保存 token",
            "保持",
        ):
            self.assertIn(required, skill)

    def test_manifest_requires_central_pipeline_and_governed_gates(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["maturity_tier"], "governed")
        self.assertEqual(
            manifest["dependencies"],
            [{"skill": "game-site-pipeline", "version": ">=0.2.0", "required": True}],
        )
        self.assertIn("explicit_external_authorization", manifest["release_gates"])
        self.assertIn("provider_readback", manifest["release_gates"])

    def test_output_cases_cover_material_launch_failures(self) -> None:
        payload = json.loads((ROOT / "evals" / "output_cases.json").read_text(encoding="utf-8"))
        ids = {case["id"] for case in payload["cases"]}
        self.assertEqual(
            ids,
            {
                "blanket_authorization_is_rejected",
                "deployment_needs_matching_authorization",
                "facts_remain_separate",
                "partial_failure_preserves_state",
                "expansion_relaunch_stays_grow",
            },
        )
        self.assertFalse(payload["provider_backed"])
        self.assertFalse(payload["human_review"])

    def test_behavior_report_does_not_claim_provider_or_human_evidence(self) -> None:
        evidence = json.loads((ROOT / "reports" / "output-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["evidence_kind"], "behavior_specification")
        self.assertFalse(evidence["provider_backed"])
        self.assertFalse(evidence["human_blind_review"])
        self.assertTrue(evidence["missing_evidence"])


if __name__ == "__main__":
    unittest.main()
