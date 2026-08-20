"""Canonical identities and single-use, credential-free write plans."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import tempfile
from typing import Any, Callable
from urllib.parse import SplitResult, urlsplit, urlunsplit

from .output import AdapterError, rfc3339, utc_now


PLAN_TTL = timedelta(minutes=10)
RECOVERY_WINDOW = timedelta(minutes=15)
MAX_PLAN_BYTES = 128 * 1024
PLAN_DIRECTORY_PREFIX = "nemo-site-telemetry-"
RECOVERY_DIRECTORY_PREFIX = "nemo-site-telemetry-recovery-"
_FINGERPRINT = re.compile(r"^[a-f0-9]{64}$")


def canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fingerprint(value: object) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _invalid_input(next_step: str) -> AdapterError:
    return AdapterError("invalid_input", "blocked", 12, next_step)


def _split_url(value: str, next_step: str) -> SplitResult:
    try:
        return urlsplit(value)
    except ValueError as exc:
        raise _invalid_input(next_step) from exc


def _ascii_hostname(hostname: str | None) -> str:
    if not hostname:
        raise _invalid_input("Provide an absolute URL with a non-empty hostname.")
    try:
        return hostname.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise _invalid_input("Use a valid DNS hostname.") from exc


def _normalized_netloc(parsed: SplitResult) -> str:
    if parsed.username is not None or parsed.password is not None:
        raise _invalid_input("Remove user information from the URL.")
    host = _ascii_hostname(parsed.hostname)
    try:
        port = parsed.port
    except ValueError as exc:
        raise _invalid_input("Use a valid numeric URL port.") from exc
    if ":" in host:
        host = f"[{host}]"
    if port is not None and not ((parsed.scheme.lower() == "https" and port == 443) or (parsed.scheme.lower() == "http" and port == 80)):
        return f"{host}:{port}"
    return host


def canonical_origin(value: str) -> str:
    if any(ord(char) < 32 for char in value):
        raise _invalid_input("Remove control characters from the production origin.")
    parsed = _split_url(value, "Use a valid absolute production origin.")
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise _invalid_input("Use an absolute http or https production origin.")
    if parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
        raise _invalid_input("Provide only the production origin, without path, query, or fragment.")
    return urlunsplit((scheme, _normalized_netloc(parsed), "", "", ""))


def canonical_site_url(value: str) -> str:
    if value.lower().startswith("sc-domain:"):
        domain = value[len("sc-domain:") :]
        if not domain or any(char in domain for char in "/?#@:"):
            raise _invalid_input("Use sc-domain: followed by one exact domain.")
        return f"sc-domain:{_ascii_hostname(domain)}"
    parsed = _split_url(value, "Use a valid Search Console URL-prefix property identifier.")
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.hostname:
        raise _invalid_input("Use an exact Search Console domain or URL-prefix property identifier.")
    if parsed.query or parsed.fragment:
        raise _invalid_input("A URL-prefix property cannot contain a query or fragment.")
    path = parsed.path or "/"
    return urlunsplit((scheme, _normalized_netloc(parsed), path, "", ""))


def canonical_target_url(value: str, *, allow_query: bool = True) -> str:
    if any(ord(char) < 32 for char in value):
        raise _invalid_input("Remove control characters from the target URL.")
    parsed = _split_url(value, "Use a valid absolute target URL.")
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.hostname:
        raise _invalid_input("Use an absolute http or https target URL.")
    if parsed.fragment:
        raise _invalid_input("Remove the URL fragment from the target URL.")
    if parsed.query and not allow_query:
        raise _invalid_input("Remove the query from the target URL.")
    return urlunsplit((scheme, _normalized_netloc(parsed), parsed.path or "/", parsed.query, ""))


def _effective_port(parsed: SplitResult) -> int:
    if parsed.port is not None:
        return parsed.port
    return 443 if parsed.scheme.lower() == "https" else 80


def property_contains(site_url: str, target_url: str) -> bool:
    site = canonical_site_url(site_url)
    target = _split_url(canonical_target_url(target_url), "Use a valid absolute target URL.")
    if site.startswith("sc-domain:"):
        domain = site[len("sc-domain:") :]
        target_host = _ascii_hostname(target.hostname)
        return target_host == domain or target_host.endswith(f".{domain}")
    prefix = _split_url(site, "Use a valid Search Console URL-prefix property identifier.")
    if (
        prefix.scheme.lower() != target.scheme.lower()
        or _ascii_hostname(prefix.hostname) != _ascii_hostname(target.hostname)
        or _effective_port(prefix) != _effective_port(target)
    ):
        return False
    prefix_path = prefix.path or "/"
    target_path = target.path or "/"
    if prefix_path == "/":
        return True
    boundary = prefix_path if prefix_path.endswith("/") else f"{prefix_path}/"
    return target_path == prefix_path or target_path.startswith(boundary)


def target_fingerprint(
    *,
    provider: str,
    resource_type: str,
    resource_name: str,
    operation: str,
    canonical_origin_value: str | None = None,
    site_url: str | None = None,
    sitemap_url: str | None = None,
    account_name: str | None = None,
    property_name: str | None = None,
) -> str:
    identity = {
        "provider": provider,
        "resource_type": resource_type,
        "resource_name": resource_name,
        "operation": operation,
        "canonical_origin": canonical_origin_value,
        "site_url": site_url,
        "sitemap_url": sitemap_url,
        "account_name": account_name,
        "property_name": property_name,
    }
    return fingerprint(identity)


def build_authorization(
    *,
    authorization_kind: str,
    allowed_action: str,
    operation_mode: str,
    target_fingerprint_value: str,
    now: datetime,
) -> tuple[dict[str, str], str]:
    basis = {
        "authorization_kind": authorization_kind,
        "allowed_action": allowed_action,
        "operation_mode": operation_mode,
        "target_fingerprint": target_fingerprint_value,
        "authorized_at": rfc3339(now),
        "expires_at": rfc3339(now + PLAN_TTL),
    }
    return basis, fingerprint(basis)


def build_plan(
    *,
    action: str,
    operation_mode: str,
    target_fingerprint_value: str,
    authorization_kind: str,
    payload: dict[str, object],
    clock: Callable[[], datetime] = utc_now,
) -> dict[str, object]:
    now = clock()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    authorization, authorization_fp = build_authorization(
        authorization_kind=authorization_kind,
        allowed_action=action,
        operation_mode=operation_mode,
        target_fingerprint_value=target_fingerprint_value,
        now=now,
    )
    plan: dict[str, object] = {
        "plan_version": "1.0.0",
        "action": action,
        "operation_mode": operation_mode,
        "target_fingerprint": target_fingerprint_value,
        "authorization": authorization,
        "authorization_fingerprint": authorization_fp,
        "created_at": rfc3339(now),
        "expires_at": rfc3339(now + PLAN_TTL),
        "payload": payload,
    }
    plan["plan_sha256"] = fingerprint(plan)
    return plan


def public_plan(plan: dict[str, object], *, output_file_status: str) -> dict[str, object]:
    return {
        "action": plan["action"],
        "operation_mode": plan["operation_mode"],
        "target_fingerprint": plan["target_fingerprint"],
        "authorization_fingerprint": plan["authorization_fingerprint"],
        "plan_sha256": plan["plan_sha256"],
        "created_at": plan["created_at"],
        "expires_at": plan["expires_at"],
        "output_file_status": output_file_status,
    }


def _allowed_temp_roots() -> set[Path]:
    roots = {Path(tempfile.gettempdir()).absolute(), Path("/tmp"), Path("/private/tmp")}
    return roots


def _validate_parent(parent: Path, *, create: bool) -> None:
    if parent.name == "" or not parent.name.startswith(PLAN_DIRECTORY_PREFIX):
        raise AdapterError(
            "plan_invalid",
            "blocked",
            12,
            f"Use a dedicated {PLAN_DIRECTORY_PREFIX}* task directory under the system temporary directory.",
        )
    if parent.parent.absolute() not in _allowed_temp_roots():
        raise AdapterError("plan_invalid", "blocked", 12, "Keep the plan in a dedicated system temporary task directory.")
    if create and not parent.exists():
        try:
            os.mkdir(parent, 0o700)
        except OSError as exc:
            raise AdapterError("plan_invalid", "blocked", 12, "Create a private task plan directory with mode 0700.") from exc
    try:
        info = os.lstat(parent)
    except OSError as exc:
        raise AdapterError("plan_invalid", "blocked", 12, "Use an existing private task plan directory.") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise AdapterError("plan_invalid", "blocked", 12, "The task plan parent must be a real directory, not a symlink.")
    if info.st_uid != os.getuid():
        raise AdapterError("plan_invalid", "blocked", 12, "The current user must own the task plan directory.")
    if stat.S_IMODE(info.st_mode) != 0o700:
        raise AdapterError("plan_invalid", "blocked", 12, "Set the task plan directory mode to 0700.")


def write_plan(path_value: str, plan: dict[str, object]) -> None:
    path = Path(path_value).absolute()
    _validate_parent(path.parent, create=True)
    try:
        os.lstat(path)
    except FileNotFoundError:
        pass
    else:
        raise AdapterError("plan_invalid", "blocked", 12, "Choose a new plan output file; existing files are never overwritten.")

    expected = fingerprint({key: value for key, value in plan.items() if key != "plan_sha256"})
    if plan.get("plan_sha256") != expected:
        raise AdapterError("plan_digest_mismatch", "blocked", 12, "Regenerate the plan before writing it.")
    raw = canonical_json(plan) + b"\n"
    temp_path = path.parent / f".{path.name}.{secrets.token_hex(8)}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd: int | None = None
    try:
        fd = os.open(temp_path, flags, 0o600)
        os.fchmod(fd, 0o600)
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = None
        os.link(temp_path, path, follow_symlinks=False)
        os.unlink(temp_path)
        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except FileExistsError as exc:
        raise AdapterError("plan_invalid", "blocked", 12, "Choose a new plan output file; existing files are never overwritten.") from exc
    except OSError as exc:
        raise AdapterError("plan_invalid", "blocked", 12, "The private plan file could not be written safely.") from exc
    finally:
        if fd is not None:
            os.close(fd)
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass


def _parse_time(value: object) -> datetime:
    if not isinstance(value, str):
        raise AdapterError("plan_invalid", "blocked", 12, "Regenerate the plan; its timestamp is invalid.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AdapterError("plan_invalid", "blocked", 12, "Regenerate the plan; its timestamp is invalid.") from exc
    if parsed.tzinfo is None:
        raise AdapterError("plan_invalid", "blocked", 12, "Regenerate the plan; its timestamp lacks a timezone.")
    return parsed.astimezone(timezone.utc)


class FileRecoveryStore:
    """Credential-free, cross-process limiter for one GSC recovery submit."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = (root or Path(tempfile.gettempdir()) / f"{RECOVERY_DIRECTORY_PREFIX}{os.getuid()}").absolute()

    @staticmethod
    def _now(value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _validate_fingerprint(value: str) -> None:
        if not _FINGERPRINT.fullmatch(value):
            raise AdapterError("authorization_mismatch", "blocked", 12, "Use the exact prior authorization fingerprint from the ambiguous submit.")

    def _ensure_root(self) -> None:
        try:
            os.mkdir(self._root, 0o700)
        except FileExistsError:
            pass
        except OSError as exc:
            raise AdapterError("plan_invalid", "blocked", 12, "The private recovery limiter directory could not be created.") from exc
        try:
            info = os.lstat(self._root)
        except OSError as exc:
            raise AdapterError("plan_invalid", "blocked", 12, "The private recovery limiter directory is inaccessible.") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise AdapterError("plan_invalid", "blocked", 12, "The recovery limiter must use a real private directory.")
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise AdapterError("plan_invalid", "blocked", 12, "The recovery limiter directory must be owned by the current user with mode 0700.")

    def _paths(self, target_fingerprint_value: str, authorization_fingerprint: str) -> tuple[Path, Path]:
        self._validate_fingerprint(target_fingerprint_value)
        self._validate_fingerprint(authorization_fingerprint)
        key = fingerprint(
            {
                "provider": "gsc",
                "operation": "sitemap_recovery_submit",
                "target_fingerprint": target_fingerprint_value,
                "authorization_fingerprint": authorization_fingerprint,
            }
        )
        return self._root / f"{key}.json", self._root / f"{key}.claimed"

    def _create(self, path: Path, payload: dict[str, object]) -> None:
        raw = canonical_json(payload) + b"\n"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd: int | None = None
        created = False
        completed = False
        try:
            fd = os.open(path, flags, 0o600)
            created = True
            os.fchmod(fd, 0o600)
            view = memoryview(raw)
            while view:
                written = os.write(fd, view)
                view = view[written:]
            os.fsync(fd)
            os.close(fd)
            fd = None
            dir_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
            completed = True
        finally:
            if fd is not None:
                os.close(fd)
            if created and not completed:
                try:
                    os.unlink(path)
                except FileNotFoundError:
                    pass

    def _read(self, path: Path) -> dict[str, object]:
        try:
            info = os.lstat(path)
        except FileNotFoundError:
            raise AdapterError("authorization_mismatch", "blocked", 12, "Recovery requires the prior ambiguous-submit checkpoint.") from None
        except OSError as exc:
            raise AdapterError("plan_invalid", "blocked", 12, "The recovery checkpoint is inaccessible.") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise AdapterError("plan_invalid", "blocked", 12, "The recovery checkpoint must be a regular file, not a symlink.")
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
            raise AdapterError("plan_invalid", "blocked", 12, "The recovery checkpoint must be owned by the current user with mode 0600.")
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(path, flags)
            try:
                open_info = os.fstat(fd)
                if open_info.st_dev != info.st_dev or open_info.st_ino != info.st_ino:
                    raise AdapterError("plan_invalid", "blocked", 12, "The recovery checkpoint identity changed while reading.")
                raw = os.read(fd, MAX_PLAN_BYTES + 1)
            finally:
                os.close(fd)
        except AdapterError:
            raise
        except OSError as exc:
            raise AdapterError("plan_invalid", "blocked", 12, "The recovery checkpoint could not be read safely.") from exc
        if len(raw) > MAX_PLAN_BYTES:
            raise AdapterError("plan_invalid", "blocked", 12, "The recovery checkpoint exceeded the safe size limit.")
        try:
            payload = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AdapterError("plan_invalid", "blocked", 12, "The recovery checkpoint is malformed.") from exc
        if not isinstance(payload, dict) or raw != canonical_json(payload) + b"\n":
            raise AdapterError("plan_invalid", "blocked", 12, "The recovery checkpoint is non-canonical.")
        digest = fingerprint({key: value for key, value in payload.items() if key != "checkpoint_sha256"})
        if payload.get("checkpoint_sha256") != digest:
            raise AdapterError("plan_digest_mismatch", "blocked", 12, "The recovery checkpoint digest does not match.")
        return payload

    def record_ambiguous(
        self,
        *,
        target_fingerprint_value: str,
        authorization_fingerprint: str,
        authorization_expires_at: str,
        clock: datetime,
    ) -> None:
        self._ensure_root()
        marker, _ = self._paths(target_fingerprint_value, authorization_fingerprint)
        now = self._now(clock)
        expires_at = _parse_time(authorization_expires_at)
        if now > expires_at:
            raise AdapterError("plan_expired", "blocked", 12, "The original submit authorization expired before recovery could be recorded.")
        payload: dict[str, object] = {
            "checkpoint_version": "1.0.0",
            "target_fingerprint": target_fingerprint_value,
            "authorization_fingerprint": authorization_fingerprint,
            "authorization_expires_at": rfc3339(expires_at),
            "ambiguous_at": rfc3339(now),
        }
        payload["checkpoint_sha256"] = fingerprint(payload)
        try:
            self._create(marker, payload)
        except FileExistsError:
            existing = self._read(marker)
            if existing.get("target_fingerprint") != target_fingerprint_value or existing.get("authorization_fingerprint") != authorization_fingerprint:
                raise AdapterError("authorization_mismatch", "blocked", 12, "The existing recovery checkpoint belongs to a different target or authorization.") from None
        except OSError as exc:
            raise AdapterError("plan_invalid", "blocked", 12, "The recovery checkpoint could not be recorded safely.") from exc

    def validate(
        self,
        *,
        target_fingerprint_value: str,
        authorization_fingerprint: str,
        clock: datetime,
    ) -> None:
        self._ensure_root()
        marker, claim = self._paths(target_fingerprint_value, authorization_fingerprint)
        payload = self._read(marker)
        if payload.get("target_fingerprint") != target_fingerprint_value or payload.get("authorization_fingerprint") != authorization_fingerprint:
            raise AdapterError("authorization_mismatch", "blocked", 12, "The recovery checkpoint target or authorization does not match.")
        now = self._now(clock)
        ambiguous_at = _parse_time(payload.get("ambiguous_at"))
        expires_at = _parse_time(payload.get("authorization_expires_at"))
        if ambiguous_at > now:
            raise AdapterError("plan_invalid", "blocked", 12, "The recovery checkpoint timestamp is in the future.")
        if now > expires_at or now > ambiguous_at + RECOVERY_WINDOW:
            raise AdapterError("plan_expired", "blocked", 12, "The original authorization or 15-minute recovery window has expired.")
        try:
            claim_info = os.lstat(claim)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise AdapterError("plan_invalid", "blocked", 12, "The recovery submit claim is inaccessible.") from exc
        if stat.S_ISLNK(claim_info.st_mode) or not stat.S_ISREG(claim_info.st_mode) or claim_info.st_uid != os.getuid() or stat.S_IMODE(claim_info.st_mode) != 0o600:
            raise AdapterError("plan_invalid", "blocked", 12, "The recovery submit claim is not a safe private file.")
        raise AdapterError("authorization_mismatch", "blocked", 12, "The single recovery submit has already been claimed; continue readback only.")

    def claim(
        self,
        *,
        target_fingerprint_value: str,
        authorization_fingerprint: str,
        plan_sha256: str,
        clock: datetime,
    ) -> None:
        self.validate(
            target_fingerprint_value=target_fingerprint_value,
            authorization_fingerprint=authorization_fingerprint,
            clock=clock,
        )
        _, claim = self._paths(target_fingerprint_value, authorization_fingerprint)
        payload: dict[str, object] = {
            "checkpoint_version": "1.0.0",
            "target_fingerprint": target_fingerprint_value,
            "authorization_fingerprint": authorization_fingerprint,
            "plan_sha256": plan_sha256,
            "claimed_at": rfc3339(self._now(clock)),
        }
        payload["checkpoint_sha256"] = fingerprint(payload)
        try:
            self._create(claim, payload)
        except FileExistsError:
            raise AdapterError("authorization_mismatch", "blocked", 12, "The single recovery submit was already claimed; continue readback only.") from None
        except OSError as exc:
            raise AdapterError("plan_invalid", "blocked", 12, "The recovery submit claim could not be recorded safely.") from exc


def read_plan(
    path_value: str,
    *,
    expected_sha256: str,
    authorization_fingerprint: str,
    allowed_actions: set[str],
    allowed_modes: set[str],
    clock: Callable[[], datetime] = utc_now,
) -> dict[str, object]:
    path = Path(path_value).absolute()
    _validate_parent(path.parent, create=False)
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise AdapterError("plan_invalid", "blocked", 12, "Regenerate the missing or inaccessible plan.") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise AdapterError("plan_invalid", "blocked", 12, "The plan must be a regular file, not a symlink.")
    if info.st_uid != os.getuid():
        raise AdapterError("plan_invalid", "blocked", 12, "The current user must own the plan file.")
    if stat.S_IMODE(info.st_mode) != 0o600:
        raise AdapterError("plan_invalid", "blocked", 12, "Set the plan file mode to 0600.")

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
        try:
            open_info = os.fstat(fd)
            if open_info.st_dev != info.st_dev or open_info.st_ino != info.st_ino:
                raise AdapterError("plan_invalid", "blocked", 12, "Regenerate the plan after an identity change.")
            raw = os.read(fd, MAX_PLAN_BYTES + 1)
        finally:
            os.close(fd)
    except AdapterError:
        raise
    except OSError as exc:
        raise AdapterError("plan_invalid", "blocked", 12, "The plan could not be read safely.") from exc
    if len(raw) > MAX_PLAN_BYTES:
        raise AdapterError("plan_invalid", "blocked", 12, "Regenerate the plan; it exceeds the size limit.")
    try:
        plan = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterError("plan_invalid", "blocked", 12, "Regenerate the malformed plan.") from exc
    if not isinstance(plan, dict):
        raise AdapterError("plan_invalid", "blocked", 12, "Regenerate the malformed plan.")
    canonical_raw = canonical_json(plan) + b"\n"
    if raw != canonical_raw:
        raise AdapterError("plan_digest_mismatch", "blocked", 12, "Regenerate the non-canonical plan.")
    digest = fingerprint({key: value for key, value in plan.items() if key != "plan_sha256"})
    if plan.get("plan_sha256") != digest or expected_sha256 != digest:
        raise AdapterError("plan_digest_mismatch", "blocked", 12, "Regenerate the plan after a digest mismatch.")
    if plan.get("authorization_fingerprint") != authorization_fingerprint:
        raise AdapterError("authorization_mismatch", "blocked", 12, "Use the authorization fingerprint from the current task orchestration.")
    if plan.get("action") not in allowed_actions or plan.get("operation_mode") not in allowed_modes:
        raise AdapterError("plan_invalid", "blocked", 12, "Regenerate a plan for the exact allowed operation.")
    now = clock()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if now.astimezone(timezone.utc) > _parse_time(plan.get("expires_at")):
        raise AdapterError("plan_expired", "blocked", 12, "Generate a fresh plan and re-read provider state.")
    authorization = plan.get("authorization")
    if not isinstance(authorization, dict) or fingerprint(authorization) != authorization_fingerprint:
        raise AdapterError("authorization_mismatch", "blocked", 12, "Regenerate the plan from the current authorization basis.")
    return plan


def consume_plan(path_value: str) -> None:
    path = Path(path_value).absolute()
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return
    if stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode) and info.st_uid == os.getuid():
        os.unlink(path)
