import argparse
import copy
from contextlib import redirect_stdout
import hashlib
import importlib.util
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("game_site_pipeline", ROOT / "scripts" / "pipeline.py")
assert SPEC and SPEC.loader
pipeline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pipeline)

NOW = "2026-08-07T00:00:00Z"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def call_silently(function, args: argparse.Namespace) -> int:
    with redirect_stdout(StringIO()):
        return function(args)


def candidate(platform: str = "steam", platform_id: str = "123") -> dict:
    return {
        "key": "game:test-game",
        "name": "Test Game",
        "source_report": "radar-report.md",
        "qualification": {
            "trends_status": "rising",
            "semrush_database": "us",
            "semrush_volume": 1200,
            "semrush_kd": 22,
            "long_tail_count": 14,
            "serp_status": "mixed",
            "reliable_source_count": 3,
        },
        "platform_ids": [{"platform": platform, "id": platform_id}],
    }


def page_matrix() -> dict:
    return {
        "schema_version": 1,
        "candidate_key": "game:test-game",
        "base_locale": "en-US",
        "locales": [
            {
                "locale": "en-US",
                "demand_validated": True,
                "demand_evidence": ["locked candidate"],
                "content_complete": True,
            }
        ],
        "pages": [
            {
                "page_id": "codes",
                "slug": "test-game-codes",
                "page_type": "codes",
                "locale": "en-US",
                "primary_keyword": "test game codes",
                "keyword_aliases": ["codes for test game"],
                "intent_key": "test-game-current-codes",
                "search_intent": "find current codes",
                "user_goal": "copy a verified current code",
                "allowed_fields": ["code", "status", "source"],
                "allowed_actions": ["copy_code"],
                "allowed_states": ["active", "expired"],
                "non_goals": ["generate codes"],
            }
        ],
    }


def evidence_pack(two_sources: bool = True) -> dict:
    sources = [
        {
            "source_id": "official",
            "url": "https://official.example/codes",
            "title": "Official codes",
            "source_type": "official_page",
            "reliability": "official",
            "retrieved_at": NOW,
            "current_as_of": NOW,
        }
    ]
    if two_sources:
        sources.append(
            {
                "source_id": "trusted",
                "url": "https://trusted.example/codes",
                "title": "Trusted code check",
                "source_type": "guide",
                "reliability": "trusted",
                "retrieved_at": NOW,
                "current_as_of": NOW,
            }
        )
    return {
        "schema_version": 1,
        "candidate_key": "game:test-game",
        "sources": sources,
        "page_evidence": [
            {
                "page_id": "codes",
                "source_ids": [source["source_id"] for source in sources],
            }
        ],
        "claims": [
            {
                "claim_id": "current-code",
                "page_id": "codes",
                "text": "TESTCODE is currently active",
                "claim_type": "redeem_code",
                "source_ids": ["official"],
                "status": "verified",
                "verified_at": NOW,
            }
        ],
    }


def content_manifest(project_dir: Path, text: str = "TESTCODE is currently active") -> dict:
    content_path = project_dir / "content" / "codes.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text(text, encoding="utf-8")
    digest = hashlib.sha256(content_path.read_bytes()).hexdigest()
    return {
        "schema_version": 1,
        "candidate_key": "game:test-game",
        "pages": [
            {
                "page_id": "codes",
                "path": "content/codes.md",
                "title": "Test Game Codes",
                "locale": "en-US",
                "primary_keyword": "test game codes",
                "status": "reviewed",
                "source_ids": ["official", "trusted"],
                "claim_ids": ["current-code"],
                "content_sha256": digest,
                "human_reviewed": True,
                "reviewed_by": "Nemo",
                "reviewed_at": NOW,
            }
        ],
    }


def launch_report(deployed: bool = False, auth_id: str | None = None) -> dict:
    checks = [
        {"name": name, "status": "passed", "command": f"check {name}", "evidence": "passed in test"}
        for name in sorted(pipeline.REQUIRED_LOCAL_CHECKS)
    ]
    return {
        "schema_version": 1,
        "candidate_key": "game:test-game",
        "site_identity": {
            "canonical_origin": "https://new.example",
            "forbidden_origins": ["https://old.example"],
        },
        "local_checks": checks,
        "external_actions": [
            {
                "action": "deployment",
                "status": "verified" if deployed else "planned",
                "authorization_id": auth_id,
                "evidence": "provider and HTTP records" if deployed else None,
            }
        ],
        "deployment": {
            "status": "verified" if deployed else "not_started",
            "url": "https://new.example" if deployed else None,
            "provider": "test-provider" if deployed else None,
            "source_revision": "abc123" if deployed else None,
            "authorization_id": auth_id,
            "deployed_at": NOW if deployed else None,
        },
        "http_readback": {
            "status": "passed" if deployed else "not_run",
            "url": "https://new.example" if deployed else None,
            "status_code": 200 if deployed else None,
            "checked_at": NOW if deployed else None,
        },
        "rollback": {"documented": True, "procedure": "restore the prior test revision and read back"},
    }


