#!/usr/bin/env python3
"""Validate a redacted nemo-supabase-auth execution report."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit, urlunsplit


ACTIONS = (
    "application_code",
    "google_cloud_project",
    "google_auth_configuration",
    "google_oauth_client",
    "supabase_google_provider",
    "supabase_url_configuration",
    "real_login_test",
)
CONFIGURATION_ACTIONS = ACTIONS[:-1]
FORBIDDEN_KEYS = {
    "secret",
    "client_secret",
    "password",
    "token",
    "access_token",
    "refresh_token",
    "id_token",
    "oauth_code",
    "authorization_code",
    "cookie",
    "cookies",
    "session_id",
    "email",
    "user_id",
    "google_subject",
    "browser_storage",
    "local_storage",
    "session_storage",
    "authorization_header",
    "raw_callback_url",
}
EMAIL_PATTERN = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
GOOGLE_CREDENTIAL_PATTERN = re.compile(r"\bGOCSPX-[A-Za-z0-9_-]{12,}\b")
JWT_PATTERN = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~-]{12,}")
RUNTIME_QUERY_PATTERN = re.compile(r"(?i)[?&](?:code|access_token|refresh_token|id_token|token)=")


def load_report(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to read report: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("report root must be a JSON object")
    return payload


def walk(value: Any, path: str = "$") -> Iterable[tuple[str, str | None, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield child_path, str(key), child
            yield from walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, None, child
            yield from walk(child, child_path)


def scan_sensitive_data(report: dict[str, Any], failures: list[str]) -> None:
    for path, key, value in walk(report):
        if key and key.lower().replace("-", "_") in FORBIDDEN_KEYS:
            failures.append(f"forbidden sensitive key at {path}")
        if not isinstance(value, str):
            continue
        if EMAIL_PATTERN.search(value):
            failures.append(f"email-like personal data at {path}")
        if GOOGLE_CREDENTIAL_PATTERN.search(value):
            failures.append(f"Google credential-like value at {path}")
        if JWT_PATTERN.search(value):
            failures.append(f"JWT-like value at {path}")
        if BEARER_PATTERN.search(value):
            failures.append(f"Bearer credential-like value at {path}")
        if RUNTIME_QUERY_PATTERN.search(value):
            failures.append(f"runtime OAuth query data at {path}")


def as_object(value: Any, label: str, failures: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        failures.append(f"{label} must be an object")
        return {}
    return value


def as_string_list(value: Any, label: str, failures: list[str], allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty) or not all(isinstance(item, str) for item in value):
        failures.append(f"{label} must be {'a' if allow_empty else 'a non-empty'} string list")
        return []
    return list(value)


def normalized_origin(value: str) -> str | None:
    if "*" in value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
        return None
    if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "[::1]", "::1"}:
        return None
    return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))


def validate_static_url(value: str, label: str, failures: list[str], require_path: bool = False) -> None:
    if "*" in value:
        failures.append(f"{label} must be exact; preview wildcards belong in preview_patterns")
        return
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        failures.append(f"{label} must be an absolute http(s) URL without userinfo")
        return
    if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "[::1]", "::1"}:
        failures.append(f"{label} uses insecure HTTP for a non-local host")
    if parsed.query or parsed.fragment:
        failures.append(f"{label} must not contain query or fragment data")
    if require_path and parsed.path in {"", "/"}:
        failures.append(f"{label} must contain an application callback path")


def validate_preview_patterns(
    patterns: list[str], production_origin: str | None, reviewed: bool, failures: list[str]
) -> None:
    if patterns and not reviewed:
        failures.append("preview_patterns require explicit current-doc review")
    production_host = urlsplit(production_origin or "").hostname
    for index, value in enumerate(patterns):
        label = f"url_matrix.preview_patterns[{index}]"
        if "*" not in value:
            failures.append(f"{label} must contain a justified preview wildcard or be moved to exact redirects")
        if "?" in value or "#" in value:
            failures.append(f"{label} must not contain query or fragment data")
        if not value.startswith(("https://", "http://localhost", "http://127.0.0.1")):
            failures.append(f"{label} must be an HTTPS preview pattern or local pattern")
        if production_host and production_host in value:
            failures.append(f"{label} must not wildcard the production host")


def validate_url_matrix(report: dict[str, Any], failures: list[str]) -> None:
    scope = as_object(report.get("scope"), "scope", failures)
    matrix = as_object(report.get("url_matrix"), "url_matrix", failures)
    auth_origin = scope.get("supabase_auth_origin")
    if not isinstance(auth_origin, str) or normalized_origin(auth_origin) != auth_origin:
        failures.append("scope.supabase_auth_origin must be a canonical origin without a trailing slash")
        auth_origin = None

    origins = as_string_list(matrix.get("google_javascript_origins"), "url_matrix.google_javascript_origins", failures)
    for index, value in enumerate(origins):
        if normalized_origin(value) != value:
            failures.append(f"url_matrix.google_javascript_origins[{index}] must be an origin only without trailing slash")
    if auth_origin and auth_origin not in origins:
        failures.append("Google JavaScript origins must include the scoped Supabase Auth origin")

    google_redirects = as_string_list(matrix.get("google_redirect_uris"), "url_matrix.google_redirect_uris", failures)
    expected_provider_callback = f"{auth_origin}/auth/v1/callback" if auth_origin else None
    for index, value in enumerate(google_redirects):
        validate_static_url(value, f"url_matrix.google_redirect_uris[{index}]", failures, require_path=True)
        if urlsplit(value).path != "/auth/v1/callback":
            failures.append(f"url_matrix.google_redirect_uris[{index}] is not a Supabase provider callback")
    if expected_provider_callback and expected_provider_callback not in google_redirects:
        failures.append("Google redirect URIs must include the exact scoped Supabase provider callback")

    site_url = matrix.get("supabase_site_url")
    if not isinstance(site_url, str) or normalized_origin(site_url) != site_url:
        failures.append("url_matrix.supabase_site_url must be a canonical application origin")
        site_url = None
    if site_url and auth_origin and site_url == auth_origin:
        failures.append("Supabase Site URL must be the application origin, not the Supabase Auth origin")

    app_redirects = as_string_list(matrix.get("supabase_redirect_urls"), "url_matrix.supabase_redirect_urls", failures)
    for index, value in enumerate(app_redirects):
        validate_static_url(value, f"url_matrix.supabase_redirect_urls[{index}]", failures, require_path=True)
        if urlsplit(value).path == "/auth/v1/callback":
            failures.append(f"url_matrix.supabase_redirect_urls[{index}] conflates the provider callback with the app callback")
        if expected_provider_callback and value == expected_provider_callback:
            failures.append("Supabase Redirect URLs must not contain the Google provider callback")

    redirect_to = as_string_list(matrix.get("application_redirect_to"), "url_matrix.application_redirect_to", failures)
    for index, value in enumerate(redirect_to):
        validate_static_url(value, f"url_matrix.application_redirect_to[{index}]", failures, require_path=True)
        if value not in app_redirects:
            failures.append(f"url_matrix.application_redirect_to[{index}] is not in the Supabase redirect allowlist")

    preview_patterns = as_string_list(
        matrix.get("preview_patterns", []), "url_matrix.preview_patterns", failures, allow_empty=True
    )
    observations = as_object(report.get("observations"), "observations", failures)
    supabase_observation = as_object(observations.get("supabase"), "observations.supabase", failures)
    validate_preview_patterns(
        preview_patterns,
        site_url,
        supabase_observation.get("preview_patterns_reviewed") is True,
        failures,
    )


def validate_actions(report: dict[str, Any], failures: list[str]) -> dict[str, dict[str, Any]]:
    actions = as_object(report.get("actions"), "actions", failures)
    normalized: dict[str, dict[str, Any]] = {}
    for name in ACTIONS:
        action = as_object(actions.get(name), f"actions.{name}", failures)
        normalized[name] = action
        for section in ("authorization", "execution", "readback"):
            node = as_object(action.get(section), f"actions.{name}.{section}", failures)
            if not isinstance(node.get("status"), str):
                failures.append(f"actions.{name}.{section}.status must be a string")
        rollback = action.get("rollback")
        if not isinstance(rollback, str) or not rollback.strip():
            failures.append(f"actions.{name}.rollback must describe an exact recovery boundary")
    unknown = sorted(set(actions) - set(ACTIONS))
    if unknown:
        failures.append(f"unknown action keys: {', '.join(unknown)}")
    return normalized


def action_supports_ready(action: dict[str, Any]) -> bool:
    authorization = action.get("authorization", {}).get("status")
    execution = action.get("execution", {}).get("status")
    readback = action.get("readback", {}).get("status")
    mutated = authorization == "authorized" and execution == "succeeded" and readback == "verified"
    reused = authorization == "not_required" and execution == "not_required" and readback == "verified"
    return mutated or reused


def all_true(node: dict[str, Any], keys: tuple[str, ...]) -> bool:
    return all(node.get(key) is True for key in keys)


def validate_claims(
    report: dict[str, Any], actions: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    claims = as_object(report.get("claims"), "claims", failures)
    configuration_ready = claims.get("configuration_ready")
    end_to_end = claims.get("end_to_end_verified")
    if not isinstance(configuration_ready, bool) or not isinstance(end_to_end, bool):
        failures.append("claims must contain boolean configuration_ready and end_to_end_verified")
        return
    if end_to_end and not configuration_ready:
        failures.append("end_to_end_verified requires configuration_ready")

    observations = as_object(report.get("observations"), "observations", failures)
    sources = as_object(observations.get("official_sources"), "observations.official_sources", failures)
    application = as_object(observations.get("application"), "observations.application", failures)
    google = as_object(observations.get("google"), "observations.google", failures)
    supabase = as_object(observations.get("supabase"), "observations.supabase", failures)
    browser = as_object(observations.get("browser"), "observations.browser", failures)

    if configuration_ready:
        unsupported_actions = [name for name in CONFIGURATION_ACTIONS if not action_supports_ready(actions.get(name, {}))]
        if unsupported_actions:
            failures.append(f"configuration_ready lacks terminal action evidence: {', '.join(unsupported_actions)}")
        if not all_true(
            sources,
            ("supabase_google_guide_current", "supabase_redirect_guide_current", "supabase_changelog_reviewed"),
        ):
            failures.append("configuration_ready requires current Supabase official-source review")
        if not all_true(
            application,
            (
                "login_initiation_verified",
                "pkce_exchange_verified",
                "safe_relative_next_verified",
                "trusted_server_check_present",
            ),
        ) or application.get("project_native_checks") != "passed":
            failures.append("configuration_ready requires application preflight and project-native checks")
        if not all_true(
            google,
            (
                "exact_project_verified",
                "web_client_type_verified",
                "origins_match",
                "redirect_uris_match",
                "audience_and_publication_verified",
                "minimum_scopes_only",
            ),
        ):
            failures.append("configuration_ready requires complete Google provider readback")
        if not all_true(
            supabase,
            (
                "exact_project_verified",
                "provider_enabled",
                "client_identifier_matches",
                "credential_present",
                "site_url_matches",
                "redirect_urls_match",
                "preview_patterns_reviewed",
            ),
        ):
            failures.append("configuration_ready requires complete Supabase provider and URL readback")

    missing = report.get("missing_evidence")
    if not isinstance(missing, list) or not all(isinstance(item, str) for item in missing):
        failures.append("missing_evidence must be a string list")
        missing = []

    if end_to_end:
        real_login = actions.get("real_login_test", {})
        if not action_supports_ready(real_login) or real_login.get("authorization", {}).get("status") != "authorized":
            failures.append("end_to_end_verified requires an authorized, succeeded, and verified real_login_test")
        if not all_true(
            browser,
            (
                "expected_google_surface",
                "callback_chain_completed",
                "trusted_user_verified",
                "protected_route_verified",
                "logout_negative_verified",
            ),
        ):
            failures.append("end_to_end_verified requires the full browser and protected-session ladder")
        if missing:
            failures.append("end_to_end_verified requires an empty missing_evidence list")


def validate(report: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if report.get("schema_version") != "1.0":
        failures.append("schema_version must be 1.0")
    scan_sensitive_data(report, failures)
    validate_url_matrix(report, failures)
    actions = validate_actions(report, failures)
    validate_claims(report, actions, failures)
    return {"ok": not failures, "failures": sorted(set(failures))}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a redacted nemo-supabase-auth execution report.")
    parser.add_argument("report", help="Path to the JSON report.")
    parser.add_argument("--require-configuration-ready", action="store_true")
    parser.add_argument("--require-end-to-end", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        report = load_report(Path(args.report))
        result = validate(report)
    except ValueError as exc:
        result = {"ok": False, "failures": [str(exc)]}
        report = {}
    claims = report.get("claims", {}) if isinstance(report, dict) else {}
    if args.require_configuration_ready and claims.get("configuration_ready") is not True:
        result["ok"] = False
        result["failures"].append("configuration_ready is required")
    if args.require_end_to_end and claims.get("end_to_end_verified") is not True:
        result["ok"] = False
        result["failures"].append("end_to_end_verified is required")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
