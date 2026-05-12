from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import uuid
from pathlib import Path
import shutil as which_shutil

from core import (
    build_arg_parser,
    build_url_index,
    canonicalize_url,
    extract_people_token_from_example,
    inspect_markdown,
    parse_converter_output,
    run_root,
    snapshot_paths,
    split_frontmatter,
    utc_stamp,
)


SUPPORTED_TYPES = {"article", "answer"}


def resolve_article_clip_command() -> str:
    for candidate in ["article-clip.cmd", "article-clip"]:
        resolved = which_shutil.which(candidate)
        if resolved:
            return resolved
    raise FileNotFoundError("Could not find article-clip.cmd or article-clip in PATH.")


def run_json_command(command: list[str], cwd: Path) -> dict:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def list_collections(repo_root: Path, people_token: str, interactive_login: bool) -> dict:
    return list_collections_page(repo_root, people_token, 0, 20, interactive_login)


def list_collections_page(repo_root: Path, people_token: str, offset: int, limit: int, interactive_login: bool) -> dict:
    command = [
        "node",
        ".skills/zhihu-collection-sync/scripts/zhihu_browser_api.cjs",
        "list-collections",
        "--people-token",
        people_token,
        "--offset",
        str(offset),
        "--limit",
        str(limit),
    ]
    if interactive_login:
        command.append("--interactive-login")
    return run_json_command(command, repo_root)


def list_items(repo_root: Path, collection_id: str, offset: int, limit: int, interactive_login: bool) -> dict:
    command = [
        "node",
        ".skills/zhihu-collection-sync/scripts/zhihu_browser_api.cjs",
        "list-items",
        "--collection-id",
        collection_id,
        "--offset",
        str(offset),
        "--limit",
        str(limit),
    ]
    if interactive_login:
        command.append("--interactive-login")
    return run_json_command(command, repo_root)


def normalize_converted_output(output_path: Path, canonical_url: str) -> None:
    inspection = inspect_markdown(output_path)
    content = output_path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(content)

    from core import rebuild_frontmatter

    refs = inspection.refs[:]
    if inspection.source_raw and inspection.source_raw != inspection.title:
        refs.append(inspection.source_raw)
    new_frontmatter = rebuild_frontmatter(frontmatter, canonical_url, inspection.title, refs)
    output_path.write_text(new_frontmatter + body.lstrip("\n"), encoding="utf-8")


def find_content_md(temp_root: Path) -> Path:
    matches = list(temp_root.rglob("content.md"))
    if not matches:
        raise FileNotFoundError(f"No content.md found under {temp_root}")
    return matches[0]


def import_one(
    repo_root: Path,
    run_dir: Path,
    item_id: str,
    canonical_url: str,
    clip_dir: Path,
    assets_dir: Path,
) -> dict:
    temp_root = repo_root / ".omx" / "tmp" / "zhihu-collection-sync" / run_dir.name / item_id
    temp_root.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [resolve_article_clip_command(), canonical_url, "--out", str(temp_root), "--verbose"],
        cwd=repo_root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=True,
    )

    content_md = find_content_md(temp_root)
    convert_output = subprocess.run(
        [
            "node",
            ".skills/article-clip-obsidian/convert.js",
            str(content_md),
            str(clip_dir),
            str(assets_dir),
        ],
        cwd=repo_root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=True,
    )

    parsed = parse_converter_output(convert_output.stdout)
    output_path = Path(parsed["outputPath"])
    generated_assets_dir = Path(parsed["assetsDir"])
    snapshot = snapshot_paths(
        run_dir / "pre_run_snapshot.json",
        {"outputPath": output_path, "assetsDir": generated_assets_dir},
    )

    try:
        normalize_converted_output(output_path, canonical_url)
    except Exception:
        if snapshot.get("outputPath", {}).get("exists_before") is False and output_path.exists():
            output_path.unlink()
        if snapshot.get("assetsDir", {}).get("exists_before") is False and generated_assets_dir.exists():
            shutil.rmtree(generated_assets_dir)
        raise

    return {
        "status": "imported",
        "canonical_url": canonical_url,
        "outputPath": str(output_path),
        "assetsDir": str(generated_assets_dir),
        "imageCount": parsed["imageCount"],
    }


