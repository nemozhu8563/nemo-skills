import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SkillContractTest(unittest.TestCase):
    def test_root_is_the_only_skill_entrypoint(self) -> None:
        entrypoints = sorted(path.relative_to(ROOT) for path in ROOT.rglob("SKILL.md"))
        self.assertEqual(entrypoints, [Path("SKILL.md")])

    def test_governed_boundaries_are_explicit(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "不把“可进入复核”偷换成“已批准候选”",
            "同义词或 intent key 被两个页面占用时停止",
            "域名购买、DNS 修改、Git 推送、部署、创建 GSC、创建 GA、广告申请",
            "不得进入 `grow` 或 `retire`",
            "不使用 Google Indexing API",
        ):
            self.assertIn(required, skill)

    def test_json_contract_files_parse(self) -> None:
        paths = [
            *ROOT.joinpath("schemas").glob("*.json"),
            *ROOT.joinpath("templates").glob("*.json"),
            *ROOT.joinpath("evals").rglob("*.json"),
            ROOT / "manifest.json",
        ]
        self.assertGreaterEqual(len(paths), 15)
        for path in paths:
            with self.subTest(path=path):
                parsed = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsInstance(parsed, dict)

    def test_cli_has_no_network_client(self) -> None:
        cli = (ROOT / "scripts" / "pipeline.py").read_text(encoding="utf-8")
        for forbidden in ("import requests", "import urllib", "httpx", "subprocess.run"):
            self.assertNotIn(forbidden, cli)

    def test_output_eval_covers_material_failures(self) -> None:
        output_cases = json.loads((ROOT / "evals" / "output_cases.json").read_text(encoding="utf-8"))
        case_ids = {case["id"] for case in output_cases["cases"]}
        self.assertTrue(
            {
                "candidate_requires_human_confirmation",
                "researched_requires_two_sources",
                "same_name_provider_identity_is_distinct",
                "old_domain_blocks_local_verification",
                "change_batch_requires_every_human_review",
                "no_data_blocks_grow_and_retire",
                "deployment_requires_matching_authorization",
                "traffic_without_conversion_is_not_closed_loop",
                "money_milestones_are_not_lifecycle_gates",
            }.issubset(case_ids)
        )


if __name__ == "__main__":
    unittest.main()
