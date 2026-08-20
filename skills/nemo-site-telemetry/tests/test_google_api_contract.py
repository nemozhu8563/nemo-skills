from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from google_api.output import AdapterError, default_google_api, make_envelope, redact_text, safe_json


def load_adapter():
    path = SCRIPTS / "google_api_adapter.py"
    spec = importlib.util.spec_from_file_location("nemo_google_api_adapter", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


adapter = load_adapter()


class GoogleApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads((SKILL_ROOT / "contracts" / "google-api-output.schema.json").read_text())

    def assert_envelope_contract(self, envelope: dict[str, object]) -> None:
        required = set(self.schema["required"])
        self.assertEqual(required, set(envelope))
        self.assertIn(envelope["status"], self.schema["properties"]["status"]["enum"])
        google_required = set(self.schema["$defs"]["google_api"]["required"])
        self.assertEqual(google_required, set(envelope["google_api"]))
        adapter_pattern = self.schema["$defs"]["google_api"]["properties"]["adapter_version"]["pattern"]
        self.assertRegex(envelope["google_api"]["adapter_version"], re.compile(adapter_pattern))
        if envelope["status"] in {"completed", "verified", "noop"}:
            self.assertIsNone(envelope["error"])
        else:
            self.assertIsInstance(envelope["error"], dict)
            allowed_errors = set(self.schema["$defs"]["error"]["properties"]["error_code"]["enum"])
            self.assertIn(envelope["error"]["error_code"], allowed_errors)
            provider_status = envelope["error"].get("provider_status")
            if isinstance(provider_status, str):
                self.assertRegex(provider_status, re.compile(r"^[A-Z][A-Z0-9_]{0,63}$"))

    def test_schema_and_generated_success_envelope_agree(self) -> None:
        now = datetime(2026, 8, 20, tzinfo=timezone.utc)
        checked_at = "2026-08-20T00:00:00Z"
        envelope = make_envelope(
            "gsc.list-sites",
            "completed",
            clock=lambda: now,
            google_api=default_google_api(checked_at),
            result={"kind": "sites", "count": 0, "items": []},
        )
        self.assert_envelope_contract(envelope)
        serialized = safe_json(envelope)
        self.assertEqual(1, serialized.count("\n"))
        self.assertEqual(envelope, json.loads(serialized))

    def test_search_analytics_result_has_a_strict_contract(self) -> None:
        result_schema = self.schema["$defs"]["result"]
        self.assertIn("search_analytics", result_schema["properties"]["kind"]["enum"])
        row_schema = self.schema["$defs"]["search_analytics_row"]
        self.assertFalse(row_schema["additionalProperties"])
        self.assertEqual(
            {"keys", "clicks", "impressions", "ctr", "position"},
            set(row_schema["required"]),
        )

        envelope = make_envelope(
            "gsc.search-analytics",
            "verified",
            result={
                "kind": "search_analytics",
                "site_url": "sc-domain:example.com",
                "start_date": "2026-08-01",
                "end_date": "2026-08-19",
                "dimensions": ["query"],
                "search_type": "WEB",
                "data_state": "FINAL",
                "aggregation_type": "AUTO",
                "row_limit": 1000,
                "start_row": 0,
                "row_count": 1,
                "row_limit_reached": False,
                "response_aggregation_type": "AUTO",
                "rows": [
                    {
                        "keys": ["example"],
                        "clicks": 1.0,
                        "impressions": 10.0,
                        "ctr": 0.1,
                        "position": 3.2,
                    }
                ],
            },
        )
        self.assert_envelope_contract(envelope)

    def test_invalid_cli_emits_one_json_and_safe_stderr(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = adapter.main(["gsc", "get-site"])
        self.assertEqual(2, exit_code)
        self.assertEqual(1, stdout.getvalue().count("\n"))
        envelope = json.loads(stdout.getvalue())
        self.assert_envelope_contract(envelope)
        self.assertEqual("invalid_cli", envelope["error"]["error_code"])
        self.assertEqual("adapter_error=invalid_cli\n", stderr.getvalue())

    def test_safe_error_redacts_all_secret_classes(self) -> None:
        secret_values = [
            "Bearer abcdefghijklmnopqrstuvwxyz012345",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.signaturevalue",
            "ya29.fakeOAuthTokenValue123456",
            "google-site-verification=fake-verification-value",
            "/Users/example/.secrets/google/service-account.json",
            "cookie=session-value",
        ]
        redacted = redact_text(" ".join(secret_values), limit=4096)
        for value in secret_values:
            self.assertNotIn(value, redacted)
        error = AdapterError(
            "internal_error",
            "failed",
            15,
            "Bearer abcdefghijklmnopqrstuvwxyz012345",
            provider_status="Bearer providerStatusSecret123456",
            reason="/Users/example/.secrets/google/service-account.json",
        )
        self.assertEqual("UNKNOWN", error.provider_status)
        envelope = make_envelope("adapter.serialization", "failed", error=error)
        output = safe_json(envelope)
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz012345", output)
        self.assertNotIn("service-account.json", output)
        self.assertNotIn("providerStatusSecret", output)

    def test_fixture_files_are_credential_free(self) -> None:
        forbidden = ("private_key", "access_token", "refresh_token", "authorization", "client_secret", "google-site-verification=")
        for path in sorted((SKILL_ROOT / "tests" / "fixtures" / "google_api").glob("*.json")):
            payload = path.read_text().lower()
            for marker in forbidden:
                self.assertNotIn(marker, payload, path.name)

    def test_generated_reports_and_fixtures_have_no_credential_shapes(self) -> None:
        patterns = (
            re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{8,}"),
            re.compile(r"\b(?:ya29\.|1//|4/)[A-Za-z0-9._~+/=-]{8,}\b"),
            re.compile(r"-----BEGIN [^-]+PRIVATE KEY-----"),
            re.compile(r'(?i)"(?:private_key|access_token|refresh_token|client_secret)"\s*:'),
        )
        paths = list((SKILL_ROOT / "tests" / "fixtures" / "google_api").glob("*.json"))
        paths.extend(path for path in (SKILL_ROOT / "reports").glob("*") if path.is_file())
        for path in sorted(paths):
            payload = path.read_text(encoding="utf-8")
            for pattern in patterns:
                self.assertIsNone(pattern.search(payload), path.name)


if __name__ == "__main__":
    unittest.main()
