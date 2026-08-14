#!/usr/bin/env python3
"""Read-only production-origin audit for a prebuilt static site."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class CanonicalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link":
            return
        values = {key.lower(): (value or "") for key, value in attrs}
        rel = {part.lower() for part in values.get("rel", "").split()}
        href = values.get("href", "").strip()
        if "canonical" in rel and href:
            self.canonicals.append(href)


def normalize_origin(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("origin must be an absolute https URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("origin must not contain credentials, query, or fragment")
    if parsed.path not in ("", "/"):
        raise ValueError("origin must not contain a path")
    host = parsed.hostname.lower()
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        raise ValueError("origin must be a public hostname")
    port = f":{parsed.port}" if parsed.port else ""
    return f"https://{host}{port}"


def route_for_html(output_dir: Path, html_file: Path) -> str:
    relative = html_file.relative_to(output_dir).as_posix()
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        return "/" + relative[: -len("index.html")]
    return "/" + relative


def canonical_urls(path: Path) -> list[str]:
    parser = CanonicalParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return parser.canonicals


def url_matches_origin(value: str, origin: str) -> bool:
    parsed = urlparse(value)
    expected = urlparse(origin)
    try:
        return (
            parsed.scheme == expected.scheme
            and parsed.hostname == expected.hostname
            and parsed.port == expected.port
            and not parsed.username
            and not parsed.password
        )
    except ValueError:
        return False


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


def path_exists_for_route(output_dir: Path, route: str) -> bool:
    parsed = urlparse(route)
    if (
        parsed.scheme
        or parsed.netloc
        or parsed.params
        or parsed.query
        or parsed.fragment
        or not parsed.path.startswith("/")
        or any(part in {".", ".."} for part in parsed.path.split("/"))
    ):
        return False
    relative = parsed.path.lstrip("/")
    candidates: list[Path]
    if not relative:
        candidates = [output_dir / "index.html"]
    elif parsed.path.endswith("/"):
        candidates = [output_dir / relative / "index.html"]
    else:
        target = output_dir / relative
        candidates = [target]
        if not target.suffix:
            candidates.extend([output_dir / relative / "index.html", output_dir / f"{relative}.html"])
    return any(candidate.is_file() for candidate in candidates)


def git_summary(project_dir: Path) -> dict[str, Any]:
    def run(*args: str) -> subprocess.CompletedProcess[str]:
        command = ["git", "-C", str(project_dir), *args]
        try:
            return subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return subprocess.CompletedProcess(command, 1, "", str(exc))

    probe = run("rev-parse", "--is-inside-work-tree")
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        return {"is_git_repository": False, "source_revision": None, "dirty": None}
    revision = run("rev-parse", "HEAD")
    status = run("status", "--porcelain")
    lines = [line for line in status.stdout.splitlines() if line.strip()]
    return {
        "is_git_repository": True,
        "source_revision": revision.stdout.strip() if revision.returncode == 0 else None,
        "dirty": bool(lines),
        "changed_path_count": len(lines),
    }


def package_scripts(project_dir: Path) -> list[str]:
    package_json = project_dir / "package.json"
    if not package_json.is_file():
        return []
    try:
        payload = json.loads(package_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    scripts = payload.get("scripts", {}) if isinstance(payload, dict) else {}
    return sorted(str(key) for key in scripts) if isinstance(scripts, dict) else []


def sitemap_locations(path: Path) -> tuple[list[str], str | None]:
    if not path.is_file():
        return [], None
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8", errors="replace"))
    except ET.ParseError as exc:
        return [], str(exc)
    locations = [
        (element.text or "").strip()
        for element in root.iter()
        if element.tag.rsplit("}", 1)[-1] == "loc" and (element.text or "").strip()
    ]
    return locations, None


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: Any) -> None:
    checks.append({"name": name, "status": "passed" if ok else "failed", "detail": detail})


def run_preflight(
    project_dir: Path,
    output_dir_value: str,
    origin_value: str,
    representative_paths: list[str],
    allow_missing_canonical: bool = False,
    allow_missing_seo_files: bool = False,
) -> dict[str, Any]:
    project_dir = project_dir.expanduser().resolve()
    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    try:
        origin = normalize_origin(origin_value)
        add_check(checks, "production_origin", True, origin)
    except ValueError as exc:
        origin = ""
        add_check(checks, "production_origin", False, str(exc))

    project_ok = project_dir.is_dir()
    add_check(checks, "project_directory", project_ok, str(project_dir))
    output_dir = Path(output_dir_value).expanduser()
    if not output_dir.is_absolute():
        output_dir = project_dir / output_dir
    output_dir = output_dir.resolve()
    try:
        output_dir.relative_to(project_dir)
        output_in_project = True
    except ValueError:
        output_in_project = False
    add_check(checks, "output_within_project", output_in_project, str(output_dir))
    output_exists = output_in_project and output_dir.is_dir()
    add_check(checks, "output_directory", output_exists, str(output_dir))

    html_files = sorted(output_dir.rglob("*.html")) if output_exists else []
    add_check(checks, "html_output", bool(html_files), {"count": len(html_files)})
    index_exists = output_exists and (output_dir / "index.html").is_file()
    add_check(checks, "root_index", index_exists, "index.html")

    canonical_records: list[dict[str, Any]] = []
    missing_canonical: list[str] = []
    wrong_origin: list[dict[str, str]] = []
    for html_file in html_files:
        route = route_for_html(output_dir, html_file)
        values = canonical_urls(html_file)
        if not values:
            missing_canonical.append(route)
        for value in values:
            record = {"route": route, "canonical": value}
            canonical_records.append(record)
            if not url_matches_origin(value, origin):
                wrong_origin.append(record)
    canonical_ok = not wrong_origin and (allow_missing_canonical or not missing_canonical)
    add_check(
        checks,
        "canonicals",
        canonical_ok,
        {
            "count": len(canonical_records),
            "missing_routes": missing_canonical,
            "wrong_origin": wrong_origin,
        },
    )

    robots_path = output_dir / "robots.txt"
    robots_exists = output_exists and robots_path.is_file()
    robots_text = robots_path.read_text(encoding="utf-8", errors="replace") if robots_exists else ""
    expected_sitemap = f"{origin}/sitemap.xml"
    sitemap_directives = robots_sitemap_urls(robots_text)
    robots_ok = robots_exists and any(urls_equal(value, expected_sitemap) for value in sitemap_directives)
    if allow_missing_seo_files and not robots_exists:
        robots_ok = True
    add_check(
        checks,
        "robots_sitemap",
        robots_ok,
        {"exists": robots_exists, "expected": expected_sitemap, "observed": sitemap_directives},
    )

    sitemap_path = output_dir / "sitemap.xml"
    sitemap_exists = output_exists and sitemap_path.is_file()
    locations, sitemap_error = sitemap_locations(sitemap_path) if sitemap_exists else ([], None)
    wrong_sitemap_origin = [value for value in locations if not url_matches_origin(value, origin)]
    sitemap_ok = sitemap_exists and not sitemap_error and bool(locations) and not wrong_sitemap_origin
    if allow_missing_seo_files and not sitemap_exists:
        sitemap_ok = True
    add_check(
        checks,
        "sitemap",
        sitemap_ok,
        {
            "exists": sitemap_exists,
            "url_count": len(locations),
            "parse_error": sitemap_error,
            "wrong_origin": wrong_sitemap_origin,
        },
    )

    representative_results = {
        route: output_exists and path_exists_for_route(output_dir, route) for route in representative_paths
    }
    add_check(
        checks,
        "representative_paths",
        bool(representative_results) and all(representative_results.values()),
        representative_results,
    )

    failures = [check["name"] for check in checks if check["status"] == "failed"]
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_dir": str(project_dir),
        "output_dir": str(output_dir),
        "production_origin": origin,
        "git": git_summary(project_dir) if project_ok and shutil.which("git") else {"is_git_repository": False},
        "package_scripts": package_scripts(project_dir) if project_ok else [],
        "tools": {
            name: bool(shutil.which(name)) for name in ("node", "npm", "npx", "dig", "curl", "openssl")
        },
        "checks": checks,
        "summary": {"ok": not failures, "failures": failures},
    }


def write_output(payload: dict[str, Any], output: str | None) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output:
        path = Path(output).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--representative-path", action="append", default=[])
    parser.add_argument("--allow-missing-canonical", action="store_true")
    parser.add_argument("--allow-missing-seo-files", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = run_preflight(
        Path(args.project_dir),
        args.output_dir,
        args.origin,
        args.representative_path,
        args.allow_missing_canonical,
        args.allow_missing_seo_files,
    )
    write_output(payload, args.output)
    if not payload["summary"]["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
