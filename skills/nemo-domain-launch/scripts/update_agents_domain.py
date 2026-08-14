#!/usr/bin/env python3
"""Write a verified production domain to the project-root AGENTS.md exactly once."""

from __future__ import annotations

import argparse
import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any

import validate_launch_report


BEGIN_MARKER = "<!-- nemo-domain-launch:begin -->"
END_MARKER = "<!-- nemo-domain-launch:end -->"
ROUTES = {
    "static_pages": "Spaceship → Cloudflare DNS → Cloudflare Pages",
    "saas_vercel": "Spaceship → Cloudflare DNS → Vercel",
}


def managed_block(origin: str, mode: str) -> str:
    route = ROUTES.get(mode)
    if route is None:
        raise ValueError(f"unsupported deployment mode: {mode}")
    return "\n".join(
        (
            BEGIN_MARKER,
            "## Production deployment",
            "",
            f"- Formal domain: {origin}",
            f"- Deployment mode: `{mode}`",
            f"- Route: {route}",
            END_MARKER,
        )
    )


def merge_agents_content(existing: str, block: str) -> tuple[str, bool]:
    begin_count = existing.count(BEGIN_MARKER)
    end_count = existing.count(END_MARKER)
    if begin_count != end_count or begin_count > 1:
        raise ValueError("AGENTS.md has malformed or duplicate nemo-domain-launch markers")
    if begin_count == 1:
        start = existing.index(BEGIN_MARKER)
        end = existing.index(END_MARKER, start) + len(END_MARKER)
        if existing[start:end] != block:
            raise ValueError("AGENTS.md already contains a different nemo-domain-launch managed block")
        return existing, False

    if not existing:
        return block + "\n", True
    separator = "" if existing.endswith("\n\n") else "\n" if existing.endswith("\n") else "\n\n"
    return existing + separator + block + "\n", True


def atomic_write(path: Path, content: str, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temporary, stat.S_IMODE(mode))
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def prepare_writeback(report_path: Path, payload: dict[str, Any]) -> tuple[Path, str, dict[str, Any], bool]:
    validation = validate_launch_report.validate_report(payload, require_domain_ready=True)
    if not validation["ok"]:
        raise ValueError("domain_ready validation failed: " + "; ".join(validation["failures"]))

    scope = payload["scope"]
    project_dir = Path(scope["project_dir"]).expanduser().resolve()
    if not project_dir.is_dir():
        raise ValueError(f"project_dir does not exist: {project_dir}")
    agents_path = project_dir / "AGENTS.md"
    if agents_path.is_symlink():
        raise ValueError("project-root AGENTS.md must not be a symlink")

    writeback = payload["actions"]["agents_md_writeback"]
    if validate_launch_report.phase_status(writeback, "authorization") != "granted":
        raise ValueError("agents_md_writeback requires granted authorization")
    requested_target = writeback.get("target")
    if not isinstance(requested_target, str) or not Path(requested_target).is_absolute():
        raise ValueError("agents_md_writeback target must be an absolute project-root AGENTS.md path")
    if Path(requested_target).expanduser().resolve() != agents_path:
        raise ValueError("agents_md_writeback target must equal project-root AGENTS.md")

    origin = scope["production_origin"]
    mode = scope["deployment_mode"]
    block = managed_block(origin, mode)
    existed_before = agents_path.exists()
    existing = agents_path.read_text(encoding="utf-8") if existed_before else ""
    merged, changed = merge_agents_content(existing, block)

    updated = json.loads(json.dumps(payload))
    action = updated["actions"]["agents_md_writeback"]
    if action.get("before") is None:
        action["before"] = {
            "file_existed": existed_before,
            "managed_block_present": BEGIN_MARKER in existing,
        }
    action["execution"] = {
        "status": "passed",
        "evidence": {
            "path": str(agents_path),
            "managed_block": "nemo-domain-launch",
            "changed": changed,
        },
    }
    action["readback"] = {
        "status": "passed",
        "evidence": {
            "path": str(agents_path),
            "formal_domain": origin,
            "deployment_mode": mode,
        },
    }
    updated["observations"]["agents_md"] = {
        "status": "passed",
        "path": str(agents_path),
        "managed_block": "nemo-domain-launch",
    }
    updated["claims"]["launch_complete"] = True

    final_validation = validate_launch_report.validate_report(updated, require_launch_complete=True)
    if not final_validation["ok"]:
        raise ValueError("launch_complete validation failed: " + "; ".join(final_validation["failures"]))
    return agents_path, merged, updated, changed


def execute_writeback(report_path: Path) -> dict[str, Any]:
    report_path = report_path.expanduser().resolve()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("launch report must contain a JSON object")
    agents_path, merged, updated, changed = prepare_writeback(report_path, payload)

    previous_mode = agents_path.stat().st_mode if agents_path.exists() else None
    atomic_write(agents_path, merged, previous_mode)
    readback = agents_path.read_text(encoding="utf-8")
    block = managed_block(updated["scope"]["production_origin"], updated["scope"]["deployment_mode"])
    if readback.count(BEGIN_MARKER) != 1 or block not in readback:
        raise RuntimeError("AGENTS.md readback did not contain the exact managed block")

    report_mode = report_path.stat().st_mode
    atomic_write(report_path, json.dumps(updated, ensure_ascii=False, indent=2) + "\n", report_mode)
    return {
        "ok": True,
        "changed": changed,
        "agents_path": str(agents_path),
        "formal_domain": updated["scope"]["production_origin"],
        "deployment_mode": updated["scope"]["deployment_mode"],
        "launch_complete": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="Validated launch-report JSON to update in place.")
    args = parser.parse_args()
    try:
        result = execute_writeback(Path(args.report))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"ok": False, "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
