import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TelemetrySkillContractTest(unittest.TestCase):
    def test_provider_and_no_data_boundaries_are_explicit(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "setup_mode: existing",
            "gsc_setup",
            "ga_setup",
            "Google Indexing API",
            "第 7 天和第 14 天",
            "不得填造 clicks",
        ):
            self.assertIn(required, skill)

    def test_manifest_requires_central_pipeline_and_governed_gates(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["maturity_tier"], "governed")
        self.assertEqual(
            manifest["dependencies"],
            [{"skill": "web-business-pipeline", "version": ">=1.0.0", "required": True}],
        )
        self.assertIn("explicit_external_authorization", manifest["release_gates"])
        self.assertIn("provider_readback", manifest["release_gates"])

    def test_output_cases_cover_material_telemetry_failures(self) -> None:
        payload = json.loads((ROOT / "evals" / "output_cases.json").read_text(encoding="utf-8"))
        ids = {case["id"] for case in payload["cases"]}
        self.assertEqual(
            ids,
            {
                "existing_property_needs_readback_not_creation_claim",
                "created_properties_need_separate_authorization",
                "no_data_schedules_reviews",
                "indexing_is_not_performance",
                "review_cycle_returns_to_observing",
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
