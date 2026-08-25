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
SPEC = importlib.util.spec_from_file_location("web_business_pipeline", ROOT / "scripts" / "pipeline.py")
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


def candidate(provider: str = "internal", identity_id: str = "123") -> dict:
    return {
        "key": "tool:test-tool",
        "name": "Test Tool",
        "source_report": "qualification-report.md",
        "qualification": {
            "status": "qualified",
            "method": "fixture-review",
            "checked_at": NOW,
            "checks": [
                {
                    "check_id": "problem-evidence",
                    "criterion": "A specific customer problem has direct evidence",
                    "status": "passed",
                    "evidence_refs": ["qualification-report.md#problem"],
                    "observations": {},
                }
            ],
        },
        "identities": [{"provider": provider, "id": identity_id}],
        "business_hypothesis": {
            "target_customer": "Small online businesses",
            "customer_problem": "A recurring workflow is slow and error-prone",
            "value_proposition": "A focused web tool completes the workflow with evidence",
            "business_models": ["subscription"],
            "primary_acquisition_channel": "search",
            "primary_value_event": "workflow completed",
            "riskiest_assumption": "The workflow happens often enough to justify payment",
            "unknowns": ["repeat usage"],
        },
    }


def page_matrix() -> dict:
    return {
        "schema_version": 2,
        "candidate_key": "tool:test-tool",
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
                "page_id": "tool",
                "slug": "test-tool",
                "page_type": "utility",
                "locale": "en-US",
                "primary_keyword": "test web tool",
                "keyword_aliases": ["web tool for testing"],
                "intent_key": "test-tool-workflow",
                "search_intent": "complete a focused workflow",
                "user_goal": "complete the workflow with a traceable result",
                "allowed_fields": ["input", "result", "source"],
                "allowed_actions": ["run_tool"],
                "allowed_states": ["ready", "result", "error"],
                "non_goals": ["account login"],
            }
        ],
    }


def evidence_pack(two_sources: bool = True) -> dict:
    sources = [
        {
            "source_id": "official",
            "url": "https://official.example/docs",
            "title": "Official product documentation",
            "source_type": "official_documentation",
            "reliability": "official",
            "retrieved_at": NOW,
            "current_as_of": NOW,
        }
    ]
    if two_sources:
        sources.append(
            {
                "source_id": "trusted",
                "url": "https://trusted.example/review",
                "title": "Independent product review",
                "source_type": "guide",
                "reliability": "trusted",
                "retrieved_at": NOW,
                "current_as_of": NOW,
            }
        )
    return {
        "schema_version": 2,
        "candidate_key": "tool:test-tool",
        "sources": sources,
        "page_evidence": [
            {
                "page_id": "tool",
                "source_ids": [source["source_id"] for source in sources],
            }
        ],
        "claims": [
            {
                "claim_id": "official-link",
                "page_id": "tool",
                "text": "The official documentation is available at the linked URL",
                "claim_type": "official_link",
                "evidence_requirement": "current_trusted",
                "source_ids": ["official"],
                "status": "verified",
                "verified_at": NOW,
            }
        ],
    }


