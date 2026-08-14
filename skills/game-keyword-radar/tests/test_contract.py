from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SkillContractTest(unittest.TestCase):
    def test_root_is_the_only_skill_entrypoint(self) -> None:
        entrypoints = sorted(path.relative_to(ROOT) for path in ROOT.rglob("SKILL.md"))
        self.assertEqual(entrypoints, [Path("SKILL.md")])

    def test_browser_and_evidence_guardrails_are_documented(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "不读取、导出、复制或保存 Cookie",
            "CAPTCHA 出现时必须停下",
            "没有展示的字段留空，不估算",
            "Output Contract",
        ):
            self.assertIn(required, skill)

    def test_wrapper_uses_an_overridable_project_path(self) -> None:
        wrapper = (ROOT / "scripts" / "run-radar.sh").read_text(encoding="utf-8")
        self.assertIn("GAME_KEYWORD_RADAR_PROJECT_DIR", wrapper)
        self.assertIn('exec npm --prefix "$project_dir" run radar', wrapper)

    def test_gpts_comparison_is_reference_by_default(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        workflow = (ROOT / "references" / "workflow.md").read_text(encoding="utf-8")
        self.assertIn("该对比仅作参考", skill)
        self.assertIn("高于、相等、低于或缺失都不参与评分", skill)
        self.assertIn("都不参与评分、缺失判断或候选状态", workflow)


if __name__ == "__main__":
    unittest.main()
