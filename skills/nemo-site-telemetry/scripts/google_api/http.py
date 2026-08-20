"""Bounded urllib transport for the adapter's Google REST allowlist."""

from __future__ import annotations

from dataclasses import dataclass
import http.client
import ipaddress
import json
import random
import socket
import time
from typing import Callable, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import SplitResult, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET

from .output import AdapterError, normalize_provider_status, redact_text


GOOGLE_API_HOSTS = frozenset(
    {
        "www.googleapis.com",
        "searchconsole.googleapis.com",
        "analyticsadmin.googleapis.com",
        "analyticsdata.googleapis.com",
    }
)
READ_METHODS = frozenset({"GET"})
MAX_PROVIDER_BODY = 2 * 1024 * 1024
MAX_PUBLIC_BODY = 4 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status: int
    body: bytes
    final_url: str
    location: str | None = None


class Transport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout: float,
    ) -> HttpResponse: ...


class _SameHostRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        original = urlsplit(req.full_url).hostname
        target = urlsplit(newurl).hostname
        if not original or not target or original.lower() != target.lower():
            raise HTTPError(req.full_url, code, "cross-host redirect blocked", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class UrlLibTransport:
    def __init__(self, *, max_body: int = MAX_PROVIDER_BODY) -> None:
        self._max_body = max_body
        self._opener = build_opener(_SameHostRedirectHandler())

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout: float,
    ) -> HttpResponse:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() not in GOOGLE_API_HOSTS:
            raise AdapterError("invalid_input", "blocked", 12, "The provider endpoint is outside the Google API allowlist.")
        normalized_method = method.upper()
        if normalized_method not in {"GET", "POST", "PUT"}:
            raise AdapterError("invalid_input", "blocked", 12, "The HTTP method is outside the adapter allowlist.")
        request = Request(url, data=body, headers=dict(headers), method=normalized_method)
        try:
            with self._opener.open(request, timeout=timeout) as response:
                response_body = response.read(self._max_body + 1)
                if len(response_body) > self._max_body:
                    raise AdapterError("provider_rejected", "failed", 14, "The provider response exceeded the safe size limit.")
                final_url = response.geturl()
                if (urlsplit(final_url).hostname or "").lower() != (parsed.hostname or "").lower():
                    raise AdapterError("provider_rejected", "failed", 14, "A cross-host provider redirect was blocked.")
                return HttpResponse(int(response.status), response_body, final_url)
        except HTTPError as exc:
            response_body = exc.read(self._max_body + 1)
            if len(response_body) > self._max_body:
                response_body = b""
            return HttpResponse(int(exc.code), response_body, exc.geturl() or url)
        except (URLError, TimeoutError, socket.timeout) as exc:
            raise AdapterError(
                "provider_transient",
                "pending",
                13,
                "Read back the exact resource before any write retry.",
                reason=type(exc).__name__,
                retryable=True,
            ) from None


def _safe_google_reason(body: bytes) -> tuple[str | int | None, str | None]:
    if not body:
        return None, None
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, None
    if not isinstance(payload, dict) or not isinstance(payload.get("error"), dict):
        return None, None
    error = payload["error"]
    provider_status = normalize_provider_status(error.get("status") or error.get("code"))
    reason: object | None = None
    details = error.get("details")
    if isinstance(details, list):
        for detail in details:
            if isinstance(detail, dict) and isinstance(detail.get("reason"), str):
                reason = detail["reason"]
                break
    if reason is None:
        errors = error.get("errors")
        if isinstance(errors, list):
            for item in errors:
                if isinstance(item, dict) and isinstance(item.get("reason"), str):
                    reason = item["reason"]
                    break
    safe_reason = redact_text(reason, limit=128) if reason is not None else None
    return provider_status, safe_reason


def _http_error(status: int, body: bytes, *, write: bool) -> AdapterError:
    provider_status, reason = _safe_google_reason(body)
    normalized = (reason or "").upper()
    if status == 401:
        return AdapterError("reauth_required", "required", 10, "Refresh Application Default Credentials, then rerun the readback.", provider_status, reason)
    if status == 403:
        if "SCOPE" in normalized:
            return AdapterError("scope_insufficient", "blocked", 11, "Grant only the required capability scope, then rerun the probe.", provider_status, reason)
        if normalized in {"USER_PERMISSION_DENIED", "RESOURCE_PERMISSION_DENIED", "ACCESS_DENIED"}:
            return AdapterError("resource_access_insufficient", "blocked", 11, "Grant the current identity access to the exact provider resource.", provider_status, reason)
        return AdapterError("capability_unknown", "blocked", 11, "Inspect scope and exact resource role separately; the provider did not distinguish them.", provider_status, reason)
    if status == 404:
        return AdapterError("not_found", "failed", 14, "Confirm the exact immutable resource identifier.", provider_status or status, reason)
    if status == 429:
        return AdapterError("provider_transient", "pending", 13, "Wait within the bounded retry window, then read back the exact resource.", provider_status or status, reason, True)
    if status >= 500:
        if write:
            return AdapterError("ambiguous_write", "pending", 13, "Read back the exact target before considering a fresh recovery plan.", provider_status or status, reason, True)
        return AdapterError("provider_transient", "pending", 13, "Retry the read within the bounded read window.", provider_status or status, reason, True)
    return AdapterError("provider_rejected", "failed", 14, "Correct the exact request inputs before retrying.", provider_status or status, reason)


