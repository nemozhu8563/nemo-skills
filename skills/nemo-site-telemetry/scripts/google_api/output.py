"""Stable JSON envelopes and credential-safe error serialization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
from typing import Any, Callable, TextIO

from . import ADAPTER_VERSION, SCHEMA_VERSION


SUCCESS_STATUSES = frozenset({"completed", "verified", "noop"})
FAILURE_STATUSES = frozenset({"required", "blocked", "pending", "failed"})
_PROVIDER_STATUS = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")

_REDACTIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{8,}"), "Bearer [REDACTED]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"), "[REDACTED_JWT]"),
    (re.compile(r"-----BEGIN [^-]+-----[\s\S]*?-----END [^-]+-----"), "[REDACTED_PEM]"),
    (re.compile(r"\b(?:ya29\.|1//|4/)[A-Za-z0-9._~+/=-]{8,}\b"), "[REDACTED_OAUTH]"),
    (re.compile(r"(?i)google-site-verification(?:=|%3D)[A-Za-z0-9._~-]+"), "google-site-verification=[REDACTED]"),
    (re.compile(r"(?i)\b(token|secret|password|cookie|authorization|credential|verification(?:_value)?)\b\s*[:=]\s*[^\s,;]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?:/[^\s:'\"]+){2,}/[^\s:'\"]+\.(?:json|pem|p12)\b"), "[REDACTED_CREDENTIAL_PATH]"),
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def rfc3339(value: datetime | None = None) -> str:
    current = value or utc_now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def redact_text(value: object, *, limit: int = 512) -> str:
    text = str(value).replace("\x00", "")
    for pattern, replacement in _REDACTIONS:
        text = pattern.sub(replacement, text)
    text = " ".join(text.split())
    return text[:limit]


def normalize_provider_status(value: object) -> str | int | None:
    """Keep only bounded Google status enums or numeric provider codes."""
    if value is None:
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and _PROVIDER_STATUS.fullmatch(value):
        return value
    return "UNKNOWN"


@dataclass(slots=True)
class AdapterError(Exception):
    error_code: str
    status: str
    exit_code: int
    next_step: str
    provider_status: str | int | None = None
    reason: str | None = None
    retryable: bool = False

    def __post_init__(self) -> None:
        self.next_step = redact_text(self.next_step)
        self.provider_status = normalize_provider_status(self.provider_status)
        self.reason = redact_text(self.reason, limit=256) if self.reason is not None else None
        Exception.__init__(self, self.error_code)

    def as_dict(self) -> dict[str, object]:
        return {
            "error_code": self.error_code,
            "provider_status": self.provider_status,
            "reason": self.reason,
            "retryable": self.retryable,
            "next_step": self.next_step,
        }


def default_google_api(
    checked_at: str,
    *,
    provider_mode: str = "google_api",
    auth_mode: str = "unknown",
) -> dict[str, object]:
    return {
        "provider_mode": provider_mode,
        "adapter_version": ADAPTER_VERSION,
        "auth_mode": auth_mode,
        "api_project": "unknown",
        "quota_project_status": "unknown",
        "account_subject": "unknown",
        "capability_status": "unknown",
        "scope_status": "unknown",
        "resource_access": "unknown",
        "bootstrap_status": "not_needed",
        "steady_state": "not_applicable",
        "api_readback": "not_attempted",
        "checked_at": checked_at,
    }


def make_evidence(
    method: str,
    status: str,
    summary: str,
    *,
    checked_at: str,
    surface: str = "api",
) -> dict[str, str]:
    return {
        "surface": surface,
        "provider_method": method,
        "observed_at": checked_at,
        "status": status,
        "summary": redact_text(summary),
    }


def make_envelope(
    command: str,
    status: str,
    *,
    clock: Callable[[], datetime] = utc_now,
    google_api: dict[str, object] | None = None,
    target: dict[str, object] | None = None,
    evidence: list[dict[str, object]] | None = None,
    result: dict[str, object] | None = None,
    plan: dict[str, object] | None = None,
    error: AdapterError | dict[str, object] | None = None,
) -> dict[str, object]:
    checked_at = rfc3339(clock())
    if status not in SUCCESS_STATUSES | FAILURE_STATUSES:
        raise ValueError("invalid envelope status")
    if status in SUCCESS_STATUSES and error is not None:
        raise ValueError("successful envelope cannot contain an error")
    if status in FAILURE_STATUSES and error is None:
        raise ValueError("failed envelope requires an error")
    safe_error = error.as_dict() if isinstance(error, AdapterError) else error
    return {
        "schema_version": SCHEMA_VERSION,
        "adapter_version": ADAPTER_VERSION,
        "command": command,
        "status": status,
        "checked_at": checked_at,
        "google_api": google_api or default_google_api(checked_at),
        "target": target,
        "evidence": evidence or [],
        "result": result,
        "plan": plan,
        "error": safe_error,
    }


def safe_json(envelope: dict[str, object]) -> str:
    try:
        return json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    except Exception:
        fallback = make_envelope(
            "adapter.serialization",
            "failed",
            error=AdapterError(
                "safe_serialization_failed",
                "failed",
                15,
                "Inspect the local adapter implementation; no provider payload was retained.",
            ),
        )
        return json.dumps(fallback, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def emit(envelope: dict[str, object], stream: TextIO) -> None:
    stream.write(safe_json(envelope))
