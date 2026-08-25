import json
from pathlib import Path
import unittest


PIPELINE_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PIPELINE_ROOT.parent

STAGE_SKILLS = {
    "web-business-lock": ("production", "candidate-lock.json", "1.0.0", ">=1.0.0"),
    "web-business-planner": ("production", "page-matrix.json", "1.0.0", ">=1.0.0"),
    "web-business-evidence": ("production", "evidence-pack.json", "1.0.0", ">=1.0.0"),
    "web-business-builder": ("production", "content-manifest.json", "1.0.0", ">=1.0.0"),
    "web-business-qa": ("production", "launch-report.json", "1.0.0", ">=1.0.0"),
    "web-business-launch": ("governed", "http_readback", "1.0.0", ">=1.0.0"),
    "web-business-telemetry": ("governed", "analytics-snapshot.json", "1.0.0", ">=1.0.0"),
    "web-business-growth": ("production", "grow", "1.0.0", ">=1.0.0"),
    "web-business-templater": ("production", "template_readiness", "1.0.0", ">=1.0.0"),
    "web-business-expander": ("production", "优化现有页面", "1.0.0", ">=1.0.0"),
}


class StageSkillSuiteTest(unittest.TestCase):
    def test_all_stage_packages_share_the_central_contract(self) -> None:
        for name, (tier, owned_marker, version, pipeline_version) in STAGE_SKILLS.items():
            with self.subTest(skill=name):
                root = SKILLS_ROOT / name
                self.assertTrue((root / "SKILL.md").is_file())
                entrypoints = sorted(path.relative_to(root) for path in root.rglob("SKILL.md"))
                self.assertEqual(entrypoints, [Path("SKILL.md")])
                self.assertLessEqual(len(name.split("-")), 3)

                manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["name"], name)
                self.assertEqual(manifest["version"], version)
                self.assertEqual(manifest["owner"], "Nemo")
                self.assertEqual(manifest["maturity_tier"], tier)
                self.assertEqual(
                    manifest["dependencies"],
                    [
                        {
                            "skill": "web-business-pipeline",
                            "version": pipeline_version,
                            "required": True,
                        }
                    ],
                )

                skill = (root / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("WEB_BUSINESS_PIPELINE_SKILL_DIR", skill)
                self.assertIn("不得直接编辑 `pipeline-state.json`", skill)
                self.assertIn(owned_marker, skill)
                self.assertFalse((root / "scripts").exists(), "stage packages must not copy the central CLI")

    def test_generated_trigger_evidence_passes_for_every_stage(self) -> None:
        for name in STAGE_SKILLS:
            with self.subTest(skill=name):
                report = json.loads(
                    (SKILLS_ROOT / name / "reports" / "trigger-eval.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertTrue(report["ok"])
                self.assertEqual(report["summary"]["passed"], report["summary"]["total"])
                self.assertGreaterEqual(report["summary"]["total"], 10)

    def test_parent_router_lists_every_stage(self) -> None:
        route = (PIPELINE_ROOT / "references" / "skill-suite.md").read_text(encoding="utf-8")
        for name in STAGE_SKILLS:
            with self.subTest(skill=name):
                self.assertIn(f"`{name}`", route)
        self.assertIn("优化现有页面", route)
        self.assertIn("新增页面", route)
        self.assertIn("批次大小不使用固定页数阈值", route)
        self.assertIn("grow -> observing", route)

    def test_high_risk_and_manual_quality_boundaries_are_explicit(self) -> None:
        launch = (SKILLS_ROOT / "web-business-launch" / "SKILL.md").read_text(encoding="utf-8")
        telemetry = (SKILLS_ROOT / "web-business-telemetry" / "SKILL.md").read_text(encoding="utf-8")
        expander = (SKILLS_ROOT / "web-business-expander" / "SKILL.md").read_text(encoding="utf-8")
        templater = (SKILLS_ROOT / "web-business-templater" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("逐项授权", launch)
        self.assertIn("授权记录都不能冒充", launch)
        self.assertIn("Google Indexing API", telemetry)
        self.assertIn("每个变更页都完成人工审核", expander)
        self.assertIn("三层", templater)
        self.assertIn("substitution test", templater)

    def test_commercial_validation_layer_is_shared_and_bounded(self) -> None:
        reference = (PIPELINE_ROOT / "references" / "commercial-validation.md").read_text(
            encoding="utf-8"
        )
        pipeline = (PIPELINE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        growth_rules = (PIPELINE_ROOT / "references" / "growth-rules.md").read_text(
            encoding="utf-8"
        )
        candidate = (SKILLS_ROOT / "web-business-lock" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        planner = (SKILLS_ROOT / "web-business-planner" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        telemetry = (SKILLS_ROOT / "web-business-telemetry" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        growth = (SKILLS_ROOT / "web-business-growth" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        expander = (SKILLS_ROOT / "web-business-expander" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("references/commercial-validation.md", pipeline)
        self.assertIn("commercial-validation.md", growth_rules)
        self.assertIn("$1K / $10K / $100K", reference)
        self.assertIn("当生命周期硬门槛", reference)
        self.assertIn("商业模式假设", candidate)
        self.assertIn("business_hypothesis", candidate)
        self.assertIn("`page_type`、`search_intent`、`user_goal`、`allowed_actions` 和 `non_goals`", planner)
        self.assertIn("`ga.metrics`", telemetry)
        self.assertIn("`search_growth`、`conversion_learning`、`commercial_scale`", growth)
        self.assertIn("`funnel_stage`", expander)
        self.assertIn("`primary_success_metric`", expander)

        cli = (PIPELINE_ROOT / "scripts" / "pipeline.py").read_text(encoding="utf-8")
        self.assertIn("SCHEMA_VERSION = 2", cli)
        self.assertNotIn("platform_ids", cli)
        self.assertNotIn("redeem_code", cli)
        self.assertNotIn("commercial_validated", cli)


if __name__ == "__main__":
    unittest.main()