class GoogleApiClient:
    def __init__(
        self,
        transport: Transport,
        *,
        access_token: str,
        quota_project_id: str | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        random_source: Callable[[], float] = random.random,
    ) -> None:
        self._transport = transport
        self._access_token = access_token
        self._quota_project_id = quota_project_id
        self._sleeper = sleeper
        self._random = random_source

    def request_json(
        self,
        method: str,
        url: str,
        *,
        body: dict[str, object] | None = None,
        allow_not_found: bool = False,
        read_attempts: int = 3,
        read_only: bool = False,
    ) -> dict[str, object] | list[object] | None:
        normalized_method = method.upper()
        is_read = normalized_method in READ_METHODS or read_only
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._access_token}",
            "User-Agent": "nemo-site-telemetry-google-api-adapter",
        }
        encoded_body = None
        if body is not None:
            encoded_body = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self._quota_project_id:
            headers["X-Goog-User-Project"] = self._quota_project_id

        maximum = read_attempts if is_read else 1
        for attempt in range(maximum):
            try:
                response = self._transport.request(normalized_method, url, headers=headers, body=encoded_body, timeout=20.0)
            except AdapterError as exc:
                if is_read and exc.error_code == "provider_transient":
                    if attempt + 1 < maximum:
                        self._sleeper(min(8.0, (2**attempt) + self._random()))
                        continue
                    raise AdapterError(
                        "provider_transient",
                        "pending",
                        13,
                        "Retry the read within the bounded read window.",
                        provider_status=exc.provider_status,
                        reason=exc.reason,
                        retryable=True,
                    ) from None
                if not is_read and exc.error_code == "provider_transient":
                    raise AdapterError(
                        "ambiguous_write",
                        "pending",
                        13,
                        "Read back the exact target before considering a fresh recovery plan.",
                        reason=exc.reason,
                        retryable=True,
                    ) from None
                raise
            if 200 <= response.status < 300:
                if not response.body:
                    return None
                try:
                    decoded = json.loads(response.body)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise AdapterError("provider_rejected", "failed", 14, "The provider returned a non-JSON response for a JSON API method.") from exc
                if not isinstance(decoded, (dict, list)):
                    raise AdapterError("provider_rejected", "failed", 14, "The provider JSON response had an unsupported shape.")
                return decoded
            if response.status == 404 and allow_not_found:
                return None
            error = _http_error(response.status, response.body, write=not is_read)
            if is_read and error.retryable and attempt + 1 < maximum:
                self._sleeper(min(8.0, (2**attempt) + self._random()))
                continue
            raise error
        raise AdapterError("provider_transient", "pending", 13, "Retry the bounded provider read.", retryable=True)


class PublicXmlFetcher(Protocol):
    def fetch(self, url: str) -> dict[str, object]: ...


def _public_host(hostname: str | None) -> str:
    if not hostname:
        raise AdapterError("invalid_input", "blocked", 12, "Use an absolute public sitemap URL.")
    try:
        return hostname.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise AdapterError("invalid_input", "blocked", 12, "Use a valid public sitemap hostname.") from exc


def _resolve_public_url(
    url: str,
    resolver: Callable[..., list[tuple[object, ...]]],
) -> tuple[SplitResult, str, int, tuple[str, ...]]:
    try:
        parsed = urlsplit(url)
    except ValueError as exc:
        raise AdapterError("invalid_input", "blocked", 12, "Use a valid absolute public sitemap URL.") from exc
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise AdapterError("invalid_input", "blocked", 12, "Use an absolute public sitemap URL.")
    if parsed.username is not None or parsed.password is not None or parsed.fragment:
        raise AdapterError("invalid_input", "blocked", 12, "Remove user information and fragments from the public sitemap URL.")
    host = _public_host(parsed.hostname)
    try:
        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    except ValueError as exc:
        raise AdapterError("invalid_input", "blocked", 12, "Use a valid public sitemap URL port.") from exc
    try:
        answers = resolver(host, port, type=socket.SOCK_STREAM)
    except (OSError, socket.gaierror) as exc:
        raise AdapterError(
            "provider_transient",
            "pending",
            13,
            "Retry the public sitemap DNS preflight before planning a submit.",
            reason=type(exc).__name__,
            retryable=True,
        ) from None
    addresses: list[str] = []
    for answer in answers:
        try:
            socket_address = answer[4]
            raw_address = socket_address[0]  # type: ignore[index]
            address = ipaddress.ip_address(str(raw_address).split("%", 1)[0])
        except (IndexError, TypeError, ValueError):
            raise AdapterError("provider_rejected", "failed", 14, "The public sitemap hostname returned an invalid DNS address.") from None
        if not address.is_global:
            raise AdapterError(
                "invalid_input",
                "blocked",
                12,
                "The public sitemap URL resolved to a non-public address; private, loopback, link-local, and reserved targets are blocked.",
            )
        normalized = str(address)
        if normalized not in addresses:
            addresses.append(normalized)
    if not addresses:
        raise AdapterError(
            "provider_transient",
            "pending",
            13,
            "Retry the public sitemap DNS preflight after the hostname has public addresses.",
            retryable=True,
        )
    return parsed, host, port, tuple(addresses)


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host: str, port: int, pinned_address: str, timeout: float) -> None:
        super().__init__(host, port=port, timeout=timeout)
        self._pinned_address = pinned_address

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self._pinned_address, self.port),
            self.timeout,
            self.source_address,
        )


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, port: int, pinned_address: str, timeout: float) -> None:
        super().__init__(host, port=port, timeout=timeout)
        self._pinned_address = pinned_address

    def connect(self) -> None:
        sock = socket.create_connection(
            (self._pinned_address, self.port),
            self.timeout,
            self.source_address,
        )
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def _public_connection(
    scheme: str,
    host: str,
    port: int,
    address: str,
    timeout: float,
) -> http.client.HTTPConnection:
    if scheme == "https":
        return _PinnedHTTPSConnection(host, port, address, timeout)
    return _PinnedHTTPConnection(host, port, address, timeout)


