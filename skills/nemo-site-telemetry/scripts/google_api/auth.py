"""gcloud-backed ADC bootstrap and short-lived token acquisition."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
from typing import Callable, Mapping, Protocol, Sequence

from .output import AdapterError


SERVICES = (
    "searchconsole.googleapis.com",
    "analyticsadmin.googleapis.com",
    "analyticsdata.googleapis.com",
)

CAPABILITY_SCOPES = {
    "gsc-read": "https://www.googleapis.com/auth/webmasters.readonly",
    "gsc-sitemap-submit": "https://www.googleapis.com/auth/webmasters",
    "ga4-read": "https://www.googleapis.com/auth/analytics.readonly",
    "ga4-admin-write": "https://www.googleapis.com/auth/analytics.edit",
}

_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9._~+/=-]{20,4096}$")
_PROJECT_PATTERN = re.compile(r"^[a-z][a-z0-9-]{4,61}[a-z0-9]$")


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class Runner(Protocol):
    def run(self, argv: Sequence[str], *, timeout: float) -> CommandResult: ...


class SubprocessRunner:
    def run(self, argv: Sequence[str], *, timeout: float) -> CommandResult:
        try:
            result = subprocess.run(
                list(argv),
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AdapterError("prerequisite_missing", "required", 10, "Install or repair the Google Cloud CLI before using Google API mode.", reason=type(exc).__name__) from None
        return CommandResult(result.returncode, result.stdout, result.stderr)


@dataclass(frozen=True, slots=True)
class TokenContext:
    access_token: str
    auth_mode: str
    capability: str


def validate_project_id(value: str | None, *, required: bool) -> str | None:
    if value is None:
        if required:
            raise AdapterError("invalid_input", "blocked", 12, "Provide the exact Google Cloud project ID.")
        return None
    if not _PROJECT_PATTERN.fullmatch(value):
        raise AdapterError("invalid_input", "blocked", 12, "Provide a syntactically valid Google Cloud project ID.")
    return value


def ensure_python() -> None:
    if sys.version_info < (3, 11):
        raise AdapterError("prerequisite_missing", "required", 10, "Run the adapter with Python 3.11 or newer.")


def _repository_ancestor(path: Path) -> bool:
    return any((parent / ".git").exists() for parent in (path, *path.parents))


def validate_service_account_credential(path_value: str) -> None:
    path = Path(path_value).absolute()
    if _repository_ancestor(path.parent):
        raise AdapterError("prerequisite_missing", "required", 10, "Move the service-account credential outside every repository and worktree.")
    components = [path, *path.parents]
    for component in components:
        try:
            info = os.lstat(component)
        except OSError as exc:
            raise AdapterError("prerequisite_missing", "required", 10, "Provide an existing, private service-account credential file.") from exc
        if stat.S_ISLNK(info.st_mode):
            raise AdapterError("prerequisite_missing", "required", 10, "Credential path components cannot be symlinks.")
        if component == path:
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
                raise AdapterError("prerequisite_missing", "required", 10, "The credential must be a current-user-owned regular file with mode 0600 or stricter.")
        elif component != Path("/") and stat.S_IMODE(info.st_mode) & 0o022:
            raise AdapterError("prerequisite_missing", "required", 10, "Credential parent directories cannot be group or world writable.")


class GoogleAuthBroker:
    def __init__(
        self,
        runner: Runner | None = None,
        *,
        which: Callable[[str], str | None] = shutil.which,
        environ: Mapping[str, str] | None = None,
        impersonate_service_account: str | None = None,
    ) -> None:
        self._runner = runner or SubprocessRunner()
        self._which = which
        self._environ = dict(os.environ if environ is None else environ)
        self._impersonation = impersonate_service_account

    def auth_mode(self) -> str:
        if self._impersonation:
            return "impersonation"
        credential_path = self._environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if credential_path:
            validate_service_account_credential(credential_path)
            return "adc_service_account"
        return "adc_user"

    def _gcloud(self) -> str:
        binary = self._which("gcloud")
        if not binary:
            raise AdapterError("prerequisite_missing", "required", 10, "Install Google Cloud CLI explicitly or use the governed browser/manual fallback.")
        return binary

    def _ensure_token_capability(self, binary: str) -> None:
        result = self._runner.run([binary, "auth", "application-default", "print-access-token", "--help"], timeout=15.0)
        if result.returncode != 0 or "--scopes" not in result.stdout + result.stderr:
            raise AdapterError("gcloud_incompatible", "required", 10, "Update Google Cloud CLI to a version supporting ADC access-token scopes.")
        if self._impersonation and "--impersonate-service-account" not in result.stdout + result.stderr:
            raise AdapterError("gcloud_incompatible", "required", 10, "Use a gcloud version supporting service-account impersonation.")

    def token(self, capability: str) -> TokenContext:
        ensure_python()
        scope = CAPABILITY_SCOPES.get(capability)
        if not scope:
            raise AdapterError("invalid_input", "blocked", 12, "Choose one adapter capability from the fixed allowlist.")
        binary = self._gcloud()
        self._ensure_token_capability(binary)
        mode = self.auth_mode()
        argv = [binary, "auth", "application-default", "print-access-token", f"--scopes={scope}"]
        if self._impersonation:
            argv.append(f"--impersonate-service-account={self._impersonation}")
        result = self._runner.run(argv, timeout=30.0)
        token = result.stdout.strip()
        if result.returncode != 0:
            raise AdapterError("reauth_required", "required", 10, "Refresh Application Default Credentials without changing the selected account.")
        if "\n" in token or "\r" in token or not _TOKEN_PATTERN.fullmatch(token):
            raise AdapterError("reauth_required", "required", 10, "Refresh Application Default Credentials; no valid short-lived token was produced.")
        return TokenContext(token, mode, capability)

    def service_status(self, project_id: str) -> dict[str, str]:
        ensure_python()
        project = validate_project_id(project_id, required=True)
        binary = self._gcloud()
        result = self._runner.run(
            [binary, "services", "list", "--enabled", f"--project={project}", "--format=value(config.name)"],
            timeout=30.0,
        )
        if result.returncode != 0:
            raise AdapterError("capability_unknown", "blocked", 11, "Confirm serviceusage access on the exact Google Cloud project.")
        enabled = {line.strip() for line in result.stdout.splitlines() if line.strip()}
        return {service: ("enabled" if service in enabled else "disabled") for service in SERVICES}

    def enable_services(self, project_id: str) -> dict[str, str]:
        project = validate_project_id(project_id, required=True)
        before = self.service_status(project)
        missing = [service for service, status in before.items() if status != "enabled"]
        if missing:
            binary = self._gcloud()
            result = self._runner.run([binary, "services", "enable", *missing, f"--project={project}"], timeout=120.0)
            if result.returncode != 0:
                raise AdapterError("provider_rejected", "failed", 14, "Grant serviceusage.services.enable on the exact project, then retry the explicit bootstrap command.")
        after = self.service_status(project)
        if any(status != "enabled" for status in after.values()):
            raise AdapterError("api_not_enabled", "required", 10, "Re-read the exact project services after propagation completes.")
        return after
