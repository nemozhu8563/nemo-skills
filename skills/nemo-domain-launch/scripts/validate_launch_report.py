#!/usr/bin/env python3
"""Validate dual-route launch reports, completion claims, and secret boundaries."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DEPLOYMENT_MODES = {"static_pages", "saas_vercel"}
FORMAL_DOMAIN_STATUSES = {"absent", "provider_default_only", "present", "unresolved"}
ELIGIBLE_FORMAL_DOMAIN_STATUSES = {"absent", "provider_default_only"}
PROVIDER_DEFAULT_DOMAINS = {"pages.dev", "vercel.app"}
REQUIRED_ACTIONS = (
    "pages_deploy",
    "vercel_deploy",
    "custom_domain_binding",
    "dns_record_change",
    "nameserver_change",
    "dnssec_change",
    "agents_md_writeback",
)
DOMAIN_ACTIONS = (
    "custom_domain_binding",
    "dns_record_change",
    "nameserver_change",
    "dnssec_change",
)
PHASE_STATUSES = {"pending", "passed", "failed", "not_required", "missing_evidence"}
AUTH_STATUSES = {"requested", "granted", "not_granted", "not_required"}
SECRET_KEY = re.compile(
    r"(^|_)(token|password|cookie|private_key|oauth_code|callback_url|authorization_header)($|_)",
    re.I,
)
SECRET_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}", re.I),
    re.compile(r"oauth/callback\?[^\s\"']*code=", re.I),
    re.compile(r"\bcfoac_[A-Za-z0-9._-]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
)


def secret_findings(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if SECRET_KEY.search(str(key)) and child not in (None, "", [], {}):
                findings.append(f"secret-like key has a value: {child_path}")
            findings.extend(secret_findings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(secret_findings(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        for pattern in SECRET_VALUE_PATTERNS:
            if pattern.search(value):
                findings.append(f"secret-like value at {path}")
                break
    return findings


def phase_status(action: dict[str, Any], phase: str) -> str | None:
    value = action.get(phase)
    return value.get("status") if isinstance(value, dict) else None


def phase_evidence(action: dict[str, Any], phase: str) -> Any:
    value = action.get(phase)
    return value.get("evidence") if isinstance(value, dict) else None


def evidence_present(value: Any) -> bool:
    return value not in (None, "", [], {})


def action_is_complete(action: dict[str, Any]) -> bool:
    authorization = phase_status(action, "authorization")
    execution = phase_status(action, "execution")
    readback = phase_status(action, "readback")
    if execution == "passed":
        return authorization == "granted" and readback == "passed"
    if execution == "not_required":
        return authorization == "not_required" and readback == "not_required"
    return False


def action_has_completion_evidence(action: dict[str, Any]) -> bool:
    return all(evidence_present(phase_evidence(action, phase)) for phase in ("authorization", "execution", "readback"))


def action_is_not_required(action: dict[str, Any]) -> bool:
    return all(phase_status(action, phase) == "not_required" for phase in ("authorization", "execution", "readback"))


def origin_error(value: str, domain: str) -> str | None:
    parsed = urlparse(value.strip())
    try:
        port = parsed.port
    except ValueError:
        return "scope.production_origin has an invalid port"
    if parsed.scheme != "https" or not parsed.hostname:
        return "scope.production_origin must be an absolute https origin"
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        return "scope.production_origin must not contain credentials, query, or fragment"
    if parsed.path not in ("", "/"):
        return "scope.production_origin must not contain a path"
    if port is not None and not 1 <= port <= 65535:
        return "scope.production_origin has an invalid port"
    if parsed.hostname.lower().rstrip(".") != domain.lower().rstrip("."):
        return "scope.production_origin hostname must match scope.domain"
    return None


def formal_domain_error(value: str) -> str | None:
    domain = value.strip().lower().rstrip(".")
    if not domain or len(domain) > 253 or "." not in domain:
        return "scope.domain must be a public fully qualified domain name"
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        pass
    else:
        return "scope.domain must not be an IP address"
    if any(domain == suffix or domain.endswith(f".{suffix}") for suffix in PROVIDER_DEFAULT_DOMAINS):
        return "scope.domain must be a formal domain, not a provider default domain"
    labels = domain.split(".")
    if any(
        len(label) > 63
        or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label)
        for label in labels
    ):
        return "scope.domain contains an invalid DNS label"
    return None


def distinct_strings(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item).strip() for item in value if str(item).strip()}


def domain_ready_failures(payload: dict[str, Any]) -> list[str]:
    """Return evidence failures that block AGENTS.md writeback."""
    failures: list[str] = []
    scope = payload.get("scope", {})
    actions = payload.get("actions", {})
    observations = payload.get("observations", {})
    provider = observations.get("provider", {}) if isinstance(observations, dict) else {}
    public_dns = observations.get("public_dns", {}) if isinstance(observations, dict) else {}
    public_http = observations.get("public_http", {}) if isinstance(observations, dict) else {}

    if not isinstance(scope, dict):
        return ["domain_ready requires a valid scope"]
    mode = scope.get("deployment_mode")
    if mode not in DEPLOYMENT_MODES:
        failures.append("domain_ready requires deployment_mode=static_pages or saas_vercel")

    formal_domain = scope.get("formal_domain_before")
    formal_status = formal_domain.get("status") if isinstance(formal_domain, dict) else None
    if formal_status not in ELIGIBLE_FORMAL_DOMAIN_STATUSES:
        failures.append("domain_ready requires formal_domain_before.status=absent or provider_default_only")
    if not isinstance(formal_domain, dict) or not evidence_present(formal_domain.get("evidence")):
        failures.append("domain_ready requires formal_domain_before evidence")
    if str(scope.get("registrar", "")).strip().lower() != "spaceship":
        failures.append("domain_ready requires registrar=spaceship")

    active_hosting = "pages_deploy" if mode == "static_pages" else "vercel_deploy"
    inactive_hosting = "vercel_deploy" if mode == "static_pages" else "pages_deploy"
    for action_name in (active_hosting, *DOMAIN_ACTIONS):
        action = actions.get(action_name, {}) if isinstance(actions, dict) else {}
        if not isinstance(action, dict) or not action_is_complete(action):
            failures.append(f"domain_ready requires a coherent completed/no-op action: {action_name}")
        elif not action_has_completion_evidence(action):
            failures.append(f"domain_ready requires authorization/execution/readback evidence: {action_name}")
    inactive_action = actions.get(inactive_hosting, {}) if isinstance(actions, dict) else {}
    if not isinstance(inactive_action, dict) or not action_is_not_required(inactive_action):
        failures.append(f"domain_ready requires a consistent not_required triad: {inactive_hosting}")
    elif not action_has_completion_evidence(inactive_action):
        failures.append(f"domain_ready requires not_required evidence: {inactive_hosting}")

    if not isinstance(provider, dict):
        provider = {}
    active_observation = "pages_deployment" if mode == "static_pages" else "vercel_deployment"
    inactive_observation = "vercel_deployment" if mode == "static_pages" else "pages_deployment"
    if provider.get(active_observation) != "passed":
        failures.append(f"domain_ready requires provider.{active_observation}=passed")
    if provider.get(inactive_observation) != "not_required":
        failures.append(f"domain_ready requires provider.{inactive_observation}=not_required")
    for key in ("cloudflare_zone", "custom_domain", "certificate", "hosting_dns"):
        if provider.get(key) != "passed":
            failures.append(f"domain_ready requires provider.{key}=passed")

    if not isinstance(public_dns, dict):
        public_dns = {}
    if len(distinct_strings(public_dns.get("resolvers"))) < 2:
        failures.append("domain_ready requires at least two named public DNS resolvers")
    if public_dns.get("cloudflare_nameservers") is not True:
        failures.append("domain_ready requires public_dns.cloudflare_nameservers=true")
    if public_dns.get("hosting_records_match") is not True:
        failures.append("domain_ready requires public_dns.hosting_records_match=true")
    if mode == "saas_vercel" and public_dns.get("verification_records_dns_only") not in {"passed", "not_required"}:
        failures.append("domain_ready requires Vercel verification records to be DNS-only or not_required")

    if not isinstance(public_http, dict):
        public_http = {}
    for key in ("hosting_default_url", "root", "representative_path", "tls"):
        if public_http.get(key) != "passed":
            failures.append(f"domain_ready requires public_http.{key}=passed")
    for key in ("canonical", "robots", "sitemap"):
        allowed = {"passed"} if mode == "static_pages" else {"passed", "not_required"}
        if public_http.get(key) not in allowed:
            failures.append(f"domain_ready requires mode-appropriate public_http.{key}")

    missing = payload.get("missing_evidence")
    if not isinstance(missing, list):
        failures.append("domain_ready requires missing_evidence to be a list")
    elif missing:
        failures.append("domain_ready requires empty missing_evidence for scoped domain evidence")
    return failures


def validate_report(
    payload: dict[str, Any],
    *,
    require_domain_ready: bool = False,
    require_launch_complete: bool = False,
) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    required_top = ("schema_version", "scope", "actions", "rollback", "observations", "claims", "missing_evidence")
    for key in required_top:
        if key not in payload:
            failures.append(f"missing top-level field: {key}")

    failures.extend(secret_findings(payload))
    if payload.get("schema_version") != "2.0":
        failures.append("schema_version must be 2.0")

    scope = payload.get("scope", {})
    if not isinstance(scope, dict):
        failures.append("scope must be an object")
        scope = {}
    mode = scope.get("deployment_mode")
    if mode not in DEPLOYMENT_MODES:
        failures.append("scope.deployment_mode must be static_pages or saas_vercel")
    formal_domain = scope.get("formal_domain_before")
    formal_status = formal_domain.get("status") if isinstance(formal_domain, dict) else None
    if formal_status not in FORMAL_DOMAIN_STATUSES:
        failures.append("scope.formal_domain_before.status is invalid")
    for key in ("project_dir", "build_command", "production_origin", "domain", "registrar"):
        value = scope.get(key)
        if not isinstance(value, str) or not value.strip() or (value.startswith("<") and value.endswith(">")):
            failures.append(f"scope.{key} must be resolved")
    project_dir = scope.get("project_dir")
    if isinstance(project_dir, str) and project_dir and not Path(project_dir).expanduser().is_absolute():
        failures.append("scope.project_dir must be absolute")
    if mode == "static_pages":
        for key in ("pages_project", "output_dir"):
            if not isinstance(scope.get(key), str) or not str(scope.get(key)).strip():
                failures.append(f"scope.{key} must be resolved for static_pages")
        output_dir = scope.get("output_dir")
        if isinstance(output_dir, str) and output_dir and not Path(output_dir).expanduser().is_absolute():
            failures.append("scope.output_dir must be absolute for static_pages")
    elif mode == "saas_vercel":
        if not isinstance(scope.get("vercel_project"), str) or not str(scope.get("vercel_project")).strip():
            failures.append("scope.vercel_project must be resolved for saas_vercel")
    origin = scope.get("production_origin", "")
    domain = scope.get("domain", "")
    if isinstance(domain, str) and domain:
        error = formal_domain_error(domain)
        if error:
            failures.append(error)
    if isinstance(origin, str) and origin and isinstance(domain, str) and domain:
        error = origin_error(origin, domain)
        if error:
            failures.append(error)

    actions = payload.get("actions", {})
    if not isinstance(actions, dict):
        failures.append("actions must be an object")
        actions = {}
    for action_name in REQUIRED_ACTIONS:
        action = actions.get(action_name)
        if not isinstance(action, dict):
            failures.append(f"missing action: {action_name}")
            continue
        auth = phase_status(action, "authorization")
        execution = phase_status(action, "execution")
        readback = phase_status(action, "readback")
        if auth not in AUTH_STATUSES:
            failures.append(f"invalid authorization status: {action_name}")
        if execution not in PHASE_STATUSES:
            failures.append(f"invalid execution status: {action_name}")
        if readback not in PHASE_STATUSES:
            failures.append(f"invalid readback status: {action_name}")
        if execution == "passed" and auth != "granted":
            failures.append(f"{action_name} executed without granted authorization")
        if execution == "not_required" and auth != "not_required":
            failures.append(f"{action_name} execution is not_required without matching authorization")
        if auth == "not_required" and execution != "not_required":
            failures.append(f"{action_name} authorization is not_required but execution is {execution}")
        if readback == "passed" and execution != "passed":
            failures.append(f"{action_name} readback passed without successful execution")
        if readback == "not_required" and execution != "not_required":
            failures.append(f"{action_name} readback is not_required but execution is {execution}")
        if execution == "not_required" and readback != "not_required":
            failures.append(f"{action_name} not_required phases must form a consistent triad")

    rollback = payload.get("rollback", {})
    if not isinstance(rollback, dict) or not isinstance(rollback.get("last_safe_checkpoint"), str):
        failures.append("rollback.last_safe_checkpoint is required")
    if not isinstance(rollback, dict) or not isinstance(rollback.get("dns_records_before"), list):
        failures.append("rollback.dns_records_before must be a list")

    observations = payload.get("observations", {})
    provider = observations.get("provider", {}) if isinstance(observations, dict) else {}
    public_dns = observations.get("public_dns", {}) if isinstance(observations, dict) else {}
    agents_observation = observations.get("agents_md", {}) if isinstance(observations, dict) else {}
    claims = payload.get("claims", {})
    if not isinstance(claims, dict):
        failures.append("claims must be an object")
        claims = {}
    for key in ("domain_ready", "launch_complete", "dnssec_complete"):
        if not isinstance(claims.get(key), bool):
            failures.append(f"claims.{key} must be boolean")
    domain_ready = claims.get("domain_ready") is True
    launch_complete = claims.get("launch_complete") is True
    dnssec_complete = claims.get("dnssec_complete") is True

    if domain_ready:
        failures.extend(domain_ready_failures(payload))
    if require_domain_ready and not domain_ready:
        failures.append("domain_ready is required but not claimed")

    if launch_complete:
        if not domain_ready:
            failures.append("launch_complete requires domain_ready=true")
        writeback = actions.get("agents_md_writeback", {})
        if not isinstance(writeback, dict) or not action_is_complete(writeback):
            failures.append("launch_complete requires completed agents_md_writeback")
        elif not action_has_completion_evidence(writeback):
            failures.append("launch_complete requires agents_md_writeback evidence")
        if not isinstance(agents_observation, dict) or agents_observation.get("status") != "passed":
            failures.append("launch_complete requires observations.agents_md.status=passed")
        expected_path = (Path(str(scope.get("project_dir", ""))).expanduser() / "AGENTS.md").resolve()
        observed_path = agents_observation.get("path") if isinstance(agents_observation, dict) else None
        if not isinstance(observed_path, str) or not Path(observed_path).expanduser().is_absolute():
            failures.append("launch_complete requires observations.agents_md.path at project root")
        elif Path(observed_path).expanduser().resolve() != expected_path:
            failures.append("launch_complete requires observations.agents_md.path at project root")
        if isinstance(agents_observation, dict) and agents_observation.get("managed_block") != "nemo-domain-launch":
            failures.append("launch_complete requires the nemo-domain-launch managed block")
    if require_launch_complete and not launch_complete:
        failures.append("launch_complete is required but not claimed")

    if dnssec_complete:
        dnssec_action = actions.get("dnssec_change", {})
        if not isinstance(dnssec_action, dict) or not action_is_complete(dnssec_action) or phase_status(dnssec_action, "execution") != "passed":
            failures.append("dnssec_complete requires an executed dnssec_change action with passed readback")
        if not isinstance(provider, dict) or provider.get("cloudflare_dnssec") != "passed":
            failures.append("dnssec_complete requires provider.cloudflare_dnssec=passed")
        if not isinstance(public_dns, dict) or public_dns.get("ds_present") is not True:
            failures.append("dnssec_complete requires public_dns.ds_present=true")
        resolvers = public_dns.get("dnssec_ad_resolvers") if isinstance(public_dns, dict) else None
        if len(distinct_strings(resolvers)) < 2:
            failures.append("dnssec_complete requires at least two DNSSEC AD resolvers")

    if not domain_ready:
        warnings.append("domain_ready is not proven")
    if not launch_complete:
        warnings.append("launch_complete is not proven")
    if not dnssec_complete:
        warnings.append("dnssec_complete is not proven or not requested")
    return {"ok": not failures, "failures": failures, "warnings": warnings}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report")
    parser.add_argument("--require-domain-ready", action="store_true")
    parser.add_argument("--require-launch-complete", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    path = Path(args.report).expanduser().resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result = {"ok": False, "failures": [str(exc)], "warnings": []}
    else:
        result = validate_report(
            payload if isinstance(payload, dict) else {},
            require_domain_ready=args.require_domain_ready,
            require_launch_complete=args.require_launch_complete,
        )
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if not result["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
