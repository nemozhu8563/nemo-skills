#!/usr/bin/env python3
"""Deterministic state and evidence gates for the web-business pipeline.

This CLI never buys, publishes, deploys, changes DNS, or calls analytics
providers. It only creates and validates local durable project records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 2
ARTIFACTS = {
    "candidate": "candidate-lock.json",
    "state": "pipeline-state.json",
    "matrix": "page-matrix.json",
    "evidence": "evidence-pack.json",
    "content": "content-manifest.json",
    "launch": "launch-report.json",
    "analytics": "analytics-snapshot.json",
    "decision_log": "decision-log.md",
}

STAGE_TRANSITIONS = {
    "candidate_locked": ("planned",),
    "planned": ("researched",),
    "researched": ("build_ready",),
    "build_ready": ("local_verified",),
    "local_verified": ("deploy_ready",),
    "deploy_ready": ("deployed",),
    "deployed": ("telemetry_verified",),
    "telemetry_verified": ("observing",),
    "observing": ("grow", "hold", "retire"),
    "hold": ("observing", "retire"),
    "grow": ("observing", "templated"),
    "retire": (),
    "templated": (),
}

STAGE_LEVEL = {
    "candidate_locked": 0,
    "planned": 1,
    "researched": 2,
    "build_ready": 3,
    "local_verified": 4,
    "deploy_ready": 5,
    "deployed": 6,
    "telemetry_verified": 7,
    "observing": 8,
    "grow": 9,
    "hold": 9,
    "retire": 9,
    "templated": 10,
}

EXTERNAL_ACTIONS = (
    "domain_purchase",
    "dns_change",
    "git_push",
    "deployment",
    "gsc_setup",
    "ga_setup",
    "advertising_application",
)

TRUSTED_SOURCE_LEVELS = {"official", "trusted"}
REQUIRED_LOCAL_CHECKS = {
    "build",
    "lint",
    "tests",
    "links",
    "assets",
    "visual",
    "content_review",
}

SECRET_PATTERNS = (
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github_token", re.compile(r"\bgh[oprsu]_[A-Za-z0-9]{20,}\b")),
    (
        "credential_assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|password|client[_-]?secret)\b"
            r"\s*[:=]\s*[\"']?[A-Za-z0-9_./+=-]{12,}"
        ),
    ),
)


class PipelineError(Exception):
    """Expected user-facing pipeline error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: Any, label: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty ISO-8601 timestamp")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label} is not a valid ISO-8601 timestamp")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{label} must include a timezone")
        return None
    return parsed


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PipelineError(f"missing artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PipelineError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise PipelineError(f"top-level JSON must be an object: {path}")
    return data


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        handle.write(payload)
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_sha256(data: dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(payload.encode("utf-8"))


def artifact_path(project_dir: Path, key: str) -> Path:
    return project_dir / ARTIFACTS[key]


def is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def normalize_keyword(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", normalized).strip()


def ensure_string_list(value: Any, label: str, errors: list[str], allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        errors.append(f"{label} must be {'a' if allow_empty else 'a non-empty'} list")
        return []
    result: list[str] = []
    for index, item in enumerate(value):
        if not is_nonempty_string(item):
            errors.append(f"{label}[{index}] must be a non-empty string")
        else:
            result.append(item.strip())
    return result


def validate_schema_version(data: dict[str, Any], label: str, errors: list[str]) -> None:
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{label}.schema_version must equal {SCHEMA_VERSION}")


def validate_candidate(candidate: dict[str, Any], locked: bool = True) -> list[str]:
    errors: list[str] = []
    if locked:
        validate_schema_version(candidate, "candidate-lock", errors)
    if candidate.get("example_only") is True:
        errors.append("candidate example_only must be removed after replacing every example value")
    key = candidate.get("key")
    if not is_nonempty_string(key) or re.fullmatch(
        r"[a-z][a-z0-9-]*:[a-z0-9][a-z0-9-]*", key
    ) is None:
        errors.append("candidate key must be a non-empty <namespace>:<slug> value")
    if not is_nonempty_string(candidate.get("name")):
        errors.append("candidate name is required")
    if not is_nonempty_string(candidate.get("source_report")):
        errors.append("candidate source_report is required")

    identities = candidate.get("identities")
    if not isinstance(identities, list) or not identities:
        errors.append("candidate identities must contain at least one stable identity")
    else:
        seen_identities: set[tuple[str, str]] = set()
        for index, item in enumerate(identities):
            if not isinstance(item, dict):
                errors.append(f"identities[{index}] must be an object")
                continue
            provider = item.get("provider")
            identity_id = item.get("id")
            if not is_nonempty_string(provider) or not is_nonempty_string(identity_id):
                errors.append(f"identities[{index}] requires non-empty provider and id")
                continue
            identity = (provider.casefold(), identity_id.casefold())
            if identity in seen_identities:
                errors.append(f"duplicate candidate identity: {provider}:{identity_id}")
            seen_identities.add(identity)

    qualification = candidate.get("qualification")
    if not isinstance(qualification, dict):
        errors.append("candidate qualification must be an object")
    else:
        if qualification.get("status") != "qualified":
            errors.append("qualification.status must be qualified")
        if not is_nonempty_string(qualification.get("method")):
            errors.append("qualification.method is required")
        parse_timestamp(qualification.get("checked_at"), "qualification.checked_at", errors)
        checks = qualification.get("checks")
        if not isinstance(checks, list) or not checks:
            errors.append("qualification.checks must be a non-empty list")
        else:
            check_ids: set[str] = set()
            for index, check in enumerate(checks):
                if not isinstance(check, dict):
                    errors.append(f"qualification.checks[{index}] must be an object")
                    continue
                check_id = check.get("check_id")
                if not is_nonempty_string(check_id):
                    errors.append(f"qualification.checks[{index}].check_id is required")
                elif check_id in check_ids:
                    errors.append(f"duplicate qualification check_id: {check_id}")
                else:
                    check_ids.add(check_id)
                if not is_nonempty_string(check.get("criterion")):
                    errors.append(f"qualification check {check_id!r}.criterion is required")
                if check.get("status") != "passed":
                    errors.append(f"qualification check {check_id!r}.status must be passed")
                ensure_string_list(
                    check.get("evidence_refs"),
                    f"qualification check {check_id!r}.evidence_refs",
                    errors,
                )
                if not isinstance(check.get("observations"), dict):
                    errors.append(
                        f"qualification check {check_id!r}.observations must be an object"
                    )

    hypothesis = candidate.get("business_hypothesis")
    if not isinstance(hypothesis, dict):
        errors.append("candidate business_hypothesis must be an object")
    else:
        for field in (
            "target_customer",
            "customer_problem",
            "value_proposition",
            "primary_acquisition_channel",
            "primary_value_event",
            "riskiest_assumption",
        ):
            if not is_nonempty_string(hypothesis.get(field)):
                errors.append(f"business_hypothesis.{field} is required")
        ensure_string_list(
            hypothesis.get("business_models"),
            "business_hypothesis.business_models",
            errors,
        )
        ensure_string_list(
            hypothesis.get("unknowns"),
            "business_hypothesis.unknowns",
            errors,
        )

    if locked:
        parse_timestamp(candidate.get("locked_at"), "candidate-lock.locked_at", errors)
        decision = candidate.get("decision")
        if not isinstance(decision, dict):
            errors.append("candidate-lock.decision must be an object")
        else:
            if decision.get("status") != "approved":
                errors.append("candidate-lock.decision.status must be approved")
            if not is_nonempty_string(decision.get("approved_by")):
                errors.append("candidate-lock.decision.approved_by is required")
            if decision.get("confirmed_key") != key:
                errors.append("candidate-lock.decision.confirmed_key must exactly match key")
            if not is_nonempty_string(decision.get("rationale")):
                errors.append("candidate-lock.decision.rationale is required")
    return errors


def validate_state(state: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_schema_version(state, "pipeline-state", errors)
    if state.get("candidate_key") != candidate.get("key"):
        errors.append("pipeline-state.candidate_key does not match candidate-lock.key")
    if state.get("candidate_identity") != canonical_json_sha256(
        {"key": candidate.get("key"), "identities": candidate.get("identities")}
    ):
        errors.append("pipeline-state.candidate_identity does not match the locked candidate identity")
    if state.get("candidate_lock_sha256") != canonical_json_sha256(candidate):
        errors.append("candidate-lock.json changed after initialization")
    stage = state.get("current_stage")
    if stage not in STAGE_TRANSITIONS:
        errors.append(f"pipeline-state.current_stage is invalid: {stage!r}")
    parse_timestamp(state.get("updated_at"), "pipeline-state.updated_at", errors)
    history = state.get("history")
    if not isinstance(history, list) or not history:
        errors.append("pipeline-state.history must be a non-empty list")
    else:
        for index, event in enumerate(history):
            if not isinstance(event, dict):
                errors.append(f"history[{index}] must be an object")
                continue
            if event.get("event") not in {
                "transition",
                "authorization_granted",
                "authorization_revoked",
            }:
                errors.append(f"history[{index}].event is invalid")
            parse_timestamp(event.get("at"), f"history[{index}].at", errors)
            if not is_nonempty_string(event.get("actor")):
                errors.append(f"history[{index}].actor is required")
            if not is_nonempty_string(event.get("reason")):
                errors.append(f"history[{index}].reason is required")
    authorizations = state.get("authorizations")
    if not isinstance(authorizations, list):
        errors.append("pipeline-state.authorizations must be a list")
    else:
        ids: set[str] = set()
        for index, auth in enumerate(authorizations):
            if not isinstance(auth, dict):
                errors.append(f"authorizations[{index}] must be an object")
                continue
            auth_id = auth.get("authorization_id")
            if not is_nonempty_string(auth_id):
                errors.append(f"authorizations[{index}].authorization_id is required")
            elif auth_id in ids:
                errors.append(f"duplicate authorization_id: {auth_id}")
            else:
                ids.add(auth_id)
            if auth.get("action") not in EXTERNAL_ACTIONS:
                errors.append(f"authorizations[{index}].action is invalid")
            if auth.get("status") not in {"granted", "revoked"}:
                errors.append(f"authorizations[{index}].status must be granted or revoked")
            if not is_nonempty_string(auth.get("granted_by")):
                errors.append(f"authorizations[{index}].granted_by is required")
            if not is_nonempty_string(auth.get("scope")):
                errors.append(f"authorizations[{index}].scope is required")
            if not is_nonempty_string(auth.get("user_instruction")):
                errors.append(f"authorizations[{index}].user_instruction is required")
            parse_timestamp(auth.get("granted_at"), f"authorizations[{index}].granted_at", errors)
            if auth.get("expires_at") is not None:
                parse_timestamp(auth.get("expires_at"), f"authorizations[{index}].expires_at", errors)
    return errors


def validate_page_matrix(matrix: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_schema_version(matrix, "page-matrix", errors)
    if matrix.get("candidate_key") != candidate.get("key"):
        errors.append("page-matrix.candidate_key does not match candidate-lock.key")
    base_locale = matrix.get("base_locale")
    if not is_nonempty_string(base_locale):
        errors.append("page-matrix.base_locale is required")

    locales = matrix.get("locales")
    locale_map: dict[str, dict[str, Any]] = {}
    if not isinstance(locales, list) or not locales:
        errors.append("page-matrix.locales must be a non-empty list")
    else:
        for index, locale in enumerate(locales):
            if not isinstance(locale, dict) or not is_nonempty_string(locale.get("locale")):
                errors.append(f"locales[{index}] requires a locale")
                continue
            code = locale["locale"]
            if code in locale_map:
                errors.append(f"duplicate locale: {code}")
            locale_map[code] = locale
            if code != base_locale:
                if not locale.get("demand_validated"):
                    errors.append(f"locale {code} requires demand_validated=true")
                if not ensure_string_list(
                    locale.get("demand_evidence"), f"locale {code}.demand_evidence", errors
                ):
                    pass
                if not locale.get("content_complete"):
                    errors.append(f"locale {code} requires content_complete=true")

    pages = matrix.get("pages")
    if not isinstance(pages, list) or not pages:
        errors.append("page-matrix.pages must be a non-empty list")
        return errors
    page_ids: set[str] = set()
    slugs: dict[str, str] = {}
    intent_keys: dict[str, str] = {}
    keyword_owners: dict[str, str] = {}
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            errors.append(f"pages[{index}] must be an object")
            continue
        page_id = page.get("page_id")
        if not is_nonempty_string(page_id):
            errors.append(f"pages[{index}].page_id is required")
            continue
        if page_id in page_ids:
            errors.append(f"duplicate page_id: {page_id}")
        page_ids.add(page_id)
        for field in ("slug", "page_type", "primary_keyword", "intent_key", "search_intent", "user_goal"):
            if not is_nonempty_string(page.get(field)):
                errors.append(f"page {page_id}.{field} is required")
        slug = normalize_keyword(str(page.get("slug", "")))
        if slug:
            if slug in slugs:
                errors.append(f"duplicate page slug: pages {slugs[slug]} and {page_id}")
            slugs[slug] = page_id
        intent_key = normalize_keyword(str(page.get("intent_key", "")))
        if intent_key:
            if intent_key in intent_keys:
                errors.append(
                    f"keyword cannibalization: pages {intent_keys[intent_key]} and {page_id} share intent_key"
                )
            intent_keys[intent_key] = page_id
        aliases = ensure_string_list(
            page.get("keyword_aliases", []), f"page {page_id}.keyword_aliases", errors, allow_empty=True
        )
        keywords = [str(page.get("primary_keyword", "")), *aliases]
        for keyword in keywords:
            normalized = normalize_keyword(keyword)
            if not normalized:
                continue
            owner = keyword_owners.get(normalized)
            if owner and owner != page_id:
                errors.append(
                    f"keyword cannibalization: {keyword!r} belongs to both pages {owner} and {page_id}"
                )
            keyword_owners[normalized] = page_id
        locale = page.get("locale")
        if locale not in locale_map:
            errors.append(f"page {page_id}.locale is not declared in page-matrix.locales")
        for field in ("allowed_fields", "allowed_actions", "allowed_states", "non_goals"):
            ensure_string_list(page.get(field), f"page {page_id}.{field}", errors, allow_empty=True)
    return errors


def validate_evidence_pack(
    evidence: dict[str, Any], candidate: dict[str, Any], matrix: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    validate_schema_version(evidence, "evidence-pack", errors)
    if evidence.get("candidate_key") != candidate.get("key"):
        errors.append("evidence-pack.candidate_key does not match candidate-lock.key")
    pages = matrix.get("pages") if isinstance(matrix.get("pages"), list) else []
    page_ids = {page.get("page_id") for page in pages if isinstance(page, dict)}

    sources = evidence.get("sources")
    source_map: dict[str, dict[str, Any]] = {}
    if not isinstance(sources, list) or not sources:
        errors.append("evidence-pack.sources must be a non-empty list")
    else:
        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                errors.append(f"sources[{index}] must be an object")
                continue
            source_id = source.get("source_id")
            if not is_nonempty_string(source_id):
                errors.append(f"sources[{index}].source_id is required")
                continue
            if source_id in source_map:
                errors.append(f"duplicate source_id: {source_id}")
            source_map[source_id] = source
            for field in ("url", "title"):
                if not is_nonempty_string(source.get(field)):
                    errors.append(f"source {source_id}.{field} is required")
            if is_nonempty_string(source.get("url")) and re.match(r"^https?://", source["url"], re.I) is None:
                errors.append(f"source {source_id}.url must use http or https")
            if source.get("reliability") not in {"official", "trusted", "community", "unverified"}:
                errors.append(f"source {source_id}.reliability is invalid")
            parse_timestamp(source.get("retrieved_at"), f"source {source_id}.retrieved_at", errors)
            if source.get("current_as_of") is not None:
                parse_timestamp(source.get("current_as_of"), f"source {source_id}.current_as_of", errors)

    page_evidence = evidence.get("page_evidence")
    coverage: dict[str, list[str]] = {}
    if not isinstance(page_evidence, list):
        errors.append("evidence-pack.page_evidence must be a list")
    else:
        for index, item in enumerate(page_evidence):
            if not isinstance(item, dict) or item.get("page_id") not in page_ids:
                errors.append(f"page_evidence[{index}] references an unknown page")
                continue
            page_id = item["page_id"]
            if page_id in coverage:
                errors.append(f"duplicate page_evidence entry for {page_id}")
            source_ids = ensure_string_list(item.get("source_ids"), f"page_evidence {page_id}.source_ids", errors)
            distinct = list(dict.fromkeys(source_ids))
            coverage[page_id] = distinct
            if len(distinct) < 2:
                errors.append(f"page {page_id} requires at least two distinct sources")
            for source_id in distinct:
                if source_id not in source_map:
                    errors.append(f"page {page_id} references unknown source {source_id}")
    for page_id in page_ids:
        if page_id not in coverage:
            errors.append(f"page {page_id} has no page_evidence entry")

    claims = evidence.get("claims")
    claim_ids: set[str] = set()
    if not isinstance(claims, list):
        errors.append("evidence-pack.claims must be a list")
    else:
        for index, claim in enumerate(claims):
            if not isinstance(claim, dict):
                errors.append(f"claims[{index}] must be an object")
                continue
            claim_id = claim.get("claim_id")
            if not is_nonempty_string(claim_id):
                errors.append(f"claims[{index}].claim_id is required")
                continue
            if claim_id in claim_ids:
                errors.append(f"duplicate claim_id: {claim_id}")
            claim_ids.add(claim_id)
            page_id = claim.get("page_id")
            if page_id not in page_ids:
                errors.append(f"claim {claim_id} references unknown page {page_id}")
            if not is_nonempty_string(claim.get("text")):
                errors.append(f"claim {claim_id}.text is required")
            claim_type = claim.get("claim_type")
            if not is_nonempty_string(claim_type):
                errors.append(f"claim {claim_id}.claim_type is required")
            evidence_requirement = claim.get("evidence_requirement")
            if evidence_requirement not in {"standard", "current_trusted"}:
                errors.append(f"claim {claim_id}.evidence_requirement is invalid")
            if claim.get("status") not in {"verified", "provisional", "rejected"}:
                errors.append(f"claim {claim_id}.status is invalid")
            source_ids = ensure_string_list(claim.get("source_ids"), f"claim {claim_id}.source_ids", errors)
            resolved_sources = [source_map[source_id] for source_id in source_ids if source_id in source_map]
            for source_id in source_ids:
                if source_id not in source_map:
                    errors.append(f"claim {claim_id} references unknown source {source_id}")
            if evidence_requirement == "current_trusted":
                current_trusted = [
                    source
                    for source in resolved_sources
                    if source.get("reliability") in TRUSTED_SOURCE_LEVELS
                    and source.get("current_as_of") is not None
                ]
                if not current_trusted:
                    errors.append(
                        f"current-trusted claim {claim_id} requires a current official or trusted source"
                    )
                if claim.get("status") != "verified":
                    errors.append(f"current-trusted claim {claim_id}.status must be verified")
                parse_timestamp(claim.get("verified_at"), f"claim {claim_id}.verified_at", errors)
            elif claim.get("status") == "verified":
                parse_timestamp(claim.get("verified_at"), f"claim {claim_id}.verified_at", errors)
    return errors


def safe_content_path(project_dir: Path, raw_path: Any, label: str, errors: list[str]) -> Path | None:
    if not is_nonempty_string(raw_path):
        errors.append(f"{label} is required")
        return None
    path = Path(raw_path)
    if path.is_absolute() or ".." in path.parts:
        errors.append(f"{label} must be a safe project-relative path")
        return None
    return project_dir / path


def validate_content_manifest(
    content: dict[str, Any],
    candidate: dict[str, Any],
    matrix: dict[str, Any],
    evidence: dict[str, Any],
    project_dir: Path,
    require_files: bool,
) -> list[str]:
    errors: list[str] = []
    validate_schema_version(content, "content-manifest", errors)
    if content.get("candidate_key") != candidate.get("key"):
        errors.append("content-manifest.candidate_key does not match candidate-lock.key")
    matrix_pages = {
        page.get("page_id"): page
        for page in matrix.get("pages", [])
        if isinstance(page, dict) and is_nonempty_string(page.get("page_id"))
    }
    source_ids = {
        source.get("source_id")
        for source in evidence.get("sources", [])
        if isinstance(source, dict)
    }
    claim_map = {
        claim.get("claim_id"): claim
        for claim in evidence.get("claims", [])
        if isinstance(claim, dict) and is_nonempty_string(claim.get("claim_id"))
    }
    claim_ids = set(claim_map)
    claims_by_page: dict[str, set[str]] = {}
    for claim in evidence.get("claims", []):
        if (
            isinstance(claim, dict)
            and is_nonempty_string(claim.get("claim_id"))
            and claim.get("status") != "rejected"
        ):
            claims_by_page.setdefault(str(claim.get("page_id")), set()).add(claim["claim_id"])
    pages = content.get("pages")
    if not isinstance(pages, list) or not pages:
        errors.append("content-manifest.pages must be a non-empty list")
        return errors
    manifest_ids: set[str] = set()
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            errors.append(f"content pages[{index}] must be an object")
            continue
        page_id = page.get("page_id")
        if page_id not in matrix_pages:
            errors.append(f"content page {page_id!r} is not in page-matrix")
            continue
        if page_id in manifest_ids:
            errors.append(f"duplicate content page_id: {page_id}")
        manifest_ids.add(page_id)
        matrix_page = matrix_pages[page_id]
        if page.get("locale") != matrix_page.get("locale"):
            errors.append(f"content page {page_id}.locale does not match page-matrix")
        for field in ("title", "primary_keyword"):
            if not is_nonempty_string(page.get(field)):
                errors.append(f"content page {page_id}.{field} is required")
        if normalize_keyword(str(page.get("primary_keyword", ""))) != normalize_keyword(
            str(matrix_page.get("primary_keyword", ""))
        ):
            errors.append(f"content page {page_id}.primary_keyword does not match page-matrix")
        if page.get("status") not in {"planned", "draft", "reviewed", "published"}:
            errors.append(f"content page {page_id}.status is invalid")
        referenced_sources = ensure_string_list(
            page.get("source_ids"), f"content page {page_id}.source_ids", errors
        )
        for source_id in referenced_sources:
            if source_id not in source_ids:
                errors.append(f"content page {page_id} references unknown source {source_id}")
        referenced_claims = ensure_string_list(
            page.get("claim_ids", []), f"content page {page_id}.claim_ids", errors, allow_empty=True
        )
        for claim_id in referenced_claims:
            if claim_id not in claim_ids:
                errors.append(f"content page {page_id} references unknown claim {claim_id}")
            elif claim_map[claim_id].get("status") == "rejected":
                errors.append(f"content page {page_id} references rejected claim {claim_id}")
        if set(referenced_claims) != claims_by_page.get(page_id, set()):
            errors.append(
                f"content page {page_id}.claim_ids must exactly match the evidence claims assigned to that page"
            )
        content_path = safe_content_path(project_dir, page.get("path"), f"content page {page_id}.path", errors)
        if require_files and content_path is not None:
            if not content_path.is_file():
                errors.append(f"content page {page_id} file is missing: {content_path}")
            else:
                expected_hash = page.get("content_sha256")
                if not is_nonempty_string(expected_hash):
                    errors.append(f"content page {page_id}.content_sha256 is required after build")
                elif sha256_file(content_path) != expected_hash:
                    errors.append(f"content page {page_id} content_sha256 does not match file")
                if page.get("status") not in {"reviewed", "published"}:
                    errors.append(f"content page {page_id} must be reviewed before local verification")
                if page.get("human_reviewed") is True:
                    if not is_nonempty_string(page.get("reviewed_by")):
                        errors.append(f"content page {page_id}.reviewed_by is required")
                    parse_timestamp(page.get("reviewed_at"), f"content page {page_id}.reviewed_at", errors)
    if manifest_ids != set(matrix_pages):
        missing = sorted(set(matrix_pages) - manifest_ids)
        extra = sorted(manifest_ids - set(matrix_pages))
        if missing:
            errors.append(f"content-manifest is missing page ids: {', '.join(missing)}")
        if extra:
            errors.append(f"content-manifest has extra page ids: {', '.join(extra)}")
    return errors


def validate_launch_report(
    launch: dict[str, Any],
    candidate: dict[str, Any],
    content: dict[str, Any],
    project_dir: Path,
    require_local: bool,
    require_deploy_plan: bool,
    require_deployed: bool,
    state: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    validate_schema_version(launch, "launch-report", errors)
    if launch.get("candidate_key") != candidate.get("key"):
        errors.append("launch-report.candidate_key does not match candidate-lock.key")
    site_identity = launch.get("site_identity")
    if not isinstance(site_identity, dict):
        errors.append("launch-report.site_identity must be an object")
        site_identity = {}
    canonical_origin = site_identity.get("canonical_origin")
    if not is_nonempty_string(canonical_origin):
        errors.append("launch-report.site_identity.canonical_origin is required")
    forbidden_origins = ensure_string_list(
        site_identity.get("forbidden_origins", []),
        "launch-report.site_identity.forbidden_origins",
        errors,
        allow_empty=True,
    )

    rollback = launch.get("rollback")
    if not isinstance(rollback, dict) or rollback.get("documented") is not True:
        errors.append("launch-report.rollback.documented must be true")
    elif not is_nonempty_string(rollback.get("procedure")):
        errors.append("launch-report.rollback.procedure is required")

    local_checks = launch.get("local_checks")
    check_map: dict[str, dict[str, Any]] = {}
    if not isinstance(local_checks, list):
        errors.append("launch-report.local_checks must be a list")
    else:
        for index, check in enumerate(local_checks):
            if not isinstance(check, dict) or not is_nonempty_string(check.get("name")):
                errors.append(f"local_checks[{index}] requires a name")
                continue
            name = check["name"]
            if name in check_map:
                errors.append(f"duplicate local check: {name}")
            check_map[name] = check
            if check.get("status") not in {"passed", "not_applicable", "failed", "not_run"}:
                errors.append(f"local check {name}.status is invalid")
            if check.get("status") in {"passed", "not_applicable"} and not is_nonempty_string(
                check.get("evidence")
            ):
                errors.append(f"local check {name}.evidence is required")
    if require_local:
        for name in sorted(REQUIRED_LOCAL_CHECKS):
            if name not in check_map:
                errors.append(f"required local check is missing: {name}")
            elif check_map[name].get("status") not in {"passed", "not_applicable"}:
                errors.append(f"required local check has not passed: {name}")

        pages = content.get("pages") if isinstance(content.get("pages"), list) else []
        change_batch = [
            page
            for page in pages
            if isinstance(page, dict) and page.get("status") == "reviewed"
        ]
        if not change_batch:
            errors.append(
                "human review gate requires at least one reviewed page in the current change batch"
            )
        else:
            missing_human_review = [
                str(page.get("page_id"))
                for page in change_batch
                if page.get("human_reviewed") is not True
            ]
            if missing_human_review:
                errors.append(
                    "human review gate requires every page in the current change batch; "
                    f"missing: {', '.join(sorted(missing_human_review))}"
                )
        for page in pages:
            if not isinstance(page, dict):
                continue
            path = safe_content_path(
                project_dir,
                page.get("path"),
                f"content page {page.get('page_id')}.path",
                errors,
            )
            if path is None or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for forbidden in forbidden_origins:
                if forbidden.casefold() in text.casefold():
                    errors.append(f"old-domain residue in {path}: {forbidden}")

    external_actions = launch.get("external_actions")
    action_rows: list[dict[str, Any]] = []
    if not isinstance(external_actions, list):
        errors.append("launch-report.external_actions must be a list")
    else:
        for index, row in enumerate(external_actions):
            if not isinstance(row, dict) or row.get("action") not in EXTERNAL_ACTIONS:
                errors.append(f"external_actions[{index}].action is invalid")
                continue
            if row.get("status") not in {"planned", "not_needed", "verified", "failed"}:
                errors.append(f"external action {row.get('action')}.status is invalid")
            action_rows.append(row)

    if require_deploy_plan:
        deployment_plans = [row for row in action_rows if row.get("action") == "deployment"]
        if len(deployment_plans) != 1 or deployment_plans[0].get("status") not in {
            "planned",
            "verified",
        }:
            errors.append("deploy-ready stage requires exactly one planned or verified deployment action")

    if require_deployed:
        deployment = launch.get("deployment")
        if not isinstance(deployment, dict) or deployment.get("status") != "verified":
            errors.append("launch-report.deployment.status must be verified")
        else:
            for field in ("url", "provider", "source_revision", "authorization_id"):
                if not is_nonempty_string(deployment.get(field)):
                    errors.append(f"launch-report.deployment.{field} is required")
            parse_timestamp(deployment.get("deployed_at"), "launch-report.deployment.deployed_at", errors)
        readback = launch.get("http_readback")
        if not isinstance(readback, dict) or readback.get("status") != "passed":
            errors.append("launch-report.http_readback.status must be passed")
        else:
            if not is_nonempty_string(readback.get("url")):
                errors.append("launch-report.http_readback.url is required")
            parse_timestamp(readback.get("checked_at"), "launch-report.http_readback.checked_at", errors)
        deployments = [row for row in action_rows if row.get("action") == "deployment"]
        if len(deployments) != 1 or deployments[0].get("status") != "verified":
            errors.append("exactly one verified deployment external_action is required")
        elif isinstance(deployment, dict) and deployments[0].get("authorization_id") != deployment.get(
            "authorization_id"
        ):
            errors.append("deployment and external_action must reference the same authorization_id")
        for row in action_rows:
            if row.get("status") == "verified":
                errors.extend(validate_authorization(row, state))
    return errors


def validate_authorization(action_row: dict[str, Any], state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    action = action_row.get("action")
    auth_id = action_row.get("authorization_id")
    if not is_nonempty_string(auth_id):
        return [f"verified external action {action} requires authorization_id"]
    matches = [
        auth
        for auth in state.get("authorizations", [])
        if isinstance(auth, dict) and auth.get("authorization_id") == auth_id
    ]
    if len(matches) != 1:
        return [f"external action {action} references unknown authorization {auth_id}"]
    auth = matches[0]
    if auth.get("action") != action:
        errors.append(f"authorization {auth_id} grants {auth.get('action')}, not {action}")
    if auth.get("status") != "granted":
        errors.append(f"authorization {auth_id} is not active")
    expires_at = auth.get("expires_at")
    if expires_at:
        parsed: list[str] = []
        expiry = parse_timestamp(expires_at, f"authorization {auth_id}.expires_at", parsed)
        errors.extend(parsed)
        if expiry and expiry <= datetime.now(timezone.utc):
            errors.append(f"authorization {auth_id} has expired")
    return errors


def validate_analytics(
    analytics: dict[str, Any],
    candidate: dict[str, Any],
    state: dict[str, Any],
    require_observation: bool,
    decision_target: str | None,
    require_template: bool,
) -> list[str]:
    errors: list[str] = []
    validate_schema_version(analytics, "analytics-snapshot", errors)
    if analytics.get("candidate_key") != candidate.get("key"):
        errors.append("analytics-snapshot.candidate_key does not match candidate-lock.key")
    parse_timestamp(analytics.get("snapshot_at"), "analytics-snapshot.snapshot_at", errors)
    if not is_nonempty_string(analytics.get("site_url")):
        errors.append("analytics-snapshot.site_url is required")

    for provider_name, action in (("gsc", "gsc_setup"), ("ga", "ga_setup")):
        provider = analytics.get(provider_name)
        if not isinstance(provider, dict) or provider.get("setup_status") != "verified":
            errors.append(f"analytics-snapshot.{provider_name}.setup_status must be verified")
            continue
        setup_mode = provider.get("setup_mode")
        if setup_mode not in {"existing", "created"}:
            errors.append(f"analytics-snapshot.{provider_name}.setup_mode must be existing or created")
        if not is_nonempty_string(provider.get("property")):
            errors.append(f"analytics-snapshot.{provider_name}.property is required")
        parse_timestamp(provider.get("readback_at"), f"analytics-snapshot.{provider_name}.readback_at", errors)
        if provider.get("data_status") not in {"valid", "no_valid_data", "error"}:
            errors.append(f"analytics-snapshot.{provider_name}.data_status is invalid")
        if setup_mode == "created":
            errors.extend(
                validate_authorization(
                    {"action": action, "authorization_id": provider.get("authorization_id")}, state
                )
            )

    gsc = analytics.get("gsc") if isinstance(analytics.get("gsc"), dict) else {}
    data_status = gsc.get("data_status")
    if data_status not in {"valid", "no_valid_data", "error"}:
        errors.append("analytics-snapshot.gsc.data_status is invalid")
    if data_status == "valid":
        metrics = gsc.get("metrics")
        if not isinstance(metrics, dict):
            errors.append("valid GSC data requires metrics")
        else:
            for field in ("clicks", "impressions", "indexed_pages"):
                value = metrics.get(field)
                if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                    errors.append(f"analytics-snapshot.gsc.metrics.{field} must be non-negative")

    observation = analytics.get("observation")
    if require_observation:
        if not isinstance(observation, dict):
            errors.append("analytics-snapshot.observation must be an object")
        else:
            day = observation.get("day")
            if not isinstance(day, int) or isinstance(day, bool) or day < 0:
                errors.append("analytics-snapshot.observation.day must be a non-negative integer")
            review_dates = observation.get("next_review_dates")
            if data_status != "valid":
                dates = ensure_string_list(
                    review_dates,
                    "analytics-snapshot.observation.next_review_dates",
                    errors,
                )
                if len(dates) < 2:
                    errors.append("missing GSC data requires both day-7 and day-14 review dates")
                for index, date in enumerate(dates):
                    parse_timestamp(date, f"observation.next_review_dates[{index}]", errors)
                checks = observation.get("technical_checks")
                if not isinstance(checks, list) or not checks:
                    errors.append("missing GSC data requires recorded technical_checks")

    if decision_target:
        decision = analytics.get("decision")
        if not isinstance(decision, dict) or decision.get("recommendation") != decision_target:
            errors.append(f"analytics decision.recommendation must equal {decision_target}")
        else:
            if not is_nonempty_string(decision.get("rationale")):
                errors.append("analytics decision.rationale is required")
            if not is_nonempty_string(decision.get("approved_by")):
                errors.append("analytics decision.approved_by is required")
            parse_timestamp(decision.get("approved_at"), "analytics decision.approved_at", errors)
        if decision_target in {"grow", "retire"} and data_status != "valid":
            errors.append(f"cannot enter {decision_target} without valid GSC data")

    if require_template:
        readiness = analytics.get("template_readiness")
        if not isinstance(readiness, dict) or readiness.get("approved") is not True:
            errors.append("analytics-snapshot.template_readiness.approved must be true")
        else:
            if not is_nonempty_string(readiness.get("reusable_scope")):
                errors.append("template_readiness.reusable_scope is required")
            if not is_nonempty_string(readiness.get("product_specific_exclusions")):
                errors.append("template_readiness.product_specific_exclusions is required")
            if not is_nonempty_string(readiness.get("approved_by")):
                errors.append("template_readiness.approved_by is required")
            parse_timestamp(readiness.get("approved_at"), "template_readiness.approved_at", errors)
    return errors


def scan_for_secrets(paths: Iterable[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"possible secret ({label}) in {path}")
    return errors


def load_required(project_dir: Path, key: str, errors: list[str]) -> dict[str, Any] | None:
    path = artifact_path(project_dir, key)
    try:
        return read_json(path)
    except PipelineError as exc:
        errors.append(str(exc))
        return None


def validate_project(project_dir: Path, target_stage: str | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    candidate = load_required(project_dir, "candidate", errors)
    state = load_required(project_dir, "state", errors)
    if candidate is None or state is None:
        return {"ok": False, "stage": None, "errors": errors, "warnings": warnings}
    errors.extend(validate_candidate(candidate, locked=True))
    errors.extend(validate_state(state, candidate))
    if candidate.get("source_report_sha256") is None:
        warnings.append("missing evidence: source_report could not be hashed at candidate lock time")
    current_stage = state.get("current_stage")
    stage = target_stage or current_stage
    if stage not in STAGE_LEVEL:
        errors.append(f"unknown target stage: {stage}")
        return {"ok": False, "stage": stage, "errors": errors, "warnings": warnings}
    level = STAGE_LEVEL[stage]

    matrix: dict[str, Any] | None = None
    evidence: dict[str, Any] | None = None
    content: dict[str, Any] | None = None
    launch: dict[str, Any] | None = None
    analytics: dict[str, Any] | None = None

    if level >= STAGE_LEVEL["planned"]:
        matrix = load_required(project_dir, "matrix", errors)
        if matrix:
            errors.extend(validate_page_matrix(matrix, candidate))
    if level >= STAGE_LEVEL["researched"]:
        evidence = load_required(project_dir, "evidence", errors)
        if evidence and matrix:
            errors.extend(validate_evidence_pack(evidence, candidate, matrix))
    if level >= STAGE_LEVEL["build_ready"]:
        content = load_required(project_dir, "content", errors)
        if content and matrix and evidence:
            errors.extend(
                validate_content_manifest(
                    content, candidate, matrix, evidence, project_dir, require_files=level >= 4
                )
            )
    if level >= STAGE_LEVEL["local_verified"]:
        launch = load_required(project_dir, "launch", errors)
        if launch and content:
            errors.extend(
                validate_launch_report(
                    launch,
                    candidate,
                    content,
                    project_dir,
                    require_local=True,
                    require_deploy_plan=level >= STAGE_LEVEL["deploy_ready"],
                    require_deployed=level >= STAGE_LEVEL["deployed"],
                    state=state,
                )
            )
    if level >= STAGE_LEVEL["telemetry_verified"]:
        analytics = load_required(project_dir, "analytics", errors)
        if analytics:
            decision_target = (
                stage
                if stage in {"grow", "hold", "retire"}
                else "grow"
                if stage == "templated"
                else None
            )
            errors.extend(
                validate_analytics(
                    analytics,
                    candidate,
                    state,
                    require_observation=level >= STAGE_LEVEL["observing"],
                    decision_target=decision_target,
                    require_template=stage == "templated",
                )
            )

    decision_log = artifact_path(project_dir, "decision_log")
    if not decision_log.is_file() or not decision_log.read_text(encoding="utf-8").strip():
        errors.append("decision-log.md is missing or empty")

    scan_paths = [
        artifact_path(project_dir, key)
        for key in ("candidate", "state", "matrix", "evidence", "content", "launch", "analytics", "decision_log")
    ]
    if content:
        for page in content.get("pages", []):
            if isinstance(page, dict):
                path_errors: list[str] = []
                content_path = safe_content_path(project_dir, page.get("path"), "content path", path_errors)
                if content_path:
                    scan_paths.append(content_path)
    errors.extend(scan_for_secrets(scan_paths))
    if level >= STAGE_LEVEL["telemetry_verified"] and analytics:
        gsc = analytics.get("gsc") if isinstance(analytics.get("gsc"), dict) else {}
        if gsc.get("data_status") != "valid":
            warnings.append("missing evidence: no valid GSC performance data; only diagnostics and day-7/day-14 review are allowed")
    return {
        "ok": not errors,
        "stage": stage,
        "current_stage": current_stage,
        "errors": errors,
        "warnings": warnings,
    }


def gate_project(project_dir: Path, target: str) -> dict[str, Any]:
    state_path = artifact_path(project_dir, "state")
    try:
        state = read_json(state_path)
    except PipelineError as exc:
        return {"ok": False, "target": target, "errors": [str(exc)], "warnings": []}
    current = state.get("current_stage")
    errors: list[str] = []
    if target not in STAGE_TRANSITIONS:
        errors.append(f"unknown target stage: {target}")
    elif target not in STAGE_TRANSITIONS.get(current, ()):
        allowed = ", ".join(STAGE_TRANSITIONS.get(current, ())) or "none"
        errors.append(f"transition {current} -> {target} is not allowed; valid next stages: {allowed}")
    validation = validate_project(project_dir, target_stage=target)
    errors.extend(validation["errors"])
    return {
        "ok": not errors,
        "current_stage": current,
        "target": target,
        "errors": errors,
        "warnings": validation["warnings"],
    }


def append_decision_log(project_dir: Path, title: str, fields: dict[str, str]) -> None:
    path = artifact_path(project_dir, "decision_log")
    lines = [f"\n## {title}\n"]
    for key, value in fields.items():
        lines.append(f"- {key}: {value}\n")
    with path.open("a", encoding="utf-8") as handle:
        handle.writelines(lines)


def cmd_init(args: argparse.Namespace) -> int:
    project_dir = args.project_dir.resolve()
    candidate_source = args.candidate_file.resolve()
    candidate_input = read_json(candidate_source)
    errors = validate_candidate(candidate_input, locked=False)
    if args.confirm_key != candidate_input.get("key"):
        errors.append("--confirm-key must exactly match the candidate key")
    if not is_nonempty_string(args.approved_by):
        errors.append("--approved-by is required")
    if not is_nonempty_string(args.rationale):
        errors.append("--rationale is required")
    for key in ("candidate", "state", "decision_log"):
        if artifact_path(project_dir, key).exists():
            errors.append(f"refusing to overwrite existing artifact: {artifact_path(project_dir, key)}")
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 2

    locked_at = utc_now()
    source_report = candidate_input["source_report"]
    source_report_path = Path(source_report)
    if not source_report_path.is_absolute():
        source_report_path = candidate_source.parent / source_report_path
    candidate_lock = {
        "schema_version": SCHEMA_VERSION,
        "key": candidate_input["key"],
        "name": candidate_input["name"],
        "source_report": source_report,
        "source_report_sha256": sha256_file(source_report_path) if source_report_path.is_file() else None,
        "locked_at": locked_at,
        "qualification": candidate_input["qualification"],
        "identities": candidate_input["identities"],
        "business_hypothesis": candidate_input["business_hypothesis"],
        "decision": {
            "status": "approved",
            "approved_by": args.approved_by,
            "confirmed_key": args.confirm_key,
            "rationale": args.rationale,
        },
    }
    identity = canonical_json_sha256(
        {"key": candidate_lock["key"], "identities": candidate_lock["identities"]}
    )
    slug = re.sub(r"[^a-z0-9]+", "-", candidate_lock["key"].casefold()).strip("-")
    project_id = f"{slug}-{identity[:8]}"
    state = {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "candidate_key": candidate_lock["key"],
        "candidate_identity": identity,
        "candidate_lock_sha256": canonical_json_sha256(candidate_lock),
        "current_stage": "candidate_locked",
        "updated_at": locked_at,
        "authorizations": [],
        "history": [
            {
                "event": "transition",
                "from": None,
                "to": "candidate_locked",
                "at": locked_at,
                "actor": args.approved_by,
                "reason": args.rationale,
            }
        ],
    }
    project_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(artifact_path(project_dir, "candidate"), candidate_lock)
    atomic_write_json(artifact_path(project_dir, "state"), state)
    artifact_path(project_dir, "decision_log").write_text(
        "# Decision Log\n\n"
        "This log records human approvals, stage transitions, evidence gaps, and reversals.\n",
        encoding="utf-8",
    )
    append_decision_log(
        project_dir,
        "Candidate locked",
        {
            "at": locked_at,
            "actor": args.approved_by,
            "candidate": candidate_lock["key"],
            "candidate identity": identity,
            "rationale": args.rationale,
        },
    )
    print(
        json.dumps(
            {
                "ok": True,
                "project_dir": str(project_dir),
                "project_id": project_id,
                "stage": "candidate_locked",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    project_dir = args.project_dir.resolve()
    try:
        state = read_json(artifact_path(project_dir, "state"))
    except PipelineError as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2
    current = state.get("current_stage")
    current_validation = validate_project(project_dir)
    next_stages = []
    for target in STAGE_TRANSITIONS.get(current, ()):
        result = gate_project(project_dir, target)
        next_stages.append(
            {
                "stage": target,
                "ready": result["ok"],
                "blockers": result["errors"],
                "warnings": result["warnings"],
            }
        )
    payload = {
        "ok": current_validation["ok"],
        "project_id": state.get("project_id"),
        "current_stage": current,
        "current_errors": current_validation["errors"],
        "current_warnings": current_validation["warnings"],
        "next_stages": next_stages,
        "active_authorizations": [
            {
                "authorization_id": auth.get("authorization_id"),
                "action": auth.get("action"),
                "scope": auth.get("scope"),
                "expires_at": auth.get("expires_at"),
            }
            for auth in state.get("authorizations", [])
            if isinstance(auth, dict) and auth.get("status") == "granted"
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 2


def cmd_validate(args: argparse.Namespace) -> int:
    result = validate_project(args.project_dir.resolve(), target_stage=args.stage)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def cmd_gate(args: argparse.Namespace) -> int:
    result = gate_project(args.project_dir.resolve(), args.target)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def cmd_transition(args: argparse.Namespace) -> int:
    project_dir = args.project_dir.resolve()
    if not is_nonempty_string(args.actor) or not is_nonempty_string(args.reason):
        print(
            json.dumps(
                {"ok": False, "errors": ["--actor and --reason must be non-empty"]},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    result = gate_project(project_dir, args.to)
    if not result["ok"]:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    state_path = artifact_path(project_dir, "state")
    state = read_json(state_path)
    previous = state["current_stage"]
    at = utc_now()
    state["current_stage"] = args.to
    state["updated_at"] = at
    state["history"].append(
        {
            "event": "transition",
            "from": previous,
            "to": args.to,
            "at": at,
            "actor": args.actor,
            "reason": args.reason,
        }
    )
    atomic_write_json(state_path, state)
    append_decision_log(
        project_dir,
        f"Transition: {previous} -> {args.to}",
        {"at": at, "actor": args.actor, "reason": args.reason},
    )
    print(
        json.dumps(
            {"ok": True, "from": previous, "to": args.to, "at": at},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_authorize(args: argparse.Namespace) -> int:
    if args.confirm != args.action:
        print(
            json.dumps(
                {"ok": False, "errors": ["--confirm must exactly match --action"]},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    if any(
        not is_nonempty_string(value)
        for value in (args.granted_by, args.scope, args.user_instruction)
    ):
        print(
            json.dumps(
                {
                    "ok": False,
                    "errors": ["--granted-by, --scope and --user-instruction must be non-empty"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    state_path = artifact_path(args.project_dir.resolve(), "state")
    state = read_json(state_path)
    now = utc_now()
    errors: list[str] = []
    if args.expires_at:
        parsed = parse_timestamp(args.expires_at, "--expires-at", errors)
        if parsed and parsed <= datetime.now(timezone.utc):
            errors.append("--expires-at must be in the future")
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 2
    seed = (
        f"{args.action}|{now}|{args.granted_by}|{args.scope}|{args.user_instruction}|"
        f"{len(state.get('authorizations', []))}"
    )
    auth_id = f"auth-{sha256_bytes(seed.encode('utf-8'))[:12]}"
    authorization = {
        "authorization_id": auth_id,
        "action": args.action,
        "status": "granted",
        "granted_by": args.granted_by,
        "granted_at": now,
        "expires_at": args.expires_at,
        "scope": args.scope,
        "user_instruction": args.user_instruction,
    }
    state["authorizations"].append(authorization)
    state["updated_at"] = now
    state["history"].append(
        {
            "event": "authorization_granted",
            "authorization_id": auth_id,
            "action": args.action,
            "at": now,
            "actor": args.granted_by,
            "reason": args.scope,
        }
    )
    atomic_write_json(state_path, state)
    append_decision_log(
        args.project_dir.resolve(),
        f"Authorization granted: {args.action}",
        {
            "at": now,
            "authorization id": auth_id,
            "actor": args.granted_by,
            "scope": args.scope,
            "user instruction": args.user_instruction,
        },
    )
    print(json.dumps({"ok": True, **authorization}, ensure_ascii=False, indent=2))
    return 0


def cmd_revoke(args: argparse.Namespace) -> int:
    project_dir = args.project_dir.resolve()
    state_path = artifact_path(project_dir, "state")
    state = read_json(state_path)
    matches = [
        auth
        for auth in state.get("authorizations", [])
        if isinstance(auth, dict) and auth.get("authorization_id") == args.authorization_id
    ]
    if len(matches) != 1 or matches[0].get("status") != "granted":
        print(
            json.dumps(
                {"ok": False, "errors": ["active authorization not found"]},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    now = utc_now()
    matches[0]["status"] = "revoked"
    matches[0]["revoked_at"] = now
    matches[0]["revoked_by"] = args.actor
    matches[0]["revoke_reason"] = args.reason
    state["updated_at"] = now
    state["history"].append(
        {
            "event": "authorization_revoked",
            "authorization_id": args.authorization_id,
            "action": matches[0]["action"],
            "at": now,
            "actor": args.actor,
            "reason": args.reason,
        }
    )
    atomic_write_json(state_path, state)
    append_decision_log(
        project_dir,
        f"Authorization revoked: {matches[0]['action']}",
        {
            "at": now,
            "authorization id": args.authorization_id,
            "actor": args.actor,
            "reason": args.reason,
        },
    )
    print(
        json.dumps(
            {"ok": True, "authorization_id": args.authorization_id, "status": "revoked"},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Govern a web-business project through evidence gates")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="lock one human-approved qualified candidate")
    init.add_argument("--project-dir", type=Path, required=True)
    init.add_argument("--candidate-file", type=Path, required=True)
    init.add_argument("--approved-by", required=True)
    init.add_argument("--confirm-key", required=True)
    init.add_argument("--rationale", required=True)
    init.set_defaults(handler=cmd_init)

    status = subparsers.add_parser("status", help="show the current stage and next blockers")
    status.add_argument("--project-dir", type=Path, required=True)
    status.set_defaults(handler=cmd_status)

    validate = subparsers.add_parser("validate", help="validate the current or named stage")
    validate.add_argument("--project-dir", type=Path, required=True)
    validate.add_argument("--stage", choices=tuple(STAGE_TRANSITIONS))
    validate.set_defaults(handler=cmd_validate)

    gate = subparsers.add_parser("gate", help="check one allowed next transition without writing")
    gate.add_argument("--project-dir", type=Path, required=True)
    gate.add_argument("--target", choices=tuple(STAGE_TRANSITIONS), required=True)
    gate.set_defaults(handler=cmd_gate)

    transition = subparsers.add_parser("transition", help="record a passing stage transition")
    transition.add_argument("--project-dir", type=Path, required=True)
    transition.add_argument("--to", choices=tuple(STAGE_TRANSITIONS), required=True)
    transition.add_argument("--actor", required=True)
    transition.add_argument("--reason", required=True)
    transition.set_defaults(handler=cmd_transition)

    authorize = subparsers.add_parser("authorize", help="record explicit permission; execute nothing")
    authorize.add_argument("--project-dir", type=Path, required=True)
    authorize.add_argument("--action", choices=EXTERNAL_ACTIONS, required=True)
    authorize.add_argument("--confirm", required=True)
    authorize.add_argument("--granted-by", required=True)
    authorize.add_argument("--scope", required=True)
    authorize.add_argument("--user-instruction", required=True)
    authorize.add_argument("--expires-at")
    authorize.set_defaults(handler=cmd_authorize)

    revoke = subparsers.add_parser("revoke", help="revoke a recorded authorization")
    revoke.add_argument("--project-dir", type=Path, required=True)
    revoke.add_argument("--authorization-id", required=True)
    revoke.add_argument("--actor", required=True)
    revoke.add_argument("--reason", required=True)
    revoke.set_defaults(handler=cmd_revoke)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except PipelineError as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2
    except OSError as exc:
        print(json.dumps({"ok": False, "errors": [f"filesystem error: {exc}"]}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
