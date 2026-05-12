from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, quote, unquote, urlsplit, urlunsplit


URL_PATTERN = re.compile(r"https?://[^\s\]>)\"']+")
TOP_LEVEL_KEY_PATTERN = re.compile(r"^([A-Za-z0-9_-]+):(?:\s*(.*))?$")
TRACKING_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_psn",
    "share_code",
    "source",
    "zhida_source",
    "needBackground",
}


class UrlIdentityClass:
    SOURCE_CANONICAL_URL = "source_canonical_url"
    SOURCE_URL_NEEDS_NORMALIZE = "source_url_needs_normalize"
    SOURCE_TEXT_REFS_URL = "source_text_refs_url"
    REFS_URL_ONLY = "refs_url_only"
    INVALID_URL_ONLY = "invalid_url_only"
    NO_URL_FOUND = "no_url_found"

    ALL = {
        SOURCE_CANONICAL_URL,
        SOURCE_URL_NEEDS_NORMALIZE,
        SOURCE_TEXT_REFS_URL,
        REFS_URL_ONLY,
        INVALID_URL_ONLY,
        NO_URL_FOUND,
    }


HIT_ORIGIN_BY_CLASS = {
    UrlIdentityClass.SOURCE_CANONICAL_URL: "hit_source",
    UrlIdentityClass.SOURCE_URL_NEEDS_NORMALIZE: "hit_source",
    UrlIdentityClass.SOURCE_TEXT_REFS_URL: "hit_refs",
    UrlIdentityClass.REFS_URL_ONLY: "hit_refs",
    UrlIdentityClass.INVALID_URL_ONLY: "miss_invalid",
    UrlIdentityClass.NO_URL_FOUND: "miss_none",
}


@dataclass
class Inspection:
    path: Path
    title: str
    source_raw: str | None
    refs: list[str]
    source_url: str | None
    canonical_url: str | None
    identity_class: str
    hit_origin: str
    candidate_urls: list[str]
    frontmatter_text: str | None
    body: str
    content: str


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def make_run_id() -> str:
    return f"zhsync-{utc_stamp()}-{uuid.uuid4().hex[:8]}"


def strip_wrapping(value: str | None) -> str:
    if value is None:
        return ""
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1].strip()
    return text


def is_url(value: str | None) -> bool:
    if not value:
        return False
    try:
        parts = urlsplit(strip_wrapping(value))
        return parts.scheme in {"http", "https"} and bool(parts.netloc)
    except Exception:
        return False


def normalize_query(query: str) -> str:
    pairs = []
    for key, val in parse_qsl(query, keep_blank_values=True):
        if key in TRACKING_QUERY_KEYS:
            continue
        pairs.append((key, val))
    if not pairs:
        return ""
    return "&".join(f"{quote(key)}={quote(val)}" for key, val in pairs)


def canonicalize_url(value: str | None) -> str | None:
    if not value:
        return None
    raw = strip_wrapping(value)
    if not raw:
        return None
    try:
        parts = urlsplit(raw)
    except Exception:
        return None
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return None

    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = unquote(parts.path).rstrip("/")

    if host.endswith("zhihu.com"):
        if host == "zhuanlan.zhihu.com":
            match = re.match(r"^/p/(\d+)$", path)
            if match:
                return f"https://zhuanlan.zhihu.com/p/{match.group(1)}"
        question_answer = re.match(r"^/question/(\d+)/answer/(\d+)$", path)
        if question_answer:
            return f"https://www.zhihu.com/question/{question_answer.group(1)}/answer/{question_answer.group(2)}"
        query = normalize_query(parts.query)
        return urlunsplit(("https", f"www.{host}" if host != "www.zhihu.com" else host, path or "/", query, ""))

    query = normalize_query(parts.query)
    canonical_host = "x.com" if host in {"twitter.com", "www.twitter.com"} else host
    return urlunsplit(("https", canonical_host, path or "/", query, ""))


def extract_url_candidates(text: str | None) -> list[str]:
    if not text:
        return []
    return [match.group(0).rstrip(".,)") for match in URL_PATTERN.finditer(text)]


