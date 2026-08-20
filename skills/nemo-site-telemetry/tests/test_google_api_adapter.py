from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
FIXTURES = SKILL_ROOT / "tests" / "fixtures" / "google_api"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from google_api.auth import TokenContext
from google_api.ga4 import GA4Client
from google_api.gsc import GSCClient
from google_api.http import GoogleApiClient, HttpResponse, UrlLibPublicXmlFetcher
from google_api.output import AdapterError
from google_api.plans import FileRecoveryStore, build_plan, property_contains, read_plan, write_plan


def load_adapter():
    path = SCRIPTS / "google_api_adapter.py"
    spec = importlib.util.spec_from_file_location("nemo_google_api_adapter_tests", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


adapter = load_adapter()


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


@dataclass
class ExpectedResponse:
    status: int
    body: bytes = b""


class FakeTransport:
    def __init__(self, responses: list[ExpectedResponse | AdapterError]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method, url, *, headers, body, timeout):
        self.calls.append({"method": method, "url": url, "headers": dict(headers), "body": body, "timeout": timeout})
        if not self.responses:
            raise AssertionError(f"unexpected transport call: {method} {url}")
        response = self.responses.pop(0)
        if isinstance(response, AdapterError):
            raise response
        return HttpResponse(response.status, response.body, url)


class FakeAuth:
    def __init__(self, *, mode: str = "adc_service_account") -> None:
        self.mode = mode
        self.token_calls: list[str] = []
        self.status_calls: list[str] = []
        self.enable_calls: list[str] = []

    def auth_mode(self) -> str:
        return self.mode

    def token(self, capability: str) -> TokenContext:
        self.token_calls.append(capability)
        return TokenContext("A" * 40, self.mode, capability)

    def service_status(self, project_id: str) -> dict[str, str]:
        self.status_calls.append(project_id)
        return {
            "searchconsole.googleapis.com": "enabled",
            "analyticsadmin.googleapis.com": "enabled",
            "analyticsdata.googleapis.com": "enabled",
        }

    def enable_services(self, project_id: str) -> dict[str, str]:
        self.enable_calls.append(project_id)
        return self.service_status(project_id)


class FakePublicFetcher:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def fetch(self, url: str) -> dict[str, object]:
        self.calls.append(url)
        return {"status": 200, "root": "urlset", "non_empty": True}


class FakeRecoveryStore:
    def __init__(self) -> None:
        self.markers: set[tuple[str, str]] = set()
        self.claims: set[tuple[str, str]] = set()

    def record_ambiguous(self, *, target_fingerprint_value, authorization_fingerprint, authorization_expires_at, clock):
        self.markers.add((target_fingerprint_value, authorization_fingerprint))

    def validate(self, *, target_fingerprint_value, authorization_fingerprint, clock):
        key = (target_fingerprint_value, authorization_fingerprint)
        if key not in self.markers:
            raise AdapterError("authorization_mismatch", "blocked", 12, "Missing recovery checkpoint.")
        if key in self.claims:
            raise AdapterError("authorization_mismatch", "blocked", 12, "Recovery submit already claimed.")

    def claim(self, *, target_fingerprint_value, authorization_fingerprint, plan_sha256, clock):
        self.validate(
            target_fingerprint_value=target_fingerprint_value,
            authorization_fingerprint=authorization_fingerprint,
            clock=clock,
        )
        self.claims.add((target_fingerprint_value, authorization_fingerprint))


class FakePublicResponse:
    def __init__(self, status: int, body: bytes, location: str | None = None) -> None:
        self.status = status
        self._body = body
        self._location = location

    def read(self, limit: int) -> bytes:
        return self._body[:limit]

    def getheader(self, name: str) -> str | None:
        return self._location if name.lower() == "location" else None


class FakePinnedConnection:
    def __init__(self, response: FakePublicResponse) -> None:
        self.response = response
        self.requests: list[tuple[str, str]] = []

    def request(self, method: str, path: str, *, headers) -> None:
        self.requests.append((method, path))

    def getresponse(self) -> FakePublicResponse:
        return self.response

    def close(self) -> None:
        pass


class FixedClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 20, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.value


class GoogleApiAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FixedClock()

    def runtime(
        self,
        responses: list[ExpectedResponse],
        *,
        auth: FakeAuth | None = None,
        recovery: FakeRecoveryStore | None = None,
    ):
        transport = FakeTransport(responses)
        selected_auth = auth or FakeAuth()
        public = FakePublicFetcher()
        selected_recovery = recovery or FakeRecoveryStore()
        return adapter.Runtime(selected_auth, transport, public, self.clock, selected_recovery), selected_auth, transport, public

    def test_status_only_cannot_reach_auth_http_or_plan_file(self) -> None:
        runtime, auth, transport, _ = self.runtime([])
        with tempfile.TemporaryDirectory(prefix="nemo-site-telemetry-", dir="/tmp") as directory:
            output = str(Path(directory) / "plan.json")
            envelope, code = adapter.execute(
                [
                    "gsc",
                    "sitemap-plan",
                    "--operation-mode",
                    "status_only",
                    "--site-url",
                    "sc-domain:example.com",
                    "--sitemap-url",
                    "https://example.com/sitemap.xml",
                    "--output",
                    output,
                ],
                runtime=runtime,
            )
            self.assertEqual(12, code)
            self.assertEqual("authorization_mismatch", envelope["error"]["error_code"])
            self.assertFalse(Path(output).exists())
        self.assertEqual([], auth.token_calls)
        self.assertEqual([], transport.calls)

    def test_search_analytics_uses_read_only_post_and_normalizes_rows(self) -> None:
        site = json.dumps({"siteUrl": "sc-domain:example.com", "permissionLevel": "siteOwner"}).encode()
        runtime, auth, transport, _ = self.runtime(
            [ExpectedResponse(200, site), ExpectedResponse(200, fixture("gsc_search_analytics.json"))]
        )
        envelope, code = adapter.execute(
            [
                "gsc",
                "search-analytics",
                "--site-url",
                "sc-domain:example.com",
                "--start-date",
                "2026-08-01",
                "--end-date",
                "2026-08-19",
                "--dimension",
                "query",
                "--dimension",
                "page",
                "--search-type",
                "WEB",
                "--data-state",
                "FINAL",
                "--aggregation-type",
                "AUTO",
                "--row-limit",
                "100",
                "--start-row",
                "0",
            ],
            runtime=runtime,
        )
        self.assertEqual(0, code)
        self.assertEqual("verified", envelope["status"])
        self.assertEqual("search_analytics", envelope["result"]["kind"])
        self.assertEqual("gsc_search_analytics", envelope["target"]["resource_type"])
        self.assertEqual(["gsc-read"], auth.token_calls)
        self.assertEqual(["GET", "POST"], [call["method"] for call in transport.calls])
        self.assertEqual(
            "https://www.googleapis.com/webmasters/v3/sites/sc-domain%3Aexample.com/searchAnalytics/query",
            transport.calls[1]["url"],
        )
        self.assertEqual(
            {
                "aggregationType": "AUTO",
                "dataState": "FINAL",
                "dimensions": ["query", "page"],
                "endDate": "2026-08-19",
                "rowLimit": 100,
                "startDate": "2026-08-01",
                "startRow": 0,
                "type": "WEB",
            },
            json.loads(transport.calls[1]["body"]),
        )
        result = envelope["result"]
        self.assertEqual(1, result["row_count"])
        self.assertFalse(result["row_limit_reached"])
        self.assertEqual("BY_PAGE", result["response_aggregation_type"])
        self.assertEqual(0.05, result["rows"][0]["ctr"])
        self.assertNotIn("providerOnlyField", result["rows"][0])
        self.assertIn("not a complete export", envelope["evidence"][1]["summary"])

    def test_search_analytics_invalid_input_blocks_before_auth_or_http(self) -> None:
        runtime, auth, transport, _ = self.runtime([])
        envelope, code = adapter.execute(
            [
                "gsc",
                "search-analytics",
                "--site-url",
                "sc-domain:example.com",
                "--start-date",
                "2026-08-20",
                "--end-date",
                "2026-08-19",
                "--dimension",
                "query",
            ],
            runtime=runtime,
        )
        self.assertEqual(12, code)
        self.assertEqual("invalid_input", envelope["error"]["error_code"])
        self.assertEqual([], auth.token_calls)
        self.assertEqual([], transport.calls)

    def test_search_analytics_empty_response_is_a_valid_empty_result(self) -> None:
        transport = FakeTransport([ExpectedResponse(200, b"{}")])
        client = GSCClient(GoogleApiClient(transport, access_token="A" * 40))
        result = client.search_analytics(
            "sc-domain:example.com",
            start_date="2026-08-01",
            end_date="2026-08-19",
            dimensions=["query"],
        )
        self.assertEqual([], result["rows"])
        self.assertEqual(0, result["row_count"])

    def test_search_analytics_rejects_malformed_provider_rows(self) -> None:
        payload = {
            "rows": [
                {
                    "keys": [123],
                    "clicks": 1,
                    "impressions": 2,
                    "ctr": 0.5,
                    "position": 1,
                }
            ]
        }
        transport = FakeTransport([ExpectedResponse(200, json.dumps(payload).encode())])
        client = GSCClient(GoogleApiClient(transport, access_token="A" * 40))
        with self.assertRaises(AdapterError) as raised:
            client.search_analytics(
                "sc-domain:example.com",
                start_date="2026-08-01",
                end_date="2026-08-19",
                dimensions=["query"],
            )
        self.assertEqual("provider_rejected", raised.exception.error_code)

    def test_search_analytics_rejects_unknown_response_aggregation(self) -> None:
        payload = {"rows": [], "responseAggregationType": "byUnknown"}
        transport = FakeTransport([ExpectedResponse(200, json.dumps(payload).encode())])
        client = GSCClient(GoogleApiClient(transport, access_token="A" * 40))
        with self.assertRaises(AdapterError) as raised:
            client.search_analytics(
                "sc-domain:example.com",
                start_date="2026-08-01",
                end_date="2026-08-19",
                dimensions=["query"],
            )
        self.assertEqual("provider_rejected", raised.exception.error_code)

    def test_search_analytics_post_retries_5xx_as_a_read(self) -> None:
        transport = FakeTransport([ExpectedResponse(503), ExpectedResponse(200, b"{}")])
        sleeps: list[float] = []
        client = GSCClient(
            GoogleApiClient(
                transport,
                access_token="A" * 40,
                sleeper=sleeps.append,
                random_source=lambda: 0.0,
            )
        )
        result = client.search_analytics(
            "sc-domain:example.com",
            start_date="2026-08-01",
            end_date="2026-08-19",
            dimensions=["query"],
        )
        self.assertEqual(0, result["row_count"])
        self.assertEqual(2, len(transport.calls))
        self.assertEqual([1.0], sleeps)

    def _create_sitemap_plan(self, directory: str, *, recovery: FakeRecoveryStore | None = None):
        responses = [
            ExpectedResponse(200, json.dumps({"siteUrl": "sc-domain:example.com", "permissionLevel": "siteOwner"}).encode()),
            ExpectedResponse(404),
        ]
        runtime, auth, transport, public = self.runtime(responses, recovery=recovery)
        output = str(Path(directory) / "plan.json")
        envelope, code = adapter.execute(
            [
                "gsc",
                "sitemap-plan",
                "--operation-mode",
                "submit_once",
                "--site-url",
                "sc-domain:example.com",
                "--sitemap-url",
                "https://example.com/sitemap.xml",
                "--output",
                output,
            ],
            runtime=runtime,
        )
        self.assertEqual(0, code)
        self.assertTrue(Path(output).exists())
        self.assertEqual(["gsc-read"], auth.token_calls)
        self.assertEqual(["GET", "GET"], [call["method"] for call in transport.calls])
        self.assertEqual(["https://example.com/sitemap.xml"], public.calls)
        return output, envelope["plan"]

    def test_sitemap_apply_writes_once_then_reads_back(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nemo-site-telemetry-", dir="/tmp") as directory:
            plan_path, public_plan = self._create_sitemap_plan(directory)
            responses = [
                ExpectedResponse(200, json.dumps({"siteUrl": "sc-domain:example.com", "permissionLevel": "siteOwner"}).encode()),
                ExpectedResponse(404),
                ExpectedResponse(204),
                ExpectedResponse(200, fixture("gsc_sitemap.json")),
            ]
            runtime, auth, transport, _ = self.runtime(responses)
            envelope, code = adapter.execute(
                [
                    "gsc",
                    "sitemap-apply",
                    "--plan",
                    plan_path,
                    "--expected-plan-sha256",
                    public_plan["plan_sha256"],
                    "--authorization-fingerprint",
                    public_plan["authorization_fingerprint"],
                ],
                runtime=runtime,
            )
            self.assertEqual(0, code)
            self.assertEqual("verified", envelope["status"])
            self.assertEqual(["GET", "GET", "PUT", "GET"], [call["method"] for call in transport.calls])
            self.assertEqual(1, sum(call["method"] == "PUT" for call in transport.calls))
            self.assertFalse(Path(plan_path).exists())
            self.assertEqual(["gsc-sitemap-submit"], auth.token_calls)

    def test_ambiguous_sitemap_submit_first_recovers_with_get(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nemo-site-telemetry-", dir="/tmp") as directory:
            plan_path, public_plan = self._create_sitemap_plan(directory)
            responses = [
                ExpectedResponse(200, json.dumps({"siteUrl": "sc-domain:example.com", "permissionLevel": "siteOwner"}).encode()),
                ExpectedResponse(404),
                ExpectedResponse(503),
                ExpectedResponse(200, fixture("gsc_sitemap.json")),
            ]
            runtime, _, transport, _ = self.runtime(responses)
            envelope, code = adapter.execute(
                [
                    "gsc",
                    "sitemap-apply",
                    "--plan",
                    plan_path,
                    "--expected-plan-sha256",
                    public_plan["plan_sha256"],
                    "--authorization-fingerprint",
                    public_plan["authorization_fingerprint"],
                ],
                runtime=runtime,
            )
            self.assertEqual(0, code)
            self.assertEqual("verified", envelope["status"])
            self.assertEqual(["PUT", "GET"], [call["method"] for call in transport.calls][-2:])
            self.assertEqual(1, sum(call["method"] == "PUT" for call in transport.calls))

    def test_ambiguous_sitemap_allows_only_one_bound_recovery_submit(self) -> None:
        recovery = FakeRecoveryStore()
        with tempfile.TemporaryDirectory(prefix="nemo-site-telemetry-", dir="/tmp") as first_directory:
            plan_path, public_plan = self._create_sitemap_plan(first_directory, recovery=recovery)
            runtime, _, initial_transport, _ = self.runtime(
                [
                    ExpectedResponse(200, json.dumps({"siteUrl": "sc-domain:example.com", "permissionLevel": "siteOwner"}).encode()),
                    ExpectedResponse(404),
                    ExpectedResponse(503),
                    ExpectedResponse(404),
                ],
                recovery=recovery,
            )
            envelope, code = adapter.execute(
                [
                    "gsc",
                    "sitemap-apply",
                    "--plan",
                    plan_path,
                    "--expected-plan-sha256",
                    public_plan["plan_sha256"],
                    "--authorization-fingerprint",
                    public_plan["authorization_fingerprint"],
                ],
                runtime=runtime,
            )
            self.assertEqual(13, code)
            self.assertEqual("pending", envelope["status"])
            self.assertEqual(1, sum(call["method"] == "PUT" for call in initial_transport.calls))

        original_authorization = public_plan["authorization_fingerprint"]
        with tempfile.TemporaryDirectory(prefix="nemo-site-telemetry-", dir="/tmp") as recovery_directory:
            recovery_plan_path = str(Path(recovery_directory) / "plan.json")
            runtime, _, _, _ = self.runtime(
                [
                    ExpectedResponse(200, json.dumps({"siteUrl": "sc-domain:example.com", "permissionLevel": "siteOwner"}).encode()),
                    ExpectedResponse(404),
                ],
                recovery=recovery,
            )
            recovery_plan_envelope, code = adapter.execute(
                [
                    "gsc",
                    "sitemap-plan",
                    "--operation-mode",
                    "recovery_readback",
                    "--site-url",
                    "sc-domain:example.com",
                    "--sitemap-url",
                    "https://example.com/sitemap.xml",
                    "--output",
                    recovery_plan_path,
                    "--recovery-authorization-fingerprint",
                    original_authorization,
                ],
                runtime=runtime,
            )
            self.assertEqual(0, code)
            recovery_plan = recovery_plan_envelope["plan"]
            runtime, _, recovery_transport, _ = self.runtime(
                [
                    ExpectedResponse(200, json.dumps({"siteUrl": "sc-domain:example.com", "permissionLevel": "siteOwner"}).encode()),
                    ExpectedResponse(404),
                    ExpectedResponse(503),
                    ExpectedResponse(404),
                ],
                recovery=recovery,
            )
            envelope, code = adapter.execute(
                [
                    "gsc",
                    "sitemap-apply",
                    "--plan",
                    recovery_plan_path,
                    "--expected-plan-sha256",
                    recovery_plan["plan_sha256"],
                    "--authorization-fingerprint",
                    recovery_plan["authorization_fingerprint"],
                ],
                runtime=runtime,
            )
            self.assertEqual(13, code)
            self.assertEqual("pending", envelope["status"])
            self.assertEqual(1, sum(call["method"] == "PUT" for call in recovery_transport.calls))

        with tempfile.TemporaryDirectory(prefix="nemo-site-telemetry-", dir="/tmp") as blocked_directory:
            runtime, auth, transport, _ = self.runtime([], recovery=recovery)
            envelope, code = adapter.execute(
                [
                    "gsc",
                    "sitemap-plan",
                    "--operation-mode",
                    "recovery_readback",
                    "--site-url",
                    "sc-domain:example.com",
                    "--sitemap-url",
                    "https://example.com/sitemap.xml",
                    "--output",
                    str(Path(blocked_directory) / "plan.json"),
                    "--recovery-authorization-fingerprint",
                    original_authorization,
                ],
                runtime=runtime,
            )
            self.assertEqual(12, code)
            self.assertEqual("authorization_mismatch", envelope["error"]["error_code"])
            self.assertEqual([], auth.token_calls)
            self.assertEqual([], transport.calls)

    def test_plan_digest_mismatch_blocks_before_token_or_http(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nemo-site-telemetry-", dir="/tmp") as directory:
            plan_path, public_plan = self._create_sitemap_plan(directory)
            runtime, auth, transport, _ = self.runtime([])
            envelope, code = adapter.execute(
                [
                    "gsc",
                    "sitemap-apply",
                    "--plan",
                    plan_path,
                    "--expected-plan-sha256",
                    "0" * 64,
                    "--authorization-fingerprint",
                    public_plan["authorization_fingerprint"],
                ],
                runtime=runtime,
            )
            self.assertEqual(12, code)
            self.assertEqual("plan_digest_mismatch", envelope["error"]["error_code"])
            self.assertEqual([], auth.token_calls)
            self.assertEqual([], transport.calls)

    def test_plan_expiry_and_symlink_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nemo-site-telemetry-", dir="/tmp") as directory:
            target = "a" * 64
            plan = build_plan(
                action="submit_sitemap",
                operation_mode="submit_once",
                target_fingerprint_value=target,
                authorization_kind="explicit_submit",
                payload={"site_url": "sc-domain:example.com", "sitemap_url": "https://example.com/sitemap.xml"},
                clock=self.clock,
            )
            actual = str(Path(directory) / "actual.json")
            write_plan(actual, plan)
            link = str(Path(directory) / "link.json")
            os.symlink(actual, link)
            with self.assertRaises(AdapterError) as symlink_error:
                read_plan(
                    link,
                    expected_sha256=plan["plan_sha256"],
                    authorization_fingerprint=plan["authorization_fingerprint"],
                    allowed_actions={"submit_sitemap"},
                    allowed_modes={"submit_once"},
                    clock=self.clock,
                )
            self.assertEqual("plan_invalid", symlink_error.exception.error_code)
            self.clock.value += timedelta(minutes=11)
            with self.assertRaises(AdapterError) as expiry_error:
                read_plan(
                    actual,
                    expected_sha256=plan["plan_sha256"],
                    authorization_fingerprint=plan["authorization_fingerprint"],
                    allowed_actions={"submit_sitemap"},
                    allowed_modes={"submit_once"},
                    clock=self.clock,
                )
            self.assertEqual("plan_expired", expiry_error.exception.error_code)

    def test_ga4_realtime_is_not_debugview_evidence(self) -> None:
        runtime, _, transport, _ = self.runtime([ExpectedResponse(200, fixture("ga4_realtime.json"))])
        envelope, code = adapter.execute(
            ["ga4", "realtime", "--property-id", "987654", "--metric", "activeUsers"],
            runtime=runtime,
        )
        self.assertEqual(0, code)
        self.assertEqual("realtime", envelope["result"]["kind"])
        self.assertIn("not DebugView", envelope["evidence"][0]["summary"])
        self.assertEqual(["POST"], [call["method"] for call in transport.calls])

    def test_ga4_realtime_post_retries_a_transient_transport_failure(self) -> None:
        transient = AdapterError(
            "provider_transient",
            "pending",
            13,
            "Retry through the bounded read policy.",
            reason="TimeoutError",
            retryable=True,
        )
        transport = FakeTransport([transient, ExpectedResponse(200, fixture("ga4_realtime.json"))])
        sleeps: list[float] = []
        client = GA4Client(
            GoogleApiClient(
                transport,
                access_token="A" * 40,
                sleeper=sleeps.append,
                random_source=lambda: 0.0,
            )
        )
        result = client.realtime("987654", "activeUsers")
        self.assertEqual("activeUsers", result["metric"])
        self.assertEqual(2, len(transport.calls))
        self.assertEqual([1.0], sleeps)

    def test_gsc_inspection_post_retries_5xx_as_a_read(self) -> None:
        body = json.dumps({"inspectionResult": {"indexStatusResult": {"verdict": "PASS"}}}).encode()
        transport = FakeTransport([ExpectedResponse(503), ExpectedResponse(200, body)])
        sleeps: list[float] = []
        client = GSCClient(
            GoogleApiClient(
                transport,
                access_token="A" * 40,
                sleeper=sleeps.append,
                random_source=lambda: 0.0,
            )
        )
        result = client.inspect_url("sc-domain:example.com", "https://example.com/page/")
        self.assertEqual("PASS", result["verdict"])
        self.assertEqual(2, len(transport.calls))
        self.assertEqual([1.0], sleeps)

    def test_semantic_read_post_exhaustion_stays_provider_transient(self) -> None:
        transport = FakeTransport([ExpectedResponse(503), ExpectedResponse(503)])
        client = GoogleApiClient(
            transport,
            access_token="A" * 40,
            sleeper=lambda _: None,
            random_source=lambda: 0.0,
        )
        with self.assertRaises(AdapterError) as raised:
            client.request_json(
                "POST",
                "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
                body={"inspectionUrl": "https://example.com/", "siteUrl": "sc-domain:example.com"},
                read_only=True,
                read_attempts=2,
            )
        self.assertEqual("provider_transient", raised.exception.error_code)
        self.assertEqual(2, len(transport.calls))

    def test_ga4_ambiguous_create_is_never_replayed(self) -> None:
        transport = FakeTransport([ExpectedResponse(503)])
        client = GA4Client(GoogleApiClient(transport, access_token="A" * 40))
        with self.assertRaises(AdapterError) as raised:
            client.create_property(
                "123456",
                display_name="Example",
                time_zone="Asia/Shanghai",
                currency_code="USD",
            )
        self.assertEqual("ambiguous_write", raised.exception.error_code)
        self.assertEqual(1, len(transport.calls))
        self.assertEqual("POST", transport.calls[0]["method"])

    def test_invalid_provider_web_stream_uri_blocks_before_create(self) -> None:
        payload = {
            "dataStreams": [
                {
                    "name": "properties/987654/dataStreams/123",
                    "type": "WEB_DATA_STREAM",
                    "webStreamData": {"defaultUri": "ftp://example.com"},
                }
            ]
        }
        transport = FakeTransport([ExpectedResponse(200, json.dumps(payload).encode())])
        client = GA4Client(GoogleApiClient(transport, access_token="A" * 40))
        with self.assertRaises(AdapterError) as raised:
            client.list_web_streams("987654")
        self.assertEqual("provider_rejected", raised.exception.error_code)
        self.assertEqual(["GET"], [call["method"] for call in transport.calls])

    def test_url_prefix_scope_requires_a_path_boundary(self) -> None:
        self.assertTrue(property_contains("https://example.com/foo", "https://example.com/foo"))
        self.assertTrue(property_contains("https://example.com/foo", "https://example.com/foo/bar?x=1"))
        self.assertTrue(property_contains("https://example.com/foo/", "https://example.com/foo/bar"))
        self.assertFalse(property_contains("https://example.com/foo", "https://example.com/foobar/sitemap.xml"))
        self.assertFalse(property_contains("https://example.com/foo/", "https://example.com/foo"))
        with self.assertRaises(AdapterError):
            property_contains("https://example.com/foo", "https://[invalid/sitemap.xml")

    def test_public_sitemap_fetcher_rejects_non_public_dns_answers(self) -> None:
        def resolver(host, port, *, type):
            return [
                (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("8.8.8.8", port)),
                (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", port)),
            ]

        fetcher = UrlLibPublicXmlFetcher(
            resolver=resolver,
            connection_factory=lambda *args: self.fail("connection must not be attempted for a mixed public/private answer"),
        )
        with self.assertRaises(AdapterError) as raised:
            fetcher.fetch("https://example.com/sitemap.xml")
        self.assertEqual("invalid_input", raised.exception.error_code)

    def test_public_sitemap_fetcher_pins_the_validated_address_and_rechecks_redirect_dns(self) -> None:
        resolver_calls = 0
        pinned: list[str] = []

        def resolver(host, port, *, type):
            nonlocal resolver_calls
            resolver_calls += 1
            address = "8.8.8.8" if resolver_calls == 1 else "169.254.169.254"
            return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (address, port))]

        def factory(scheme, host, port, address, timeout):
            pinned.append(address)
            return FakePinnedConnection(FakePublicResponse(302, b"", "/final.xml"))

        fetcher = UrlLibPublicXmlFetcher(resolver=resolver, connection_factory=factory)
        with self.assertRaises(AdapterError) as raised:
            fetcher.fetch("https://example.com/sitemap.xml")
        self.assertEqual("invalid_input", raised.exception.error_code)
        self.assertEqual(["8.8.8.8"], pinned)

    def test_public_sitemap_fetcher_accepts_parseable_xml_over_a_pinned_public_address(self) -> None:
        pinned: list[str] = []

        def resolver(host, port, *, type):
            return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("8.8.8.8", port))]

        def factory(scheme, host, port, address, timeout):
            pinned.append(address)
            return FakePinnedConnection(FakePublicResponse(200, b"<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'></urlset>"))

        result = UrlLibPublicXmlFetcher(resolver=resolver, connection_factory=factory).fetch("https://example.com/sitemap.xml")
        self.assertEqual("urlset", result["root"])
        self.assertEqual(["8.8.8.8"], pinned)

    def test_file_recovery_store_claim_is_cross_instance_and_single_use(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "recovery"
            target = "a" * 64
            authorization = "b" * 64
            first = FileRecoveryStore(root)
            first.record_ambiguous(
                target_fingerprint_value=target,
                authorization_fingerprint=authorization,
                authorization_expires_at="2026-08-20T00:10:00Z",
                clock=self.clock(),
            )
            second = FileRecoveryStore(root)
            second.claim(
                target_fingerprint_value=target,
                authorization_fingerprint=authorization,
                plan_sha256="c" * 64,
                clock=self.clock(),
            )
            with self.assertRaises(AdapterError) as raised:
                first.claim(
                    target_fingerprint_value=target,
                    authorization_fingerprint=authorization,
                    plan_sha256="d" * 64,
                    clock=self.clock(),
                )
            self.assertEqual("authorization_mismatch", raised.exception.error_code)

            expiring_target = "e" * 64
            expiring_authorization = "f" * 64
            first.record_ambiguous(
                target_fingerprint_value=expiring_target,
                authorization_fingerprint=expiring_authorization,
                authorization_expires_at="2026-08-20T00:30:00Z",
                clock=self.clock(),
            )
            self.clock.value += timedelta(minutes=16)
            with self.assertRaises(AdapterError) as expired:
                second.validate(
                    target_fingerprint_value=expiring_target,
                    authorization_fingerprint=expiring_authorization,
                    clock=self.clock(),
                )
            self.assertEqual("plan_expired", expired.exception.error_code)

    def test_generic_403_does_not_guess_scope_or_resource_role(self) -> None:
        transport = FakeTransport([ExpectedResponse(403, fixture("google_error_forbidden.json"))])
        api = GoogleApiClient(transport, access_token="A" * 40)
        with self.assertRaises(AdapterError) as raised:
            api.request_json("GET", "https://www.googleapis.com/webmasters/v3/sites")
        self.assertEqual("capability_unknown", raised.exception.error_code)

    def test_read_command_never_enables_apis(self) -> None:
        auth = FakeAuth()
        runtime, auth, _, _ = self.runtime([ExpectedResponse(200, fixture("gsc_sites.json"))], auth=auth)
        envelope, code = adapter.execute(["gsc", "list-sites"], runtime=runtime)
        self.assertEqual(0, code)
        self.assertEqual("sites", envelope["result"]["kind"])
        self.assertEqual([], auth.enable_calls)


if __name__ == "__main__":
    unittest.main()
