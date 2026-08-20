#!/usr/bin/env python3
"""Governed CLI for Search Console and GA4 onboarding readback/write plans."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import sys
from typing import Callable, Protocol, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from google_api.auth import (  # noqa: E402
    CAPABILITY_SCOPES,
    GoogleAuthBroker,
    TokenContext,
    ensure_python,
    validate_project_id,
)
from google_api.ga4 import (  # noqa: E402
    ALLOWED_REALTIME_METRICS,
    GA4Client,
    account_name,
    ga4_target,
    property_name,
)
from google_api.gsc import (  # noqa: E402
    ALLOWED_AGGREGATION_TYPES,
    ALLOWED_DATA_STATES,
    ALLOWED_SEARCH_DIMENSIONS,
    ALLOWED_SEARCH_TYPES,
    GSCClient,
    search_analytics_query,
    sitemap_target,
)
from google_api.http import (  # noqa: E402
    GoogleApiClient,
    PublicXmlFetcher,
    Transport,
    UrlLibPublicXmlFetcher,
    UrlLibTransport,
)
from google_api.output import (  # noqa: E402
    AdapterError,
    default_google_api,
    emit,
    make_envelope,
    make_evidence,
    redact_text,
    rfc3339,
    utc_now,
)
from google_api.plans import (  # noqa: E402
    FileRecoveryStore,
    build_plan,
    canonical_origin,
    consume_plan,
    fingerprint,
    public_plan,
    read_plan,
    target_fingerprint,
    write_plan,
)


class AuthProvider(Protocol):
    def auth_mode(self) -> str: ...
    def token(self, capability: str) -> TokenContext: ...
    def service_status(self, project_id: str) -> dict[str, str]: ...
    def enable_services(self, project_id: str) -> dict[str, str]: ...


class RecoveryStore(Protocol):
    def record_ambiguous(
        self,
        *,
        target_fingerprint_value: str,
        authorization_fingerprint: str,
        authorization_expires_at: str,
        clock: datetime,
    ) -> None: ...

    def validate(
        self,
        *,
        target_fingerprint_value: str,
        authorization_fingerprint: str,
        clock: datetime,
    ) -> None: ...

    def claim(
        self,
        *,
        target_fingerprint_value: str,
        authorization_fingerprint: str,
        plan_sha256: str,
        clock: datetime,
    ) -> None: ...


@dataclass(slots=True)
class Runtime:
    auth: AuthProvider
    transport: Transport
    public_fetcher: PublicXmlFetcher
    clock: Callable[[], datetime] = utc_now
    recovery_store: RecoveryStore = field(default_factory=FileRecoveryStore)


class CLIContractError(Exception):
    pass


class ContractParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CLIContractError(redact_text(message, limit=256))


def _command_hint(argv: Sequence[str]) -> str:
    top = next((item for item in argv if item in {"bootstrap", "auth", "gsc", "ga4"}), "adapter")
    allowed = {
        "bootstrap": {"status", "enable-apis"},
        "auth": {"probe"},
        "gsc": {"list-sites", "get-site", "list-sitemaps", "get-sitemap", "inspect-url", "search-analytics", "sitemap-plan", "sitemap-apply"},
        "ga4": {"list-account-summaries", "get-property", "list-web-streams", "realtime", "resource-plan", "resource-apply"},
    }
    sub = next((item for item in argv if item in allowed.get(top, set())), "invalid-cli")
    return f"{top}.{sub}"


def _add_provider_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-id")
    parser.add_argument("--quota-project-id")
    parser.add_argument("--impersonate-service-account")


def build_parser() -> ContractParser:
    parser = ContractParser(prog="google_api_adapter.py", description="Governed Google API adapter for nemo-site-telemetry")
    parser.add_argument("--debug", action="store_true", help="Enable safe structural diagnostics; never prints provider payloads or credentials")
    top = parser.add_subparsers(dest="provider", required=True, parser_class=ContractParser)

    bootstrap = top.add_parser("bootstrap")
    bootstrap_sub = bootstrap.add_subparsers(dest="operation", required=True, parser_class=ContractParser)
    for operation in ("status", "enable-apis"):
        command = bootstrap_sub.add_parser(operation)
        command.add_argument("--project-id", required=True)
        command.add_argument("--quota-project-id", required=True)
        command.set_defaults(command_name=f"bootstrap.{operation}")

    auth = top.add_parser("auth")
    auth_sub = auth.add_subparsers(dest="operation", required=True, parser_class=ContractParser)
    probe = auth_sub.add_parser("probe")
    probe.add_argument("--capability", required=True, choices=sorted(CAPABILITY_SCOPES))
    _add_provider_options(probe)
    probe.set_defaults(command_name="auth.probe")

    gsc = top.add_parser("gsc")
    gsc_sub = gsc.add_subparsers(dest="operation", required=True, parser_class=ContractParser)
    list_sites = gsc_sub.add_parser("list-sites")
    _add_provider_options(list_sites)
    list_sites.set_defaults(command_name="gsc.list-sites")
    get_site = gsc_sub.add_parser("get-site")
    get_site.add_argument("--site-url", required=True)
    _add_provider_options(get_site)
    get_site.set_defaults(command_name="gsc.get-site")
    list_sitemaps = gsc_sub.add_parser("list-sitemaps")
    list_sitemaps.add_argument("--site-url", required=True)
    _add_provider_options(list_sitemaps)
    list_sitemaps.set_defaults(command_name="gsc.list-sitemaps")
    get_sitemap = gsc_sub.add_parser("get-sitemap")
    get_sitemap.add_argument("--site-url", required=True)
    get_sitemap.add_argument("--sitemap-url", required=True)
    _add_provider_options(get_sitemap)
    get_sitemap.set_defaults(command_name="gsc.get-sitemap")
    inspect_url = gsc_sub.add_parser("inspect-url")
    inspect_url.add_argument("--site-url", required=True)
    inspect_url.add_argument("--inspection-url", required=True)
    _add_provider_options(inspect_url)
    inspect_url.set_defaults(command_name="gsc.inspect-url")
    search_analytics = gsc_sub.add_parser("search-analytics")
    search_analytics.add_argument("--site-url", required=True)
    search_analytics.add_argument("--start-date", required=True)
    search_analytics.add_argument("--end-date", required=True)
    search_analytics.add_argument("--dimension", action="append", choices=sorted(ALLOWED_SEARCH_DIMENSIONS))
    search_analytics.add_argument("--search-type", default="WEB", choices=sorted(ALLOWED_SEARCH_TYPES))
    search_analytics.add_argument("--data-state", default="FINAL", choices=sorted(ALLOWED_DATA_STATES))
    search_analytics.add_argument("--aggregation-type", default="AUTO", choices=sorted(ALLOWED_AGGREGATION_TYPES))
    search_analytics.add_argument("--row-limit", type=int, default=1000)
    search_analytics.add_argument("--start-row", type=int, default=0)
    _add_provider_options(search_analytics)
    search_analytics.set_defaults(command_name="gsc.search-analytics")
    sitemap_plan = gsc_sub.add_parser("sitemap-plan")
    sitemap_plan.add_argument("--operation-mode", required=True, choices=["status_only", "manual_readback", "submit_once", "recovery_readback"])
    sitemap_plan.add_argument("--site-url", required=True)
    sitemap_plan.add_argument("--sitemap-url", required=True)
    sitemap_plan.add_argument("--output", required=True)
    sitemap_plan.add_argument("--recovery-authorization-fingerprint")
    _add_provider_options(sitemap_plan)
    sitemap_plan.set_defaults(command_name="gsc.sitemap-plan")
    sitemap_apply = gsc_sub.add_parser("sitemap-apply")
    sitemap_apply.add_argument("--plan", required=True)
    sitemap_apply.add_argument("--expected-plan-sha256", required=True)
    sitemap_apply.add_argument("--authorization-fingerprint", required=True)
    _add_provider_options(sitemap_apply)
    sitemap_apply.set_defaults(command_name="gsc.sitemap-apply")

    ga4 = top.add_parser("ga4")
    ga4_sub = ga4.add_subparsers(dest="operation", required=True, parser_class=ContractParser)
    account_summaries = ga4_sub.add_parser("list-account-summaries")
    _add_provider_options(account_summaries)
    account_summaries.set_defaults(command_name="ga4.list-account-summaries")
    get_property = ga4_sub.add_parser("get-property")
    get_property.add_argument("--property-id", required=True)
    _add_provider_options(get_property)
    get_property.set_defaults(command_name="ga4.get-property")
    list_streams = ga4_sub.add_parser("list-web-streams")
    list_streams.add_argument("--property-id", required=True)
    _add_provider_options(list_streams)
    list_streams.set_defaults(command_name="ga4.list-web-streams")
    realtime = ga4_sub.add_parser("realtime")
    realtime.add_argument("--property-id", required=True)
    realtime.add_argument("--metric", required=True, choices=sorted(ALLOWED_REALTIME_METRICS))
    _add_provider_options(realtime)
    realtime.set_defaults(command_name="ga4.realtime")
    resource_plan = ga4_sub.add_parser("resource-plan")
    resource_plan.add_argument("--account-id", required=True)
    resource_plan.add_argument("--property-id")
    resource_plan.add_argument("--production-origin", required=True)
    resource_plan.add_argument("--display-name", required=True)
    resource_plan.add_argument("--time-zone", required=True)
    resource_plan.add_argument("--currency-code", required=True)
    resource_plan.add_argument("--output", required=True)
    _add_provider_options(resource_plan)
    resource_plan.set_defaults(command_name="ga4.resource-plan")
    resource_apply = ga4_sub.add_parser("resource-apply")
    resource_apply.add_argument("--plan", required=True)
    resource_apply.add_argument("--expected-plan-sha256", required=True)
    resource_apply.add_argument("--authorization-fingerprint", required=True)
    _add_provider_options(resource_apply)
    resource_apply.set_defaults(command_name="ga4.resource-apply")
    return parser


def _runtime(namespace: argparse.Namespace, runtime: Runtime | None) -> Runtime:
    if runtime is not None:
        return runtime
    return Runtime(
        auth=GoogleAuthBroker(impersonate_service_account=getattr(namespace, "impersonate_service_account", None)),
        transport=UrlLibTransport(),
        public_fetcher=UrlLibPublicXmlFetcher(),
    )


def _api_state(
    checked_at: str,
    token: TokenContext | None,
    namespace: argparse.Namespace,
    *,
    readback: str = "verified",
) -> dict[str, object]:
    state = default_google_api(checked_at, auth_mode=token.auth_mode if token else "unknown")
    state.update(
        {
            "api_project": "matched" if getattr(namespace, "project_id", None) else "unknown",
            "quota_project_status": "matched" if getattr(namespace, "quota_project_id", None) else ("not_applicable" if token and token.auth_mode != "adc_user" else "missing"),
            "capability_status": "available" if token else "unknown",
            "scope_status": "matched" if token else "unknown",
            "resource_access": "matched" if token else "unknown",
            "bootstrap_status": "not_needed",
            "steady_state": "zero_click" if token else "not_applicable",
            "api_readback": readback,
        }
    )
    return state


def _client(runtime: Runtime, namespace: argparse.Namespace, capability: str, *, write: bool = False) -> tuple[GoogleApiClient, TokenContext]:
    project_id = validate_project_id(getattr(namespace, "project_id", None), required=False)
    quota_project_id = validate_project_id(getattr(namespace, "quota_project_id", None), required=False)
    token = runtime.auth.token(capability)
    if write and token.auth_mode == "adc_user" and not quota_project_id:
        raise AdapterError("quota_project_missing", "blocked", 11, "Provide and verify the exact quota project before an API write.")
    if write and project_id and not quota_project_id:
        raise AdapterError("quota_project_missing", "blocked", 11, "Provide and verify the exact quota project before an API write.")
    return GoogleApiClient(runtime.transport, access_token=token.access_token, quota_project_id=quota_project_id), token


def _target(resource_type: str, resource_name: str, *, operation: str, **fields: str) -> dict[str, object]:
    digest = target_fingerprint(
        provider="google",
        resource_type=resource_type,
        resource_name=resource_name,
        operation=operation,
        site_url=fields.get("site_url"),
        sitemap_url=fields.get("sitemap_url"),
        property_name=fields.get("property_name"),
    )
    return {"resource_type": resource_type, "resource_name": resource_name, "target_fingerprint": digest, **fields}


def _success(
    runtime: Runtime,
    namespace: argparse.Namespace,
    *,
    status: str,
    token: TokenContext | None,
    result: dict[str, object],
    evidence: list[dict[str, object]],
    target: dict[str, object] | None = None,
    plan: dict[str, object] | None = None,
    readback: str = "verified",
) -> tuple[dict[str, object], int]:
    checked_at = rfc3339(runtime.clock())
    return (
        make_envelope(
            namespace.command_name,
            status,
            clock=runtime.clock,
            google_api=_api_state(checked_at, token, namespace, readback=readback),
            target=target,
            evidence=evidence,
            result=result,
            plan=plan,
        ),
        0,
    )


def _bootstrap(runtime: Runtime, namespace: argparse.Namespace) -> tuple[dict[str, object], int]:
    project = validate_project_id(namespace.project_id, required=True)
    quota = validate_project_id(namespace.quota_project_id, required=True)
    checked_at = rfc3339(runtime.clock())
    services = runtime.auth.enable_services(project) if namespace.operation == "enable-apis" else runtime.auth.service_status(project)
    all_enabled = all(value == "enabled" for value in services.values())
    state = default_google_api(checked_at, auth_mode=runtime.auth.auth_mode())
    state.update(
        {
            "api_project": "matched",
            "quota_project_status": "matched",
            "bootstrap_status": "completed" if all_enabled else "required",
            "steady_state": "zero_click" if all_enabled else "not_applicable",
            "api_readback": "verified",
        }
    )
    evidence = [make_evidence("serviceusage.services.list", "verified", "Exact project service states were read back.", checked_at=checked_at)]
    if all_enabled:
        return (
            make_envelope(
                namespace.command_name,
                "completed",
                clock=runtime.clock,
                google_api=state,
                evidence=evidence,
                result={"kind": "bootstrap_status", "services": services},
            ),
            0,
        )
    error = AdapterError("api_not_enabled", "required", 10, "Run bootstrap enable-apis only after explicit Google API configuration authorization.")
    return make_envelope(namespace.command_name, "required", clock=runtime.clock, google_api=state, evidence=evidence, error=error), 10


def _auth_probe(runtime: Runtime, namespace: argparse.Namespace) -> tuple[dict[str, object], int]:
    api, token = _client(runtime, namespace, namespace.capability)
    checked_at = rfc3339(runtime.clock())
    if namespace.capability.startswith("gsc-"):
        GSCClient(api).list_sites()
        method = "webmasters.sites.list"
    else:
        GA4Client(api).list_account_summaries()
        method = "analyticsadmin.accountSummaries.list"
    return _success(
        runtime,
        namespace,
        status="verified",
        token=token,
        result={"kind": "auth_probe", "capability": namespace.capability},
        evidence=[make_evidence(method, "verified", "The fixed read probe completed for this capability.", checked_at=checked_at)],
    )


def _gsc_read(runtime: Runtime, namespace: argparse.Namespace) -> tuple[dict[str, object], int]:
    if namespace.operation == "search-analytics":
        search_analytics_query(
            start_date=namespace.start_date,
            end_date=namespace.end_date,
            dimensions=namespace.dimension,
            search_type=namespace.search_type,
            data_state=namespace.data_state,
            aggregation_type=namespace.aggregation_type,
            row_limit=namespace.row_limit,
            start_row=namespace.start_row,
        )
    api, token = _client(runtime, namespace, "gsc-read")
    client = GSCClient(api)
    checked_at = rfc3339(runtime.clock())
    if namespace.operation == "list-sites":
        items = client.list_sites()
        return _success(runtime, namespace, status="completed", token=token, result={"kind": "sites", "count": len(items), "items": items}, evidence=[make_evidence("webmasters.sites.list", "verified", "Search Console properties were read from the API.", checked_at=checked_at)])
    if namespace.operation == "get-site":
        resource = client.get_site(namespace.site_url)
        assert resource is not None
        target = _target("gsc_site", str(resource["site_url"]), operation="read_site", site_url=str(resource["site_url"]))
        return _success(runtime, namespace, status="verified", token=token, target=target, result={"kind": "site", "resource": resource}, evidence=[make_evidence("webmasters.sites.get", "verified", "The exact Search Console property was read back.", checked_at=checked_at)])
    if namespace.operation == "list-sitemaps":
        site = client.get_site(namespace.site_url)
        assert site is not None
        items = client.list_sitemaps(namespace.site_url)
        target = _target("gsc_site", str(site["site_url"]), operation="list_sitemaps", site_url=str(site["site_url"]))
        return _success(runtime, namespace, status="completed", token=token, target=target, result={"kind": "sitemaps", "count": len(items), "items": items}, evidence=[make_evidence("webmasters.sitemaps.list", "verified", "Sitemaps were read for the exact property.", checked_at=checked_at)])
    if namespace.operation == "get-sitemap":
        resource = client.get_sitemap(namespace.site_url, namespace.sitemap_url, allow_not_found=True)
        target, _ = sitemap_target(namespace.site_url, namespace.sitemap_url, operation="read_sitemap")
        if resource is None:
            error = AdapterError("not_found", "failed", 14, "The exact sitemap is absent; submit only under explicit write authorization.")
            return make_envelope(namespace.command_name, "failed", clock=runtime.clock, google_api=_api_state(checked_at, token, namespace), target=target, evidence=[make_evidence("webmasters.sitemaps.get", "observed", "The exact sitemap was not found.", checked_at=checked_at)], error=error), 14
        return _success(runtime, namespace, status="verified", token=token, target=target, result={"kind": "sitemap", "resource": resource}, evidence=[make_evidence("webmasters.sitemaps.get", "verified", "The exact sitemap was read back.", checked_at=checked_at)])
    if namespace.operation == "inspect-url":
        resource = client.inspect_url(namespace.site_url, namespace.inspection_url)
        target = _target("gsc_inspection_url", str(resource["inspection_url"]), operation="inspect_url", site_url=namespace.site_url)
        return _success(runtime, namespace, status="verified", token=token, target=target, result={"kind": "inspection", "resource": resource}, evidence=[make_evidence("searchconsole.urlInspection.index.inspect", "verified", "The exact URL inspection result was read; no indexing request was made.", checked_at=checked_at)])
    if namespace.operation == "search-analytics":
        site = client.get_site(namespace.site_url)
        assert site is not None
        resource = client.search_analytics(
            str(site["site_url"]),
            start_date=namespace.start_date,
            end_date=namespace.end_date,
            dimensions=namespace.dimension,
            search_type=namespace.search_type,
            data_state=namespace.data_state,
            aggregation_type=namespace.aggregation_type,
            row_limit=namespace.row_limit,
            start_row=namespace.start_row,
        )
        identity = {
            "provider": "gsc",
            "resource_type": "search_analytics",
            "operation": "query",
            "site_url": resource["site_url"],
            "start_date": resource["start_date"],
            "end_date": resource["end_date"],
            "dimensions": resource["dimensions"],
            "search_type": resource["search_type"],
            "data_state": resource["data_state"],
            "aggregation_type": resource["aggregation_type"],
            "row_limit": resource["row_limit"],
            "start_row": resource["start_row"],
        }
        target = {
            "resource_type": "gsc_search_analytics",
            "resource_name": str(resource["site_url"]),
            "site_url": str(resource["site_url"]),
            "target_fingerprint": fingerprint(identity),
        }
        evidence = [
            make_evidence("webmasters.sites.get", "verified", "The exact Search Console property and access were read back.", checked_at=checked_at),
            make_evidence("webmasters.searchanalytics.query", "verified", "The bounded Search Analytics query completed; top aggregated rows are not a complete export or indexing proof.", checked_at=checked_at),
        ]
        return _success(runtime, namespace, status="verified", token=token, target=target, result={"kind": "search_analytics", **resource}, evidence=evidence)
    raise AdapterError("invalid_cli", "failed", 2, "Choose a supported GSC read operation.")


def _gsc_plan(runtime: Runtime, namespace: argparse.Namespace) -> tuple[dict[str, object], int]:
    if namespace.operation_mode in {"status_only", "manual_readback"}:
        raise AdapterError("authorization_mismatch", "blocked", 12, "Use get-sitemap or list-sitemaps; read-only intent cannot create a write plan.")
    requested_target, requested_digest = sitemap_target(namespace.site_url, namespace.sitemap_url, operation="submit_sitemap")
    recovery_authorization = namespace.recovery_authorization_fingerprint
    if namespace.operation_mode == "recovery_readback":
        if not recovery_authorization:
            raise AdapterError("authorization_mismatch", "blocked", 12, "Provide the original ambiguous-submit authorization fingerprint for recovery.")
        runtime.recovery_store.validate(
            target_fingerprint_value=requested_digest,
            authorization_fingerprint=recovery_authorization,
            clock=runtime.clock(),
        )
    elif recovery_authorization:
        raise AdapterError("authorization_mismatch", "blocked", 12, "A fresh submit plan cannot consume a recovery authorization fingerprint.")
    api, token = _client(runtime, namespace, "gsc-read")
    client = GSCClient(api)
    site = client.get_site(namespace.site_url)
    assert site is not None
    target, target_digest = sitemap_target(str(site["site_url"]), namespace.sitemap_url, operation="submit_sitemap")
    if target_digest != requested_digest or target != requested_target:
        raise AdapterError("target_mismatch", "blocked", 12, "The exact sitemap target changed during recovery preflight.")
    existing = client.get_sitemap(str(site["site_url"]), namespace.sitemap_url, allow_not_found=True)
    checked_at = rfc3339(runtime.clock())
    if existing is not None:
        plan = build_plan(
            action="noop_existing",
            operation_mode=namespace.operation_mode,
            target_fingerprint_value=target_digest,
            authorization_kind="existing_readback",
            payload={"site_url": target["site_url"], "sitemap_url": target["sitemap_url"]},
            clock=runtime.clock,
        )
        return _success(runtime, namespace, status="noop", token=token, target=target, result={"kind": "write_outcome", "action": "noop_existing", "resource": existing}, plan=public_plan(plan, output_file_status="not_created"), evidence=[make_evidence("webmasters.sitemaps.get", "verified", "The exact sitemap already exists; no plan file or write was created.", checked_at=checked_at)])
    public = runtime.public_fetcher.fetch(str(target["sitemap_url"]))
    payload: dict[str, object] = {
        "site_url": target["site_url"],
        "sitemap_url": target["sitemap_url"],
        "public_preflight": {"status": public.get("status"), "root": public.get("root"), "non_empty": True},
        "recovery_attempt": 0 if namespace.operation_mode == "submit_once" else 1,
    }
    if recovery_authorization:
        payload["recovery_authorization_fingerprint"] = recovery_authorization
    plan = build_plan(
        action="submit_sitemap",
        operation_mode=namespace.operation_mode,
        target_fingerprint_value=target_digest,
        authorization_kind="explicit_submit" if namespace.operation_mode == "submit_once" else "recovery_submit",
        payload=payload,
        clock=runtime.clock,
    )
    write_plan(namespace.output, plan)
    evidence = [
        make_evidence("webmasters.sites.get", "verified", "The exact property and current access were read back.", checked_at=checked_at),
        make_evidence("webmasters.sitemaps.get", "verified", "The exact sitemap is currently absent.", checked_at=checked_at),
        make_evidence("public.sitemap.get", "verified", "The public sitemap returned non-empty parseable XML.", checked_at=checked_at),
    ]
    return _success(runtime, namespace, status="completed", token=token, target=target, result={"kind": "write_outcome", "action": "planned"}, plan=public_plan(plan, output_file_status="created"), evidence=evidence)


def _validate_plan_payload(plan: dict[str, object], required: set[str]) -> dict[str, object]:
    payload = plan.get("payload")
    if not isinstance(payload, dict) or any(key not in payload for key in required):
        raise AdapterError("plan_invalid", "blocked", 12, "Regenerate the plan; required target fields are missing.")
    return payload


def _gsc_apply(runtime: Runtime, namespace: argparse.Namespace) -> tuple[dict[str, object], int]:
    plan = read_plan(
        namespace.plan,
        expected_sha256=namespace.expected_plan_sha256,
        authorization_fingerprint=namespace.authorization_fingerprint,
        allowed_actions={"submit_sitemap"},
        allowed_modes={"submit_once", "recovery_readback"},
        clock=runtime.clock,
    )
    try:
        payload = _validate_plan_payload(plan, {"site_url", "sitemap_url", "recovery_attempt"})
        recovery_authorization: str | None = None
        if plan["operation_mode"] == "recovery_readback":
            if payload.get("recovery_attempt") != 1 or not isinstance(payload.get("recovery_authorization_fingerprint"), str):
                raise AdapterError("plan_invalid", "blocked", 12, "A recovery plan must bind one prior ambiguous-submit authorization.")
            recovery_authorization = str(payload["recovery_authorization_fingerprint"])
        elif payload.get("recovery_attempt") != 0 or "recovery_authorization_fingerprint" in payload:
            raise AdapterError("plan_invalid", "blocked", 12, "A fresh submit plan cannot contain recovery state.")
        target, digest = sitemap_target(str(payload["site_url"]), str(payload["sitemap_url"]), operation="submit_sitemap")
        if digest != plan.get("target_fingerprint"):
            raise AdapterError("target_mismatch", "blocked", 12, "Regenerate the plan after target identity drift.")
        if recovery_authorization:
            runtime.recovery_store.validate(
                target_fingerprint_value=digest,
                authorization_fingerprint=recovery_authorization,
                clock=runtime.clock(),
            )
        api, token = _client(runtime, namespace, "gsc-sitemap-submit", write=True)
        client = GSCClient(api)
        site = client.get_site(str(payload["site_url"]))
        if site is None or site.get("site_url") != payload["site_url"]:
            raise AdapterError("target_mismatch", "blocked", 12, "The exact Search Console property changed after planning.")
        checked_at = rfc3339(runtime.clock())
        existing = client.get_sitemap(str(payload["site_url"]), str(payload["sitemap_url"]), allow_not_found=True)
        if existing is not None:
            return _success(runtime, namespace, status="noop", token=token, target=target, result={"kind": "write_outcome", "action": "noop_existing", "resource": existing}, evidence=[make_evidence("webmasters.sitemaps.get", "verified", "Apply re-read found the exact sitemap; no write was sent.", checked_at=checked_at)])
        if recovery_authorization:
            runtime.recovery_store.claim(
                target_fingerprint_value=digest,
                authorization_fingerprint=recovery_authorization,
                plan_sha256=str(plan["plan_sha256"]),
                clock=runtime.clock(),
            )
        try:
            client.submit_sitemap(str(payload["site_url"]), str(payload["sitemap_url"]))
        except AdapterError as exc:
            if exc.error_code != "ambiguous_write":
                raise
            # The first network action after an ambiguous PUT is an exact readback.
            recovered = client.get_sitemap(str(payload["site_url"]), str(payload["sitemap_url"]), allow_not_found=True)
            if recovered is not None:
                return _success(runtime, namespace, status="verified", token=token, target=target, result={"kind": "write_outcome", "action": "submitted_once", "resource": recovered}, evidence=[make_evidence("webmasters.sitemaps.submit", "observed", "The submit response was ambiguous.", checked_at=checked_at), make_evidence("webmasters.sitemaps.get", "verified", "Immediate exact readback found the sitemap.", checked_at=rfc3339(runtime.clock()))])
            if recovery_authorization is None:
                authorization = plan.get("authorization")
                if not isinstance(authorization, dict) or not isinstance(authorization.get("expires_at"), str):
                    raise AdapterError("plan_invalid", "blocked", 12, "The submit plan lacks a valid authorization expiry for recovery.")
                runtime.recovery_store.record_ambiguous(
                    target_fingerprint_value=digest,
                    authorization_fingerprint=str(plan["authorization_fingerprint"]),
                    authorization_expires_at=str(authorization["expires_at"]),
                    clock=runtime.clock(),
                )
                next_step = "Keep recovery_readback pending; a new recovery plan must bind the still-valid original authorization fingerprint."
            else:
                next_step = "The single recovery submit is exhausted; continue exact readback and do not create another recovery plan."
            pending = AdapterError("ambiguous_write", "pending", 13, next_step, retryable=False)
            state = _api_state(checked_at, token, namespace, readback="pending")
            return make_envelope(namespace.command_name, "pending", clock=runtime.clock, google_api=state, target=target, evidence=[make_evidence("webmasters.sitemaps.submit", "pending", "The submit outcome was ambiguous.", checked_at=checked_at), make_evidence("webmasters.sitemaps.get", "pending", "The first recovery readback did not find the exact sitemap.", checked_at=rfc3339(runtime.clock()))], error=pending), 13
        readback = client.get_sitemap(str(payload["site_url"]), str(payload["sitemap_url"]), allow_not_found=True)
        if readback is None:
            pending = AdapterError("provider_transient", "pending", 13, "Wait for provider propagation and run exact readback; do not replay this plan.", retryable=True)
            return make_envelope(namespace.command_name, "pending", clock=runtime.clock, google_api=_api_state(checked_at, token, namespace, readback="pending"), target=target, evidence=[make_evidence("webmasters.sitemaps.submit", "observed", "One exact submit call completed.", checked_at=checked_at), make_evidence("webmasters.sitemaps.get", "pending", "The immediate readback has not exposed the sitemap yet.", checked_at=rfc3339(runtime.clock()))], error=pending), 13
        return _success(runtime, namespace, status="verified", token=token, target=target, result={"kind": "write_outcome", "action": "submitted_once", "resource": readback}, evidence=[make_evidence("webmasters.sitemaps.submit", "observed", "One exact submit call completed.", checked_at=checked_at), make_evidence("webmasters.sitemaps.get", "verified", "The write-after-readback found the exact sitemap.", checked_at=rfc3339(runtime.clock()))])
    finally:
        consume_plan(namespace.plan)


def _ga4_read(runtime: Runtime, namespace: argparse.Namespace) -> tuple[dict[str, object], int]:
    api, token = _client(runtime, namespace, "ga4-read")
    client = GA4Client(api)
    checked_at = rfc3339(runtime.clock())
    if namespace.operation == "list-account-summaries":
        items = client.list_account_summaries()
        return _success(runtime, namespace, status="completed", token=token, result={"kind": "account_summaries", "count": len(items), "items": items}, evidence=[make_evidence("analyticsadmin.accountSummaries.list", "verified", "GA4 account/property summaries were read from the Admin API.", checked_at=checked_at)])
    if namespace.operation == "get-property":
        resource = client.get_property(namespace.property_id)
        assert resource is not None
        name = str(resource["name"])
        target = _target("ga4_property", name, operation="read_property", property_name=name)
        return _success(runtime, namespace, status="verified", token=token, target=target, result={"kind": "property", "resource": resource}, evidence=[make_evidence("analyticsadmin.properties.get", "verified", "The exact GA4 property was read back.", checked_at=checked_at)])
    if namespace.operation == "list-web-streams":
        prop = property_name(namespace.property_id)
        client.get_property(prop)
        items = client.list_web_streams(prop)
        target = _target("ga4_property", prop, operation="list_web_streams", property_name=prop)
        return _success(runtime, namespace, status="completed", token=token, target=target, result={"kind": "web_streams", "count": len(items), "items": items}, evidence=[make_evidence("analyticsadmin.properties.dataStreams.list", "verified", "Web data streams were read for the exact property.", checked_at=checked_at)])
    if namespace.operation == "realtime":
        prop = property_name(namespace.property_id)
        resource = client.realtime(prop, namespace.metric)
        target = _target("ga4_property", prop, operation="realtime", property_name=prop)
        return _success(runtime, namespace, status="verified", token=token, target=target, result={"kind": "realtime", "resource": resource}, evidence=[make_evidence("analyticsdata.properties.runRealtimeReport", "verified", "The limited Realtime API report completed; this is not DebugView evidence.", checked_at=checked_at)])
    raise AdapterError("invalid_cli", "failed", 2, "Choose a supported GA4 read operation.")


def _validate_ga4_inputs(namespace: argparse.Namespace) -> tuple[str, str, str, str]:
    display_name = namespace.display_name.strip()
    if not display_name or len(display_name) > 100:
        raise AdapterError("invalid_input", "blocked", 12, "Provide a non-empty GA4 display name of at most 100 characters.")
    try:
        ZoneInfo(namespace.time_zone)
    except ZoneInfoNotFoundError as exc:
        raise AdapterError("invalid_input", "blocked", 12, "Provide an exact IANA time zone; the adapter will not guess one.") from exc
    currency = namespace.currency_code.upper()
    if len(currency) != 3 or not currency.isalpha():
        raise AdapterError("invalid_input", "blocked", 12, "Provide an exact three-letter currency code; the adapter will not guess one.")
    return display_name, namespace.time_zone, currency, canonical_origin(namespace.production_origin)


def _ga4_plan(runtime: Runtime, namespace: argparse.Namespace) -> tuple[dict[str, object], int]:
    display, time_zone, currency, origin = _validate_ga4_inputs(namespace)
    account = account_name(namespace.account_id)
    prop = property_name(namespace.property_id) if namespace.property_id else None
    api, token = _client(runtime, namespace, "ga4-read")
    client = GA4Client(api)
    summaries = client.list_account_summaries()
    if account not in {item.get("account") for item in summaries}:
        raise AdapterError("target_mismatch", "blocked", 12, "The exact GA4 account was not present in the current identity readback.")
    target, target_digest = ga4_target(account_id=account, production_origin=origin, operation="ga4_resource_create", property_id=prop)
    matches = client.find_origin_matches(account, origin)
    if len(matches) > 1:
        raise AdapterError("target_mismatch", "blocked", 12, "Multiple GA4 web streams match the exact origin; select the immutable property manually.")
    checked_at = rfc3339(runtime.clock())
    if len(matches) == 1:
        plan = build_plan(action="noop_existing", operation_mode="ga4_create", target_fingerprint_value=target_digest, authorization_kind="existing_readback", payload={"account": account, "production_origin": origin}, clock=runtime.clock)
        return _success(runtime, namespace, status="noop", token=token, target=target, result={"kind": "write_outcome", "action": "noop_existing", "resource": matches[0]}, plan=public_plan(plan, output_file_status="not_created"), evidence=[make_evidence("analyticsadmin.properties.dataStreams.list", "verified", "One exact web stream already matches the production origin.", checked_at=checked_at)])
    action = "create_property_and_stream"
    if prop:
        existing_property = client.get_property(prop)
        assert existing_property is not None
        if existing_property.get("parent") != account:
            raise AdapterError("target_mismatch", "blocked", 12, "The exact property does not belong to the selected account.")
        action = "create_stream"
    plan = build_plan(
        action=action,
        operation_mode="ga4_create",
        target_fingerprint_value=target_digest,
        authorization_kind="explicit_ga4_create",
        payload={
            "account": account,
            "property": prop,
            "production_origin": origin,
            "display_name": display,
            "time_zone": time_zone,
            "currency_code": currency,
        },
        clock=runtime.clock,
    )
    write_plan(namespace.output, plan)
    return _success(runtime, namespace, status="completed", token=token, target=target, result={"kind": "write_outcome", "action": "planned"}, plan=public_plan(plan, output_file_status="created"), evidence=[make_evidence("analyticsadmin.accountSummaries.list", "verified", "The exact account was read back.", checked_at=checked_at), make_evidence("analyticsadmin.properties.dataStreams.list", "verified", "No exact origin match exists at plan time.", checked_at=checked_at)])


def _ga4_pending(
    runtime: Runtime,
    namespace: argparse.Namespace,
    token: TokenContext,
    target: dict[str, object],
    *,
    candidate_count: int,
    partial: bool,
    evidence: list[dict[str, object]],
) -> tuple[dict[str, object], int]:
    checked_at = rfc3339(runtime.clock())
    error = AdapterError("ambiguous_write", "pending", 13, "Inspect the exact GA4 account/property readback and obtain fresh authorization; never replay create automatically.")
    return (
        make_envelope(
            namespace.command_name,
            "pending",
            clock=runtime.clock,
            google_api=_api_state(checked_at, token, namespace, readback="pending"),
            target=target,
            evidence=evidence,
            result={"kind": "write_outcome", "action": "ambiguous", "candidate_count": candidate_count, "partial_external_state": partial},
            error=error,
        ),
        13,
    )


def _ga4_apply(runtime: Runtime, namespace: argparse.Namespace) -> tuple[dict[str, object], int]:
    plan = read_plan(
        namespace.plan,
        expected_sha256=namespace.expected_plan_sha256,
        authorization_fingerprint=namespace.authorization_fingerprint,
        allowed_actions={"create_property_and_stream", "create_stream"},
        allowed_modes={"ga4_create"},
        clock=runtime.clock,
    )
    try:
        payload = _validate_plan_payload(plan, {"account", "production_origin", "display_name", "time_zone", "currency_code"})
        account = account_name(str(payload["account"]))
        prop = property_name(str(payload["property"])) if payload.get("property") else None
        origin = canonical_origin(str(payload["production_origin"]))
        target, digest = ga4_target(account_id=account, production_origin=origin, operation="ga4_resource_create", property_id=prop)
        if digest != plan.get("target_fingerprint"):
            raise AdapterError("target_mismatch", "blocked", 12, "Regenerate the GA4 plan after target identity drift.")
        api, token = _client(runtime, namespace, "ga4-admin-write", write=True)
        client = GA4Client(api)
        checked_at = rfc3339(runtime.clock())
        matches = client.find_origin_matches(account, origin)
        if len(matches) > 1:
            raise AdapterError("target_mismatch", "blocked", 12, "Multiple exact-origin streams exist; no create was attempted.")
        if len(matches) == 1:
            return _success(runtime, namespace, status="noop", token=token, target=target, result={"kind": "write_outcome", "action": "noop_existing", "resource": matches[0]}, evidence=[make_evidence("analyticsadmin.properties.dataStreams.list", "verified", "Apply re-read found one exact stream; no write was sent.", checked_at=checked_at)])

        if plan["action"] == "create_stream":
            assert prop is not None
            current_property = client.get_property(prop)
            if current_property is None or current_property.get("parent") != account:
                raise AdapterError("target_mismatch", "blocked", 12, "The exact GA4 property changed after planning.")
            try:
                client.create_web_stream(prop, display_name=str(payload["display_name"]), production_origin=origin)
            except AdapterError as exc:
                if exc.error_code != "ambiguous_write":
                    raise
                recovered = [stream for stream in client.list_web_streams(prop) if stream.get("default_uri") == origin]
                if len(recovered) != 1:
                    return _ga4_pending(runtime, namespace, token, target, candidate_count=len(recovered), partial=False, evidence=[make_evidence("analyticsadmin.properties.dataStreams.create", "pending", "The create response was ambiguous.", checked_at=checked_at), make_evidence("analyticsadmin.properties.dataStreams.list", "pending", "Exact-origin readback was not unique.", checked_at=rfc3339(runtime.clock()))])
            recovered = [stream for stream in client.list_web_streams(prop) if stream.get("default_uri") == origin]
            if len(recovered) != 1:
                return _ga4_pending(runtime, namespace, token, target, candidate_count=len(recovered), partial=False, evidence=[make_evidence("analyticsadmin.properties.dataStreams.create", "observed", "One stream create call completed.", checked_at=checked_at), make_evidence("analyticsadmin.properties.dataStreams.list", "pending", "Exact-origin readback was not unique.", checked_at=rfc3339(runtime.clock()))])
            return _success(runtime, namespace, status="verified", token=token, target=target, result={"kind": "write_outcome", "action": "created_stream", "resource": recovered[0]}, evidence=[make_evidence("analyticsadmin.properties.dataStreams.create", "observed", "One Web stream create call completed.", checked_at=checked_at), make_evidence("analyticsadmin.properties.dataStreams.list", "verified", "Exactly one stream matches the production origin.", checked_at=rfc3339(runtime.clock()))])

        try:
            created_property = client.create_property(
                account,
                display_name=str(payload["display_name"]),
                time_zone=str(payload["time_zone"]),
                currency_code=str(payload["currency_code"]),
            )
        except AdapterError as exc:
            if exc.error_code != "ambiguous_write":
                raise
            candidates = [
                item
                for item in client.list_properties(account)
                if item.get("display_name") == payload["display_name"]
                and item.get("time_zone") == payload["time_zone"]
                and item.get("currency_code") == payload["currency_code"]
            ]
            return _ga4_pending(runtime, namespace, token, target, candidate_count=len(candidates), partial=False, evidence=[make_evidence("analyticsadmin.properties.create", "pending", "The property create response was ambiguous and was not replayed.", checked_at=checked_at), make_evidence("analyticsadmin.properties.list", "pending", "Candidate readback is non-authoritative without an origin stream.", checked_at=rfc3339(runtime.clock()))])
        created_name = created_property.get("name")
        if not isinstance(created_name, str):
            return _ga4_pending(runtime, namespace, token, target, candidate_count=0, partial=True, evidence=[make_evidence("analyticsadmin.properties.create", "observed", "A property response lacked an immutable name.", checked_at=checked_at)])
        try:
            client.create_web_stream(created_name, display_name=str(payload["display_name"]), production_origin=origin)
        except AdapterError as exc:
            if exc.error_code != "ambiguous_write":
                raise
            streams = [stream for stream in client.list_web_streams(created_name) if stream.get("default_uri") == origin]
            if len(streams) != 1:
                return _ga4_pending(runtime, namespace, token, target, candidate_count=len(streams), partial=True, evidence=[make_evidence("analyticsadmin.properties.create", "observed", "One property was created.", checked_at=checked_at), make_evidence("analyticsadmin.properties.dataStreams.create", "pending", "The stream create response was ambiguous and was not replayed.", checked_at=rfc3339(runtime.clock()))])
        streams = [stream for stream in client.list_web_streams(created_name) if stream.get("default_uri") == origin]
        if len(streams) != 1:
            return _ga4_pending(runtime, namespace, token, target, candidate_count=len(streams), partial=True, evidence=[make_evidence("analyticsadmin.properties.create", "observed", "One property was created.", checked_at=checked_at), make_evidence("analyticsadmin.properties.dataStreams.list", "pending", "The exact-origin stream readback was not unique.", checked_at=rfc3339(runtime.clock()))])
        readback_property = client.get_property(created_name)
        return _success(runtime, namespace, status="verified", token=token, target=target, result={"kind": "write_outcome", "action": "created_property_and_stream", "resource": {"property": readback_property, "stream": streams[0]}}, evidence=[make_evidence("analyticsadmin.properties.create", "observed", "One GA4 property create call completed.", checked_at=checked_at), make_evidence("analyticsadmin.properties.dataStreams.create", "observed", "One Web stream create call completed.", checked_at=checked_at), make_evidence("analyticsadmin.properties.get", "verified", "The created property was read back by immutable name.", checked_at=rfc3339(runtime.clock())), make_evidence("analyticsadmin.properties.dataStreams.list", "verified", "Exactly one stream matches the production origin.", checked_at=rfc3339(runtime.clock()))])
    finally:
        consume_plan(namespace.plan)


def execute(argv: Sequence[str], *, runtime: Runtime | None = None) -> tuple[dict[str, object], int]:
    command = _command_hint(argv)
    try:
        namespace = build_parser().parse_args(list(argv))
    except CLIContractError as exc:
        error = AdapterError("invalid_cli", "failed", 2, "Use --help and provide only the fixed command arguments.", reason=str(exc))
        return make_envelope(command, "failed", error=error), 2
    command = namespace.command_name
    active_runtime = _runtime(namespace, runtime)
    try:
        ensure_python()
        if namespace.provider == "bootstrap":
            return _bootstrap(active_runtime, namespace)
        if namespace.provider == "auth":
            return _auth_probe(active_runtime, namespace)
        if namespace.provider == "gsc" and namespace.operation in {"list-sites", "get-site", "list-sitemaps", "get-sitemap", "inspect-url", "search-analytics"}:
            return _gsc_read(active_runtime, namespace)
        if namespace.provider == "gsc" and namespace.operation == "sitemap-plan":
            return _gsc_plan(active_runtime, namespace)
        if namespace.provider == "gsc" and namespace.operation == "sitemap-apply":
            return _gsc_apply(active_runtime, namespace)
        if namespace.provider == "ga4" and namespace.operation in {"list-account-summaries", "get-property", "list-web-streams", "realtime"}:
            return _ga4_read(active_runtime, namespace)
        if namespace.provider == "ga4" and namespace.operation == "resource-plan":
            return _ga4_plan(active_runtime, namespace)
        if namespace.provider == "ga4" and namespace.operation == "resource-apply":
            return _ga4_apply(active_runtime, namespace)
        raise AdapterError("invalid_cli", "failed", 2, "Choose a command from the fixed adapter allowlist.")
    except AdapterError as exc:
        return make_envelope(command, exc.status, clock=active_runtime.clock, error=exc), exc.exit_code
    except Exception:
        error = AdapterError("internal_error", "failed", 15, "Inspect the local adapter implementation; provider payloads and traceback were suppressed.")
        return make_envelope(command, "failed", clock=active_runtime.clock, error=error), 15


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    envelope, exit_code = execute(arguments)
    emit(envelope, sys.stdout)
    if exit_code:
        sys.stderr.write(f"adapter_error={envelope['error']['error_code']}\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