def main() -> None:
    parser = build_arg_parser("sync.py", "Sync Zhihu collections into the vault with URL dedupe.")
    parser.add_argument("--all-collections", action="store_true")
    parser.add_argument("--collection-id", action="append", default=[])
    parser.add_argument("--people-url-token", default="")
    parser.add_argument("--request-example-file", default="知乎收藏夹请求示例.md")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--interactive-login", action="store_true")
    parser.add_argument("--summary-out", default="")
    args = parser.parse_args()

    if args.all_collections == bool(args.collection_id):
        raise SystemExit("Provide exactly one of --all-collections or --collection-id.")

    repo_root = Path.cwd()
    clip_dir = (repo_root / args.clip_dir).resolve()
    assets_dir = (repo_root / "assets").resolve()
    run_dir = run_root(repo_root / ".omx" / "tmp" / "zhihu-collection-sync", utc_stamp())

    index_report = build_url_index(clip_dir)
    canonical_index = dict(index_report["index"])

    people_token = args.people_url_token or extract_people_token_from_example(repo_root / args.request_example_file)
    if args.all_collections:
        if not people_token:
            raise RuntimeError("Could not determine people_url_token. Pass --people-url-token explicitly.")
        selected_collections = []
        collections_offset = 0
        collections_end = False
        while not collections_end:
            collections_payload = list_collections_page(
                repo_root,
                people_token,
                collections_offset,
                args.limit,
                args.interactive_login,
            )
            selected_collections.extend([str(item["id"]) for item in collections_payload.get("data", [])])
            collections_paging = collections_payload.get("paging", {})
            collections_end = bool(collections_paging.get("is_end"))
            collections_offset += args.limit
    else:
        selected_collections = [str(value) for value in args.collection_id]

    summary = {
        "run_id": run_dir.name,
        "selected_collections": selected_collections,
        "counts": {
            "existing_source_url_hits": 0,
            "existing_refs_url_hits": 0,
            "unsupported": 0,
            "invalid_url": 0,
            "imported": 0,
            "failed": 0,
        },
        "unsupported_types": {},
        "imports": [],
    }

    for collection_id in selected_collections:
        offset = 0
        is_end = False
        while not is_end:
            items_payload = list_items(repo_root, collection_id, offset, args.limit, args.interactive_login)
            paging = items_payload.get("paging", {})
            for item in items_payload.get("data", []):
                content = item.get("content") or {}
                item_type = content.get("type")
                if item_type not in SUPPORTED_TYPES:
                    key = item_type or "unknown"
                    summary["counts"]["unsupported"] += 1
                    summary["unsupported_types"][key] = summary["unsupported_types"].get(key, 0) + 1
                    continue

                canonical_url = canonicalize_url(content.get("url"))
                if not canonical_url:
                    summary["counts"]["invalid_url"] += 1
                    continue

                existing = canonical_index.get(canonical_url)
                if existing:
                    if existing["hit_origin"] == "hit_source":
                        summary["counts"]["existing_source_url_hits"] += 1
                    else:
                        summary["counts"]["existing_refs_url_hits"] += 1
                    continue

                try:
                    result = import_one(
                        repo_root=repo_root,
                        run_dir=run_dir,
                        item_id=str(content.get("id") or uuid.uuid4().hex),
                        canonical_url=canonical_url,
                        clip_dir=clip_dir,
                        assets_dir=assets_dir,
                    )
                    summary["counts"]["imported"] += 1
                    summary["imports"].append(result)
                    canonical_index[canonical_url] = {
                        "path": result["outputPath"],
                        "identity_class": "source_canonical_url",
                        "hit_origin": "hit_source",
                        "canonical_url": canonical_url,
                    }
                except Exception as error:
                    summary["counts"]["failed"] += 1
                    summary["imports"].append(
                        {
                            "status": "failed",
                            "canonical_url": canonical_url,
                            "error": str(error),
                        }
                    )

            is_end = bool(paging.get("is_end"))
            offset += args.limit

    payload = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.summary_out:
        target = Path(args.summary_out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload, encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
