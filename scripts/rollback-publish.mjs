#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import {
  ensureParent,
  fail,
  getMetaPaths,
  loadContext,
  movePath,
  parseArgs,
  printJson,
  removePath,
  selectEntries,
} from "./nemo-skills-common.mjs";

main().catch((error) => fail(error.stack || error.message));

async function main() {
  const args = parseArgs(process.argv.slice(2), { allowBatchPositional: true });
  if (args.help) {
    printHelp();
    return;
  }
  if (!args.batchId) throw new Error("Rollback requires --batch-id <id>.");

  const { mapping, vaultRoot } = loadContext(args);
  const entries = selectEntries(mapping, args.entryIds, false);
  if (entries.length === 0) throw new Error("No entries selected for rollback.");

  const backupRoot = path.join(vaultRoot, ".agents", ".nemo-backups", "skills", args.batchId);
  if (!fs.existsSync(backupRoot)) throw new Error(`Backup batch not found: ${backupRoot}`);

  const missingBackups = [];
  for (const entry of entries) {
    const destinationPath = path.join(vaultRoot, entry.destination);
    const backupPath =
      entry.type === "skill_dir"
        ? path.join(backupRoot, entry.destination)
        : path.join(backupRoot, "files", path.basename(destinationPath));
    if (!fs.existsSync(backupPath)) {
      missingBackups.push(`${entry.id}: ${backupPath}`);
    }
  }
  if (missingBackups.length > 0) {
    throw new Error(`Rollback preflight failed; missing backups: ${missingBackups.join("; ")}`);
  }

  const results = [];
  for (const entry of entries) {
    const destinationPath = path.join(vaultRoot, entry.destination);
    const meta = getMetaPaths(destinationPath, entry.type);

    for (const targetPath of [destinationPath, meta.marker, meta.manifest]) {
      removePath(targetPath);
    }

    if (entry.type === "skill_dir") {
      const backupPath = path.join(backupRoot, entry.destination);
      ensureParent(destinationPath);
      movePath(backupPath, destinationPath);
    } else {
      const backupFile = path.join(backupRoot, "files", path.basename(destinationPath));
      ensureParent(destinationPath);
      movePath(backupFile, destinationPath);

      const backupMarker = path.join(backupRoot, "files", path.basename(meta.marker));
      const backupManifest = path.join(backupRoot, "files", path.basename(meta.manifest));
      if (fs.existsSync(backupMarker)) movePath(backupMarker, meta.marker);
      if (fs.existsSync(backupManifest)) movePath(backupManifest, meta.manifest);
    }

    results.push({ entry_id: entry.id, restored: fs.existsSync(destinationPath) });
  }

  printJson(results);
}

function printHelp() {
  process.stdout.write(`Usage: node scripts/rollback-publish.mjs --batch-id <id> [options]

Options:
  --batch-id <id>          Backup batch id to restore
  --repo-root <path>       Source repo root (default: parent of scripts/)
  --vault-root <path>      Obsidian vault root (required)
  --mapping-path <path>    Mapping JSON path (default: <repo>/docs/mapping.json)
  --entry-id <id[,id]>     Roll back selected entry ids; repeatable
  --help                   Show this help
`);
}