def split_frontmatter(content: str) -> tuple[str | None, str]:
    if not content.startswith("---\n"):
        return None, content
    end = content.find("\n---\n", 4)
    if end == -1:
        return None, content
    return content[4:end], content[end + 5 :]


def parse_top_level_scalar(frontmatter: str | None, key: str) -> str | None:
    if not frontmatter:
        return None
    for line in frontmatter.splitlines():
        match = TOP_LEVEL_KEY_PATTERN.match(line)
        if match and match.group(1) == key:
            return strip_wrapping(match.group(2) or "")
    return None


def parse_top_level_list(frontmatter: str | None, key: str) -> list[str]:
    if not frontmatter:
        return []
    lines = frontmatter.splitlines()
    items: list[str] = []
    in_block = False
    for line in lines:
        if not in_block:
            match = TOP_LEVEL_KEY_PATTERN.match(line)
            if match and match.group(1) == key:
                in_block = True
                inline = strip_wrapping(match.group(2) or "")
                if inline and inline not in {"[]", ""}:
                    items.append(inline)
                continue
        else:
            if line.startswith("  - ") or line.startswith("\t- "):
                items.append(strip_wrapping(line.split("- ", 1)[1]))
                continue
            if line.startswith("    ") or line.startswith("\t\t"):
                continue
            break
    return [item for item in items if item]


def remove_top_level_block(frontmatter: str | None, key: str) -> str:
    if not frontmatter:
        return ""
    lines = frontmatter.splitlines()
    out: list[str] = []
    skip = False
    for line in lines:
        match = TOP_LEVEL_KEY_PATTERN.match(line)
        if match and match.group(1) == key:
            skip = True
            continue
        if skip:
            if line.startswith("  - ") or line.startswith("\t- ") or line.startswith("    ") or line.startswith("\t\t"):
                continue
            skip = False
        if not skip:
            out.append(line)
    return "\n".join(out).strip("\n")


def derive_title(path: Path, title: str | None, source_raw: str | None) -> str:
    if title:
        return strip_wrapping(title)
    if source_raw and not is_url(source_raw):
        return strip_wrapping(source_raw)
    stem = re.sub(r"^\d{8,12}\s+", "", path.stem)
    return stem


def inspect_markdown(path: Path) -> Inspection:
    content = path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(content)
    source_raw = parse_top_level_scalar(frontmatter, "source")
    title = derive_title(path, parse_top_level_scalar(frontmatter, "title"), source_raw)
    refs = parse_top_level_list(frontmatter, "refs")
    source_url = parse_top_level_scalar(frontmatter, "source_url")
    canonical_url = parse_top_level_scalar(frontmatter, "canonical_url")

    candidates: list[str] = []
    for raw in [source_raw, source_url, canonical_url]:
        if raw:
            candidates.extend(extract_url_candidates(raw))
            if is_url(raw):
                candidates.append(strip_wrapping(raw))
    for ref in refs:
        candidates.extend(extract_url_candidates(ref))
        if is_url(ref):
            candidates.append(strip_wrapping(ref))

    deduped_candidates = []
    seen = set()
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            deduped_candidates.append(candidate)

    source_is_url = is_url(source_raw)
    canonical_source = canonicalize_url(source_raw) if source_is_url else None
    refs_canonical = [url for url in (canonicalize_url(ref) for ref in refs) if url]

    if canonical_source:
        source_clean = strip_wrapping(source_raw)
        identity = (
            UrlIdentityClass.SOURCE_CANONICAL_URL
            if canonical_source == source_clean
            else UrlIdentityClass.SOURCE_URL_NEEDS_NORMALIZE
        )
        canonical = canonical_source
    elif source_raw and refs_canonical:
        identity = UrlIdentityClass.SOURCE_TEXT_REFS_URL
        canonical = refs_canonical[0]
    elif refs_canonical:
        identity = UrlIdentityClass.REFS_URL_ONLY
        canonical = refs_canonical[0]
    elif deduped_candidates:
        identity = UrlIdentityClass.INVALID_URL_ONLY
        canonical = None
    else:
        identity = UrlIdentityClass.NO_URL_FOUND
        canonical = None

    return Inspection(
        path=path,
        title=title,
        source_raw=source_raw,
        refs=refs,
        source_url=source_url,
        canonical_url=canonical,
        identity_class=identity,
        hit_origin=HIT_ORIGIN_BY_CLASS[identity],
        candidate_urls=deduped_candidates,
        frontmatter_text=frontmatter,
        body=body,
        content=content,
    )


