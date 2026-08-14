#!/usr/bin/env python3
"""Verify public DNS, DNSSEC, TLS, canonical, robots, sitemap, and routes."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import shutil
import subprocess
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse


class CanonicalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): (value or "") for key, value in attrs}
        if tag.lower() == "link" and "canonical" in values.get("rel", "").lower().split():
            href = values.get("href", "").strip()
            if href:
                self.canonicals.append(href)


def validate_domain(value: str) -> str:
    domain = value.strip().lower().rstrip(".")
    if not domain or domain in {"localhost", "local"} or domain.endswith(".local"):
        raise ValueError("domain must be a public DNS hostname")
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        pass
    else:
        raise ValueError("IP literals are not allowed")
    if not re.fullmatch(r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", domain):
        raise ValueError("invalid public DNS hostname")
    return domain


def validate_resolver(value: str) -> str:
    resolver = value.strip().lower().rstrip(".")
    if not resolver:
        raise ValueError("resolver must not be empty")
    try:
        address = ipaddress.ip_address(resolver)
    except ValueError:
        return validate_domain(resolver)
    if not address.is_global:
        raise ValueError(f"resolver must be public: {value}")
    return address.compressed


def normalize_origin(value: str, domain: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or parsed.hostname != domain or parsed.path not in ("", "/"):
        raise ValueError("expected origin must be https://<domain> without a path")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("expected origin contains unsupported components")
    port = f":{parsed.port}" if parsed.port else ""
    return f"https://{domain}{port}"


def parse_dig_answers(output: str) -> list[dict[str, Any]]:
    answers: list[dict[str, Any]] = []
    for line in output.splitlines():
        parts = line.split(None, 4)
        if len(parts) != 5 or parts[2].upper() != "IN":
            continue
        try:
            ttl = int(parts[1])
        except ValueError:
            continue
        answers.append({"name": parts[0], "ttl": ttl, "type": parts[3].upper(), "value": parts[4]})
    return answers


def parse_dnssec_status(output: str) -> dict[str, Any]:
    status_match = re.search(r"status:\s*([A-Z]+)", output)
    flags_match = re.search(r"flags:\s*([^;]+);", output)
    flags = flags_match.group(1).split() if flags_match else []
    return {
        "status": status_match.group(1) if status_match else "UNKNOWN",
        "ad": "ad" in flags,
        "flags": flags,
    }


def dig_observation(domain: str, resolver: str, timeout: int) -> dict[str, Any]:
    if not shutil.which("dig"):
        return {"resolver": resolver, "error": "dig is not installed", "answers": {}, "dnssec": {}}

    answers: dict[str, Any] = {}
    for record_type in ("NS", "DS", "A", "AAAA", "CNAME"):
        command = [
            "dig",
            f"@{resolver}",
            domain,
            record_type,
            f"+time={max(1, timeout)}",
            "+tries=1",
            "+noall",
            "+answer",
        ]
        try:
            completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout + 2)
        except (OSError, subprocess.TimeoutExpired) as exc:
            answers[record_type] = {"ok": False, "records": [], "error": str(exc)}
            continue
        answers[record_type] = {
            "ok": completed.returncode == 0,
            "records": parse_dig_answers(completed.stdout),
            "error": completed.stderr.strip() or None,
        }

    dnssec_command = [
        "dig",
        f"@{resolver}",
        domain,
        "SOA",
        "+dnssec",
        "+adflag",
        f"+time={max(1, timeout)}",
        "+tries=1",
    ]
    try:
        completed = subprocess.run(dnssec_command, check=False, capture_output=True, text=True, timeout=timeout + 2)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "resolver": resolver,
            "answers": answers,
            "dnssec": {"ok": False, "status": "UNKNOWN", "ad": False, "flags": [], "error": str(exc)},
        }
    dnssec = parse_dnssec_status(completed.stdout)
    dnssec["ok"] = completed.returncode == 0
    dnssec["error"] = completed.stderr.strip() or None
    return {"resolver": resolver, "answers": answers, "dnssec": dnssec}


def fetch_url(url: str, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "nemo-domain-launch/0.2 public-verifier"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(1_000_001)
            content_type = response.headers.get("Content-Type", "")
            charset = response.headers.get_content_charset() or "utf-8"
            text = body[:1_000_000].decode(charset, errors="replace")
            return {
                "ok": 200 <= response.status < 300 and len(body) <= 1_000_000,
                "status": response.status,
                "final_url": response.geturl(),
                "content_type": content_type,
                "body": text,
                "body_truncated": len(body) > 1_000_000,
            }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        status = getattr(exc, "code", None)
        return {"ok": False, "status": status, "final_url": None, "content_type": None, "body": "", "error": str(exc)}


def canonical_from_html(text: str) -> list[str]:
    parser = CanonicalParser()
    parser.feed(text)
    return parser.canonicals


def sitemap_locations(text: str) -> tuple[list[str], str | None]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return [], str(exc)
    locations = [
        (element.text or "").strip()
        for element in root.iter()
        if element.tag.rsplit("}", 1)[-1] == "loc" and (element.text or "").strip()
    ]
    return locations, None


def robots_sitemap_urls(text: str) -> list[str]:
    urls: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        match = re.fullmatch(r"(?i)sitemap\s*:\s*(\S+)", line)
        if match:
            urls.append(match.group(1))
    return urls


def urls_equal(left: str, right: str) -> bool:
    left_parsed = urlparse(left)
    right_parsed = urlparse(right)
    try:
        return (
            left_parsed.scheme.lower() == right_parsed.scheme.lower()
            and left_parsed.hostname == right_parsed.hostname
            and left_parsed.port == right_parsed.port
            and left_parsed.path == right_parsed.path
            and not left_parsed.params
            and not left_parsed.query
            and not left_parsed.fragment
            and not left_parsed.username
            and not left_parsed.password
        )
    except ValueError:
        return False


def evaluate_report(
    report: dict[str, Any],
    expected_origin: str,
    representative_paths: list[str],
    require_cloudflare_ns: bool,
    require_dnssec: bool,
    allow_missing_canonical: bool = False,
    allow_missing_seo_files: bool = False,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: Any, *, not_required: bool = False) -> None:
        status = "not_required" if not_required else "passed" if ok else "failed"
        checks.append({"name": name, "status": status, "detail": detail})

    def same_route(expected_path: str, final_url: str | None) -> bool:
        actual_path = urlparse(final_url or "").path

        def normalized(value: str) -> str:
            return "/" if value == "/" else value.rstrip("/")

        return normalized(actual_path) == normalized(expected_path)

    def mapping(value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    expected = urlparse(expected_origin)

    def expected_https_route(path: str, observation: dict[str, Any]) -> bool:
        final = urlparse(str(observation.get("final_url") or ""))
        try:
            return (
                observation.get("ok") is True
                and final.scheme == "https"
                and final.hostname == expected.hostname
                and final.port == expected.port
                and same_route(path, observation.get("final_url"))
            )
        except ValueError:
            return False

    observations = report.get("dns", [])
    if not isinstance(observations, list):
        observations = []
    ns_by_resolver: dict[str, list[str]] = {}
    ds_by_resolver: dict[str, list[str]] = {}
    ad_resolvers: list[str] = []
    for item in observations:
        if not isinstance(item, dict):
            continue
        resolver_value = item.get("resolver")
        if not isinstance(resolver_value, str) or not resolver_value.strip():
            continue
        resolver = resolver_value.strip()
        answers = mapping(item.get("answers"))

        def record_values(record_type: str) -> list[str]:
            group = mapping(answers.get(record_type))
            records = group.get("records")
            if not isinstance(records, list):
                return []
            return [
                str(record.get("value"))
                for record in records
                if isinstance(record, dict) and isinstance(record.get("value"), str) and record.get("value").strip()
            ]

        ns_by_resolver[resolver] = record_values("NS")
        ds_by_resolver[resolver] = record_values("DS")
        dnssec = mapping(item.get("dnssec"))
        if dnssec.get("ok") is True and dnssec.get("status") == "NOERROR" and dnssec.get("ad") is True:
            ad_resolvers.append(resolver)

    def normalized_sets(records_by_resolver: dict[str, list[str]]) -> list[tuple[str, ...]]:
        return [
            tuple(sorted({str(value).strip().lower().rstrip(".") for value in values if str(value).strip()}))
            for values in records_by_resolver.values()
        ]

    ns_sets = normalized_sets(ns_by_resolver)
    ns_consistent = len(ns_sets) >= 2 and all(ns_sets) and len(set(ns_sets)) == 1

    if require_cloudflare_ns:
        ns_ok = ns_consistent and all(
            len(values) >= 2 and all(value.lower().rstrip(".").endswith(".ns.cloudflare.com") for value in values)
            for values in ns_by_resolver.values()
        )
        check("cloudflare_nameservers", ns_ok, ns_by_resolver)
    else:
        check("public_nameservers_observed", ns_consistent, ns_by_resolver)

    if require_dnssec:
        ds_sets = normalized_sets(ds_by_resolver)
        ds_ok = len(ds_sets) >= 2 and all(ds_sets) and len(set(ds_sets)) == 1
        check("parent_ds", ds_ok, ds_by_resolver)
        check("dnssec_ad", len(set(ad_resolvers)) >= 2, sorted(set(ad_resolvers)))

    http = mapping(report.get("http"))
    root = mapping(http.get("/"))
    check(
        "https_root",
        expected_https_route("/", root),
        {k: root.get(k) for k in ("status", "final_url", "error")},
    )
    root_body = root.get("body") if isinstance(root.get("body"), str) else ""
    canonicals = canonical_from_html(root_body)
    canonical_ok = bool(canonicals) and all(
        urlparse(value).scheme == "https" and urlparse(value).netloc == urlparse(expected_origin).netloc
        for value in canonicals
    )
    check(
        "canonical_origin",
        canonical_ok,
        canonicals,
        not_required=allow_missing_canonical and not canonicals,
    )

    representative = {path: expected_https_route(path, mapping(http.get(path))) for path in representative_paths}
    check("representative_paths", bool(representative) and all(representative.values()), representative)

    robots = mapping(http.get("/robots.txt"))
    expected_sitemap = f"{expected_origin}/sitemap.xml"
    robots_body = robots.get("body") if isinstance(robots.get("body"), str) else ""
    observed_sitemaps = robots_sitemap_urls(robots_body)
    robots_missing = not robots or robots.get("status") in {404, 410}
    check(
        "robots",
        robots.get("ok") is True and any(urls_equal(value, expected_sitemap) for value in observed_sitemaps),
        {"status": robots.get("status"), "expected_sitemap": expected_sitemap, "observed": observed_sitemaps},
        not_required=allow_missing_seo_files and robots_missing,
    )

    sitemap = mapping(http.get("/sitemap.xml"))
    sitemap_body = sitemap.get("body") if isinstance(sitemap.get("body"), str) else ""
    locations, parse_error = sitemap_locations(sitemap_body) if sitemap.get("ok") is True else ([], None)
    sitemap_ok = bool(sitemap.get("ok")) and not parse_error and bool(locations) and all(
        urlparse(value).scheme == "https" and urlparse(value).netloc == urlparse(expected_origin).netloc
        for value in locations
    )
    sitemap_missing = not sitemap or sitemap.get("status") in {404, 410}
    check(
        "sitemap",
        sitemap_ok,
        {"status": sitemap.get("status"), "url_count": len(locations), "parse_error": parse_error},
        not_required=allow_missing_seo_files and sitemap_missing,
    )

    failures = [item["name"] for item in checks if item["status"] == "failed"]
    return {"checks": checks, "summary": {"ok": not failures, "failures": failures}}


def run_verification(
    domain_value: str,
    expected_origin_value: str,
    representative_paths: list[str],
    resolvers: list[str],
    timeout: int,
    require_cloudflare_ns: bool,
    require_dnssec: bool,
    allow_missing_canonical: bool = False,
    allow_missing_seo_files: bool = False,
) -> dict[str, Any]:
    domain = validate_domain(domain_value)
    expected_origin = normalize_origin(expected_origin_value, domain)
    paths = ["/", "/robots.txt", "/sitemap.xml"]
    for raw in representative_paths:
        parsed = urlparse(raw)
        if (
            parsed.scheme
            or parsed.netloc
            or parsed.params
            or not parsed.path.startswith("/")
            or parsed.query
            or parsed.fragment
            or any(part in {".", ".."} for part in parsed.path.split("/"))
        ):
            raise ValueError(f"invalid representative path: {raw}")
        if parsed.path not in paths:
            paths.append(parsed.path)

    validated_resolvers = [validate_resolver(value) for value in resolvers]
    if len(set(validated_resolvers)) < 2:
        raise ValueError("at least two distinct public resolvers are required")

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "domain": domain,
        "expected_origin": expected_origin,
        "dns": [dig_observation(domain, resolver, timeout) for resolver in validated_resolvers],
        "http": {path: fetch_url(urljoin(expected_origin + "/", path.lstrip("/")), timeout) for path in paths},
        "requirements": {
            "cloudflare_nameservers": require_cloudflare_ns,
            "dnssec": require_dnssec,
            "representative_paths": representative_paths,
            "canonical_required": not allow_missing_canonical,
            "seo_files_required": not allow_missing_seo_files,
        },
    }
    report.update(
        evaluate_report(
            report,
            expected_origin,
            representative_paths,
            require_cloudflare_ns,
            require_dnssec,
            allow_missing_canonical,
            allow_missing_seo_files,
        )
    )
    for observation in report["http"].values():
        observation.pop("body", None)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain")
    parser.add_argument("--expected-origin", required=True)
    parser.add_argument("--representative-path", action="append", default=[])
    parser.add_argument("--resolver", action="append")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--require-cloudflare-ns", action="store_true")
    parser.add_argument("--require-dnssec", action="store_true")
    parser.add_argument("--allow-missing-canonical", action="store_true")
    parser.add_argument("--allow-missing-seo-files", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    resolvers = args.resolver or ["1.1.1.1", "8.8.8.8"]
    try:
        payload = run_verification(
            args.domain,
            args.expected_origin,
            args.representative_path,
            resolvers,
            max(1, min(args.timeout, 60)),
            args.require_cloudflare_ns,
            args.require_dnssec,
            args.allow_missing_canonical,
            args.allow_missing_seo_files,
        )
    except ValueError as exc:
        payload = {"schema_version": "1.0", "summary": {"ok": False, "failures": [str(exc)]}}
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if not payload.get("summary", {}).get("ok"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