def analytics_snapshot(decision: str = "none", data_status: str = "no_valid_data") -> dict:
    metrics = {"clicks": 1, "impressions": 10, "indexed_pages": 1} if data_status == "valid" else {}
    return {
        "schema_version": 1,
        "candidate_key": "game:test-game",
        "snapshot_at": NOW,
        "site_url": "https://new.example",
        "gsc": {
            "setup_status": "verified",
            "setup_mode": "existing",
            "property": "sc-domain:new.example",
            "authorization_id": None,
            "readback_at": NOW,
            "data_status": data_status,
            "period": {"start": "2026-08-01", "end": "2026-08-07"},
            "metrics": metrics,
        },
        "ga": {
            "setup_status": "verified",
            "setup_mode": "existing",
            "property": "properties/123",
            "authorization_id": None,
            "readback_at": NOW,
            "data_status": "valid",
            "period": {"start": "2026-08-01", "end": "2026-08-07"},
            "metrics": {"sessions": 2},
        },
        "indexing": {
            "checked_at": NOW,
            "sitemap_url": "https://new.example/sitemap.xml",
            "indexed_pages": 0,
            "evidence": "GSC pages report",
        },
        "observation": {
            "day": 0,
            "next_review_dates": ["2026-08-14T00:00:00Z", "2026-08-21T00:00:00Z"],
            "technical_checks": [
                {"name": "sitemap", "status": "passed", "evidence": "HTTP 200"}
            ],
        },
        "decision": {
            "recommendation": decision,
            "rationale": "test evidence decision" if decision != "none" else None,
            "approved_by": "Nemo" if decision != "none" else None,
            "approved_at": NOW if decision != "none" else None,
        },
        "template_readiness": {
            "approved": False,
            "reusable_scope": None,
            "product_specific_exclusions": None,
            "approved_by": None,
            "approved_at": None,
        },
    }


class PipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def init_project(self, project_name: str = "project", candidate_data: dict | None = None) -> Path:
        project_dir = self.root / project_name
        candidate_file = self.root / f"{project_name}-candidate.json"
        write_json(candidate_file, candidate_data or candidate())
        args = argparse.Namespace(
            project_dir=project_dir,
            candidate_file=candidate_file,
            approved_by="Nemo",
            confirm_key=(candidate_data or candidate())["key"],
            rationale="human approved test candidate",
        )
        self.assertEqual(call_silently(pipeline.cmd_init, args), 0)
        return project_dir

    def set_stage(self, project_dir: Path, stage: str) -> None:
        state_path = project_dir / "pipeline-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["current_stage"] = stage
        state["updated_at"] = NOW
        state["history"].append(
            {"event": "transition", "from": "test", "to": stage, "at": NOW, "actor": "test", "reason": "fixture"}
        )
        write_json(state_path, state)

    def populate_through_local(self, project_dir: Path, page_text: str = "TESTCODE is active") -> None:
        write_json(project_dir / "page-matrix.json", page_matrix())
        write_json(project_dir / "evidence-pack.json", evidence_pack())
        write_json(project_dir / "content-manifest.json", content_manifest(project_dir, page_text))
        write_json(project_dir / "launch-report.json", launch_report())

    def grant_deployment(self, project_dir: Path) -> str:
        args = argparse.Namespace(
            project_dir=project_dir,
            action="deployment",
            confirm="deployment",
            granted_by="Nemo",
            scope="test deployment only",
            user_instruction="deploy this test revision",
            expires_at=None,
        )
        self.assertEqual(call_silently(pipeline.cmd_authorize, args), 0)
        state = json.loads((project_dir / "pipeline-state.json").read_text(encoding="utf-8"))
        return state["authorizations"][-1]["authorization_id"]

    def test_qualified_candidate_initializes_and_is_immutable(self) -> None:
        project_dir = self.init_project()
        result = pipeline.validate_project(project_dir)
        self.assertTrue(result["ok"], result["errors"])
        lock_path = project_dir / "candidate-lock.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        lock["name"] = "Changed Name"
        write_json(lock_path, lock)
        result = pipeline.validate_project(project_dir)
        self.assertIn("candidate-lock.json changed after initialization", result["errors"])

    def test_init_requires_exact_human_confirmation(self) -> None:
        project_dir = self.root / "wrong-confirm"
        candidate_file = self.root / "candidate.json"
        write_json(candidate_file, candidate())
        args = argparse.Namespace(
            project_dir=project_dir,
            candidate_file=candidate_file,
            approved_by="Nemo",
            confirm_key="game:another-game",
            rationale="not enough",
        )
        self.assertEqual(call_silently(pipeline.cmd_init, args), 2)
        self.assertFalse((project_dir / "candidate-lock.json").exists())

    def test_example_candidate_is_rejected(self) -> None:
        example = candidate()
        example["example_only"] = True
        candidate_file = self.root / "example.json"
        write_json(candidate_file, example)
        args = argparse.Namespace(
            project_dir=self.root / "example-project",
            candidate_file=candidate_file,
            approved_by="Nemo",
            confirm_key=example["key"],
            rationale="test",
        )
        self.assertEqual(call_silently(pipeline.cmd_init, args), 2)

    def test_researched_gate_requires_two_sources(self) -> None:
        project_dir = self.init_project()
        write_json(project_dir / "page-matrix.json", page_matrix())
        write_json(project_dir / "evidence-pack.json", evidence_pack(two_sources=False))
        self.set_stage(project_dir, "planned")
        result = pipeline.gate_project(project_dir, "researched")
        self.assertFalse(result["ok"])
        self.assertTrue(any("at least two distinct sources" in error for error in result["errors"]))

    def test_keyword_cannibalization_blocks_planning(self) -> None:
        project_dir = self.init_project()
        matrix = page_matrix()
        duplicate = copy.deepcopy(matrix["pages"][0])
        duplicate["page_id"] = "guide"
        duplicate["slug"] = "test-game-guide"
        duplicate["intent_key"] = "different-intent-key"
        duplicate["primary_keyword"] = "test game guide"
        duplicate["keyword_aliases"] = ["test game codes"]
        matrix["pages"].append(duplicate)
        write_json(project_dir / "page-matrix.json", matrix)
        result = pipeline.gate_project(project_dir, "planned")
        self.assertFalse(result["ok"])
        self.assertTrue(any("keyword cannibalization" in error for error in result["errors"]))

    def test_same_name_platform_identity_remains_distinct(self) -> None:
        steam_dir = self.init_project("steam", candidate("steam", "111"))
        roblox_dir = self.init_project("roblox", candidate("roblox", "222"))
        steam_state = json.loads((steam_dir / "pipeline-state.json").read_text(encoding="utf-8"))
        roblox_state = json.loads((roblox_dir / "pipeline-state.json").read_text(encoding="utf-8"))
        self.assertEqual(steam_state["candidate_key"], roblox_state["candidate_key"])
        self.assertNotEqual(steam_state["candidate_identity"], roblox_state["candidate_identity"])

    def test_old_domain_residue_blocks_local_verification(self) -> None:
        project_dir = self.init_project()
        self.populate_through_local(project_dir, "See https://old.example/codes")
        self.set_stage(project_dir, "build_ready")
        result = pipeline.gate_project(project_dir, "local_verified")
        self.assertFalse(result["ok"])
        self.assertTrue(any("old-domain residue" in error for error in result["errors"]))

    def test_batch_expansion_requires_five_human_reviews(self) -> None:
        project_dir = self.init_project()
        matrix = page_matrix()
        evidence = evidence_pack()
        manifest = content_manifest(project_dir)
        for index in range(1, 6):
            page_id = f"guide-{index}"
            matrix_page = copy.deepcopy(matrix["pages"][0])
            matrix_page.update(
                {
                    "page_id": page_id,
                    "slug": f"test-game-guide-{index}",
                    "primary_keyword": f"test game guide {index}",
                    "keyword_aliases": [],
                    "intent_key": f"test-game-guide-{index}",
                }
            )
            matrix["pages"].append(matrix_page)
            evidence["page_evidence"].append(
                {"page_id": page_id, "source_ids": ["official", "trusted"]}
            )
            page_path = project_dir / "content" / f"guide-{index}.md"
            page_path.write_text(f"Guide {index}", encoding="utf-8")
            manifest["pages"].append(
                {
                    "page_id": page_id,
                    "path": f"content/guide-{index}.md",
                    "title": f"Test Game Guide {index}",
                    "locale": "en-US",
                    "primary_keyword": f"test game guide {index}",
                    "status": "reviewed",
                    "source_ids": ["official", "trusted"],
                    "claim_ids": [],
                    "content_sha256": hashlib.sha256(page_path.read_bytes()).hexdigest(),
                    "human_reviewed": index < 4,
                    "reviewed_by": "Nemo" if index < 4 else None,
                    "reviewed_at": NOW if index < 4 else None,
                }
            )
        write_json(project_dir / "page-matrix.json", matrix)
        write_json(project_dir / "evidence-pack.json", evidence)
        write_json(project_dir / "content-manifest.json", manifest)
        write_json(project_dir / "launch-report.json", launch_report())
        self.set_stage(project_dir, "build_ready")
        result = pipeline.gate_project(project_dir, "local_verified")
        self.assertFalse(result["ok"])
        self.assertTrue(any("requires 5 pages" in error for error in result["errors"]))

        manifest["pages"][4]["human_reviewed"] = True
        manifest["pages"][4]["reviewed_by"] = "Nemo"
        manifest["pages"][4]["reviewed_at"] = NOW
        write_json(project_dir / "content-manifest.json", manifest)
        result = pipeline.gate_project(project_dir, "local_verified")
        self.assertTrue(result["ok"], result["errors"])

    def test_deployment_requires_active_matching_authorization(self) -> None:
        project_dir = self.init_project()
        self.populate_through_local(project_dir)
        write_json(project_dir / "launch-report.json", launch_report(deployed=True, auth_id="auth-000000000000"))
        self.set_stage(project_dir, "deploy_ready")
        result = pipeline.gate_project(project_dir, "deployed")
        self.assertFalse(result["ok"])
        self.assertTrue(any("unknown authorization" in error for error in result["errors"]))

    def test_authorized_deployment_passes_with_readback(self) -> None:
        project_dir = self.init_project()
        self.populate_through_local(project_dir)
        auth_id = self.grant_deployment(project_dir)
        write_json(project_dir / "launch-report.json", launch_report(deployed=True, auth_id=auth_id))
        self.set_stage(project_dir, "deploy_ready")
        result = pipeline.gate_project(project_dir, "deployed")
        self.assertTrue(result["ok"], result["errors"])

    def test_no_gsc_data_blocks_grow_and_retire(self) -> None:
        project_dir = self.init_project()
        self.populate_through_local(project_dir)
        auth_id = self.grant_deployment(project_dir)
        write_json(project_dir / "launch-report.json", launch_report(deployed=True, auth_id=auth_id))
        self.set_stage(project_dir, "observing")
        for target in ("grow", "retire"):
            write_json(project_dir / "analytics-snapshot.json", analytics_snapshot(target, "no_valid_data"))
            result = pipeline.gate_project(project_dir, target)
            self.assertFalse(result["ok"])
            self.assertTrue(
                any(f"cannot enter {target} without valid GSC data" in error for error in result["errors"]),
                result["errors"],
            )

    def test_no_gsc_data_can_hold_with_day_7_and_day_14_reviews(self) -> None:
        project_dir = self.init_project()
        self.populate_through_local(project_dir)
        auth_id = self.grant_deployment(project_dir)
        write_json(project_dir / "launch-report.json", launch_report(deployed=True, auth_id=auth_id))
        write_json(project_dir / "analytics-snapshot.json", analytics_snapshot("hold", "no_valid_data"))
        self.set_stage(project_dir, "observing")
        result = pipeline.gate_project(project_dir, "hold")
        self.assertTrue(result["ok"], result["errors"])
        self.assertTrue(any("missing evidence" in warning for warning in result["warnings"]))

    def test_sensitive_claim_needs_current_trusted_source(self) -> None:
        project_dir = self.init_project()
        write_json(project_dir / "page-matrix.json", page_matrix())
        evidence = evidence_pack()
        evidence["sources"][0]["current_as_of"] = None
        evidence["sources"][1]["reliability"] = "community"
        evidence["claims"][0]["source_ids"] = ["official", "trusted"]
        write_json(project_dir / "evidence-pack.json", evidence)
        self.set_stage(project_dir, "planned")
        result = pipeline.gate_project(project_dir, "researched")
        self.assertFalse(result["ok"])
        self.assertTrue(any("current official or trusted source" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