def rebuild_frontmatter(existing_frontmatter: str | None, source_url: str, title: str, refs: list[str]) -> str:
    remaining = existing_frontmatter or ""
    for key in ["title", "source", "refs", "source_url", "canonical_url"]:
        remaining = remove_top_level_block(remaining, key)
    remaining_lines = [line for line in remaining.splitlines() if line.strip()]

    header_lines = [
        f'title: "{title.replace(chr(34), chr(39))}"',
        f'source: "{source_url}"',
    ]
    unique_refs = []
    seen = set()
    for ref in refs:
        cleaned = strip_wrapping(ref)
        if cleaned and cleaned != source_url and cleaned not in seen:
            seen.add(cleaned)
            unique_refs.append(cleaned)
    if unique_refs:
        header_lines.append("refs:")
        header_lines.extend([f'  - "{ref}"' for ref in unique_refs])

    return "---\n" + "\n".join(header_lines + remaining_lines).strip() + "\n---\n"


def rewrite_clipping_file(path: Path) -> dict[str, Any]:
    inspection = inspect_markdown(path)
    if inspection.identity_class in {UrlIdentityClass.INVALID_URL_ONLY, UrlIdentityClass.NO_URL_FOUND}:
        return {
            "path": str(path),
            "identity_class": inspection.identity_class,
            "changed": False,
            "canonical_url": None,
        }

    assert inspection.canonical_url
    refs = inspection.refs[:]
    if inspection.source_url:
        refs.append(inspection.source_url)

    new_frontmatter = rebuild_frontmatter(
        inspection.frontmatter_text,
        inspection.canonical_url,
        inspection.title,
        refs,
    )
    new_content = new_frontmatter + inspection.body.lstrip("\n")
    changed = new_content != inspection.content
    if changed:
        path.write_text(new_content, encoding="utf-8")
    return {
        "path": str(path),
        "identity_class": inspection.identity_class,
        "changed": changed,
        "canonical_url": inspection.canonical_url,
    }


def collect_markdown_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.md") if path.is_file())


def build_url_index(root: Path) -> dict[str, Any]:
    index: dict[str, Any] = {}
    counts = {key: 0 for key in UrlIdentityClass.ALL}
    files = []
    for path in collect_markdown_files(root):
        inspection = inspect_markdown(path)
        counts[inspection.identity_class] += 1
        record = {
            "path": str(path),
            "identity_class": inspection.identity_class,
            "hit_origin": inspection.hit_origin,
            "canonical_url": inspection.canonical_url,
            "title": inspection.title,
        }
        files.append(record)
        if inspection.canonical_url and inspection.canonical_url not in index:
            index[inspection.canonical_url] = record
    return {"index": index, "counts": counts, "files": files}


def extract_people_token_from_example(markdown_path: Path) -> str | None:
    text = markdown_path.read_text(encoding="utf-8")
    match = re.search(r"/api/v4/people/([^/]+)/collections", text)
    return match.group(1) if match else None

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def atomic_write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def run_root(state_dir: Path, run_id: str) -> Path:
    root = state_dir / "runs" / run_id
    ensure_dir(root)
    return root


def snapshot_paths(snapshot_path: Path, path_map: dict[str, Path]) -> dict[str, Any]:
    snapshot = load_json(snapshot_path, {})
    changed = False
    for key, target in path_map.items():
        if key not in snapshot:
            snapshot[key] = {
                "path": str(target),
                "exists_before": target.exists(),
            }
            changed = True
    if changed:
        atomic_write_json(snapshot_path, snapshot)
    return snapshot


def parse_converter_output(text: str) -> dict[str, Any]:
    payload = json.loads(text)
    required = {"filename", "outputPath", "assetsDir", "imageCount"}
    missing = required - set(payload)
    if missing:
        raise ValueError(f"Missing converter fields: {sorted(missing)}")
    return payload


def build_arg_parser(name: str, description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=name, description=description)
    parser.add_argument("--clip-dir", default="02_Sources/_clippings")
    return parser