class UrlLibPublicXmlFetcher:
    def __init__(
        self,
        *,
        resolver: Callable[..., list[tuple[object, ...]]] = socket.getaddrinfo,
        connection_factory: Callable[[str, str, int, str, float], http.client.HTTPConnection] = _public_connection,
        max_redirects: int = 3,
    ) -> None:
        self._resolver = resolver
        self._connection_factory = connection_factory
        self._max_redirects = max_redirects

    def _request_once(self, url: str) -> HttpResponse:
        parsed, host, port, addresses = _resolve_public_url(url, self._resolver)
        path = urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
        last_error: Exception | None = None
        for address in addresses:
            connection = self._connection_factory(parsed.scheme.lower(), host, port, address, 20.0)
            try:
                connection.request(
                    "GET",
                    path,
                    headers={
                        "Accept": "application/xml,text/xml,*/*;q=0.1",
                        "User-Agent": "nemo-site-telemetry-sitemap-check",
                    },
                )
                response = connection.getresponse()
                body = response.read(MAX_PUBLIC_BODY + 1)
                return HttpResponse(int(response.status), body, url, response.getheader("Location"))
            except (OSError, TimeoutError, socket.timeout, http.client.HTTPException, ValueError) as exc:
                last_error = exc
            finally:
                connection.close()
        raise AdapterError(
            "provider_transient",
            "pending",
            13,
            "Retry the public sitemap preflight before planning a submit.",
            reason=type(last_error).__name__ if last_error is not None else None,
            retryable=True,
        ) from None

    def fetch(self, url: str) -> dict[str, object]:
        try:
            initial = urlsplit(url)
        except ValueError as exc:
            raise AdapterError("invalid_input", "blocked", 12, "Use a valid absolute public sitemap URL.") from exc
        original_host = _public_host(initial.hostname)
        current = url
        seen: set[str] = set()
        response: HttpResponse | None = None
        for redirect_count in range(self._max_redirects + 1):
            if current in seen:
                raise AdapterError("provider_rejected", "failed", 14, "The public sitemap redirect loop was blocked.")
            seen.add(current)
            response = self._request_once(current)
            if response.status not in {301, 302, 303, 307, 308}:
                break
            if redirect_count >= self._max_redirects:
                raise AdapterError("provider_rejected", "failed", 14, "The public sitemap exceeded the redirect limit.")
            location = response.location
            if not location:
                raise AdapterError("provider_rejected", "failed", 14, "The public sitemap redirect omitted its target.")
            target = urljoin(current, location)
            target_parsed, target_host, _, _ = _resolve_public_url(target, self._resolver)
            if target_host != original_host:
                raise AdapterError("target_mismatch", "blocked", 12, "The public sitemap redirected to a different hostname.")
            if urlsplit(current).scheme.lower() == "https" and target_parsed.scheme.lower() != "https":
                raise AdapterError("target_mismatch", "blocked", 12, "The public sitemap HTTPS redirect cannot downgrade to HTTP.")
            current = target
        assert response is not None
        body = response.body
        status = response.status
        if len(body) > MAX_PUBLIC_BODY or not body:
            raise AdapterError("invalid_input", "blocked", 12, "The public sitemap must be non-empty and within the adapter size limit.")
        if status < 200 or status >= 300:
            raise AdapterError("provider_rejected", "failed", 14, "The public sitemap did not return a successful response.", status)
        try:
            root = ET.fromstring(body)
        except ET.ParseError as exc:
            raise AdapterError("invalid_input", "blocked", 12, "The public sitemap response is not parseable XML.") from exc
        root_name = root.tag.rsplit("}", 1)[-1]
        if root_name not in {"urlset", "sitemapindex"}:
            raise AdapterError("invalid_input", "blocked", 12, "The public XML is not a sitemap urlset or sitemapindex.")
        return {"status": status, "root": root_name, "non_empty": True}
