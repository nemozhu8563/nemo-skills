import json
from pathlib import Path
import unittest


PIPELINE_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PIPELINE_ROOT.parent

STAGE_SKILLS = {
    "game-candidate-lock": ("production", "candidate-lock.json"),
    "game-site-planner": ("production", "page-matrix.json"),
    "game-site-evidence": ("production", "evidence-pack.json"),
    "game-site-builder": ("production", "content-manifest.json"),
    "game-site-qa": ("production", "launch-report.json"),
    "game-site-launch": ("governed", "http_readback"),
    "game-site-telemetry": ("governed", "analytics-snapshot.json"),
    "game-site-growth": ("production", "grow"),
    "game-site-templater": ("production", "template_readiness"),
    "game-page-expander": ("production", "首批五页"),
}


class StageSkillSuiteTest(unittest.TestCase):
    def test_all_stage_packages_share_the_central_contract(self) -> None:
        for name, (tier, owned_marker) in STAGE_SKILLS.items():
            with self.subTest(skill=name):
                root = SKILLS_ROOT / name
                self.assertTrue((root / "SKILL.md").is_file())
                entrypoints = sorted(path.relative_to(root) for path in root.rglob("SKILL.md"))
                self.assertEqual(entrypoints, [Path("SKILL.md")])
                self.assertLessEqual(len(name.split("-")), 3)

                manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["name"], name)
                self.assertEqual(manifest["version"], "0.1.0")
                self.assertEqual(manifest["owner"], "Nemo")
                self.assertEqual(manifest["maturity_tier"], tier)
                self.assertEqual(
                    manifest["dependencies"],
                    [{"skill": "game-site-pipeline", "version": ">=0.2.0", "required": True}],
                )

                skill = (root / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("GAME_SITE_PIPELINE_SKILL_DIR", skill)
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
        self.assertIn("至少 10 个候选内页", route)
        self.assertIn("grow -> observing", route)

    def test_high_risk_and_manual_quality_boundaries_are_explicit(self) -> None:
        launch = (SKILLS_ROOT / "game-site-launch" / "SKILL.md").read_text(encoding="utf-8")
        telemetry = (SKILLS_ROOT / "game-site-telemetry" / "SKILL.md").read_text(encoding="utf-8")
        expander = (SKILLS_ROOT / "game-page-expander" / "SKILL.md").read_text(encoding="utf-8")
        templater = (SKILLS_ROOT / "game-site-templater" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("逐项授权", launch)
        self.assertIn("授权记录都不能冒充", launch)
        self.assertIn("Google Indexing API", telemetry)
        self.assertIn("首批五页审核", expander)
        self.assertIn("三层", templater)
        self.assertIn("substitution test", templater)


if __name__ == "__main__":
    unittest.main()