def content_manifest(project_dir: Path, text: str = "The official documentation is linked") -> dict:
    content_path = project_dir / "content" / "tool.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text(text, encoding="utf-8")
    digest = hashlib.sha256(content_path.read_bytes()).hexdigest()
    return {
        "schema_version": 2,
        "candidate_key": "tool:test-tool",
        "pages": [
            {
                "page_id": "tool",
                "path": "content/tool.md",
                "title": "Test Web Tool",
                "locale": "en-US",
                "primary_keyword": "test web tool",
                "status": "reviewed",
                "source_ids": ["official", "trusted"],
                "claim_ids": ["official-link"],
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
        "schema_version": 2,
        "candidate_key": "tool:test-tool",
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
        "schema_version": 2,
        "candidate_key": "tool:test-tool",
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
            confirm_key="tool:another-tool",
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

    def test_qualification_observations_must_be_an_object(self) -> None:
        invalid = candidate()
        invalid["qualification"]["checks"][0]["observations"] = []
        candidate_file = self.root / "invalid-observations.json"
        write_json(candidate_file, invalid)
        args = argparse.Namespace(
            project_dir=self.root / "invalid-observations-project",
            candidate_file=candidate_file,
            approved_by="Nemo",
            confirm_key=invalid["key"],
            rationale="test",
        )
        self.assertEqual(call_silently(pipeline.cmd_init, args), 2)

    def test_saas_candidate_uses_domain_neutral_qualification(self) -> None:
        saas = candidate("internal", "invoice-converter-v1")
        saas["key"] = "saas:invoice-currency-converter"
        saas["name"] = "Invoice Currency Converter"
        saas["business_hypothesis"].update(
            {
                "target_customer": "Cross-border freelancers and small agencies",
                "customer_problem": "Invoices must be converted and documented repeatedly",
                "value_proposition": "Convert invoice currencies with an auditable rate source",
                "business_models": ["subscription", "usage_based"],
                "primary_value_event": "invoice conversion exported",
            }
        )
        project_dir = self.init_project("saas-project", saas)
        lock = json.loads((project_dir / "candidate-lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["key"], "saas:invoice-currency-converter")
        self.assertEqual(lock["qualification"]["method"], "fixture-review")

    def test_lead_generation_candidate_initializes(self) -> None:
        lead = candidate("crm", "smb-owner-training-lead-v1")
        lead["key"] = "service:smb-owner-training"
        lead["name"] = "Small Business Owner Training"
        lead["qualification"] = {
            "status": "qualified",
            "method": "customer-conversation-review",
            "checked_at": NOW,
            "checks": [
                {
                    "check_id": "buyer-problem",
                    "criterion": "Owners describe a recurring training and payment problem",
                    "status": "passed",
                    "evidence_refs": ["interviews.md#owner-3"],
                    "observations": {"interview_count": 5},
                }
            ],
        }
        lead["business_hypothesis"].update(
            {
                "target_customer": "Small business owners and one-person companies",
                "customer_problem": "They need practical operations training and payment setup help",
                "value_proposition": "A focused diagnostic routes qualified owners to the right program",
                "business_models": ["lead_generation", "training"],
                "primary_acquisition_channel": "community",
                "primary_value_event": "qualified consultation request",
                "riskiest_assumption": "Owners will request a paid consultation after the diagnostic",
                "unknowns": ["lead quality", "close rate"],
            }
        )
        project_dir = self.init_project("lead-project", lead)
        result = pipeline.validate_project(project_dir)
        self.assertTrue(result["ok"], result["errors"])

    def test_game_keyword_radar_can_handoff_through_generic_contract(self) -> None:
        game = candidate("steam", "123456")
        game["key"] = "game:arcane-odyssey"
        game["name"] = "Arcane Odyssey"
        game["source_report"] = "game-keyword-radar-report.md"
        game["qualification"] = {
            "status": "qualified",
            "method": "game-keyword-radar-v0.2",
            "checked_at": NOW,
            "checks": [
                {
                    "check_id": "search-opportunity",
                    "criterion": "The game radar's current search-opportunity policy passed",
                    "status": "passed",
                    "evidence_refs": ["game-keyword-radar-report.md#arcane-odyssey"],
                    "observations": {"kd": 24, "long_tail_count": 13},
                }
            ],
        }
        game["business_hypothesis"].update(
            {
                "target_customer": "Players searching for current game help",
                "customer_problem": "Current answers are fragmented across sources",
                "value_proposition": "A focused utility gives sourced, current answers",
                "business_models": ["advertising"],
                "primary_value_event": "utility result viewed",
                "riskiest_assumption": "Search demand persists beyond the launch spike",
                "unknowns": ["retention", "ad eligibility"],
            }
        )
        project_dir = self.init_project("game-radar-project", game)
        lock = json.loads((project_dir / "candidate-lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["qualification"]["method"], "game-keyword-radar-v0.2")
        self.assertEqual(lock["identities"], [{"provider": "steam", "id": "123456"}])

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
        duplicate["slug"] = "test-tool-guide"
        duplicate["intent_key"] = "different-intent-key"
        duplicate["primary_keyword"] = "test tool guide"
        duplicate["keyword_aliases"] = ["test web tool"]
        matrix["pages"].append(duplicate)
        write_json(project_dir / "page-matrix.json", matrix)
        result = pipeline.gate_project(project_dir, "planned")
        self.assertFalse(result["ok"])
        self.assertTrue(any("keyword cannibalization" in error for error in result["errors"]))

    def test_same_name_provider_identity_remains_distinct(self) -> None:
        provider_a_dir = self.init_project("provider-a", candidate("provider-a", "111"))
        provider_b_dir = self.init_project("provider-b", candidate("provider-b", "222"))
        provider_a_state = json.loads(
            (provider_a_dir / "pipeline-state.json").read_text(encoding="utf-8")
        )
        provider_b_state = json.loads(
            (provider_b_dir / "pipeline-state.json").read_text(encoding="utf-8")
        )
        self.assertEqual(provider_a_state["candidate_key"], provider_b_state["candidate_key"])
        self.assertNotEqual(
            provider_a_state["candidate_identity"], provider_b_state["candidate_identity"]
        )

    def test_old_domain_residue_blocks_local_verification(self) -> None:
        project_dir = self.init_project()
        self.populate_through_local(project_dir, "See https://old.example/docs")
        self.set_stage(project_dir, "build_ready")
        result = pipeline.gate_project(project_dir, "local_verified")
        self.assertFalse(result["ok"])
        self.assertTrue(any("old-domain residue" in error for error in result["errors"]))

    def test_human_review_covers_every_page_in_change_batch(self) -> None:
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
                    "slug": f"test-tool-guide-{index}",
                    "primary_keyword": f"test tool guide {index}",
                    "keyword_aliases": [],
                    "intent_key": f"test-tool-guide-{index}",
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
                    "title": f"Test Tool Guide {index}",
                    "locale": "en-US",
                    "primary_keyword": f"test tool guide {index}",
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
        self.assertTrue(
            any(
                "requires every page in the current change batch" in error
                and "guide-4" in error
                and "guide-5" in error
                for error in result["errors"]
            )
        )

        manifest["pages"][4]["human_reviewed"] = True
        manifest["pages"][4]["reviewed_by"] = "Nemo"
        manifest["pages"][4]["reviewed_at"] = NOW
        manifest["pages"][5]["human_reviewed"] = True
        manifest["pages"][5]["reviewed_by"] = "Nemo"
        manifest["pages"][5]["reviewed_at"] = NOW
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

    def test_current_trusted_claim_needs_current_trusted_source(self) -> None:
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
