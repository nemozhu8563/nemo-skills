#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import {
  batchIdNow,
  compareManifest,
  copyRecursive,
  ensureParent,
  fail,
  getManagedState,
  getManifestData,
  getMetaPaths,
  loadContext,
  movePath,
  newManagedMarker,
  parseArgs,
  printJson,
  removePath,
  selectEntries,
  testEntryDrift,
  writeJson,
} from "./nemo-skills-common.mjs";

const MODES = new Set([
  "FailOnConflict",
  "OverwriteManagedClean",
  "ForceManagedDrift",
  "ForceUnmanaged",
]);

main().catch((error) => fail(error.stack || error.message));

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    printHelp();
    return;
  }

  const mode = args.mode || "FailOnConflict";
  if (!MODES.has(mode)) {
    throw new Error(`Unsupported --mode ${mode}`);
  }

  const { repoRoot, mapping, vaultRoot } = loadContext(args);
  const batchId = args.batchId || batchIdNow();
  const entries = selectEntries(mapping, args.entryIds, args.onlyMigrateNow);

  if (entries.length === 0) throw new Error("No entries selected for publish.");

  const blocked = entries.filter((entry) => entry.status !== "migrate_now");
  if (blocked.length > 0) {
    throw new Error(
      `Refusing to publish non-migrate_now entries: ${blocked
        .map((entry) => `${entry.id}:${entry.status}`)
        .join(", ")}`,
    );
  }

  const backupRoot = path.join(vaultRoot, ".agents", ".nemo-backups", "skills", batchId);
  const results = [];

  for (const entry of entries) {
    const sourcePath = path.join(repoRoot, entry.source);
    const destinationPath = path.join(vaultRoot, entry.destination);
    ensureParent(destinationPath);

    const managedState = getManagedState(entry, destinationPath);
    if (managedState.state === "managed") {
      managedState.drift = testEntryDrift(entry, repoRoot, vaultRoot);
    }

    const skipReason = getSkipReason(entry, managedState, mode);
    if (skipReason) {
      results.push({
        entry_id: entry.id,
        destination: entry.destination,
        state_before: managedState.state,
        mode,
        batch: batchId,
        dry_run: Boolean(args.dryRun),
        skipped: skipReason,
      });
      continue;
    }

    if (args.dryRun) {
      results.push({
        entry_id: entry.id,
        destination: entry.destination,
        state_before: managedState.state,
        mode,
        batch: batchId,
        dry_run: true,
      });
      continue;
    }

    publishEntry(entry, sourcePath, destinationPath, backupRoot, batchId);

    results.push({
      entry_id: entry.id,
      destination: entry.destination,
      state_before: managedState.state,
      mode,
      batch: batchId,
      dry_run: false,
    });
  }

  printJson(results);
}

function getSkipReason(entry, managedState, mode) {
  switch (managedState.state) {
    case "missing":
      return null;
    case "unmanaged":
      if (mode !== "ForceUnmanaged") {
        throw new Error(
          `Unmanaged target exists for ${entry.id}. Re-run with --mode ForceUnmanaged after review.`,
        );
      }
      return null;
    case "managed":
      if (managedState.drift.clean) {
        if (mode === "FailOnConflict") return "managed_clean_noop";
        if (mode !== "OverwriteManagedClean") {
          throw new Error(
            `Managed clean target exists for ${entry.id}. Re-run with --mode OverwriteManagedClean to replace it.`,
          );
        }
        return null;
      }
      if (mode !== "ForceManagedDrift") {
        throw new Error(
          `Managed drift detected for ${entry.id}. Re-run with --mode ForceManagedDrift after review.`,
        );
      }
      return null;
    default:
      throw new Error(`Unsupported target state for ${entry.id}: ${managedState.state}`);
  }
}

function publishEntry(entry, sourcePath, destinationPath, backupRoot, batchId) {
  const destinationParent = path.dirname(destinationPath);
  const stageLeaf = `.nemo-stage-${entry.id}-${batchId}`;

  if (entry.type === "skill_dir") {
    publishSkillDir(entry, sourcePath, destinationPath, destinationParent, stageLeaf, backupRoot, batchId);
  } else if (entry.type === "prompt_file") {
    publishPromptFile(entry, sourcePath, destinationPath, destinationParent, stageLeaf, backupRoot, batchId);
  } else {
    throw new Error(`Unsupported entry type for ${entry.id}: ${entry.type}`);
  }
}

function publishSkillDir(entry, sourcePath, destinationPath, destinationParent, stageLeaf, backupRoot, batchId) {
  const stagePath = path.join(destinationParent, stageLeaf);
  removePath(stagePath);
  copyRecursive(sourcePath, stagePath);

  const stageMeta = getMetaPaths(stagePath, entry.type);
  const manifest = getManifestData(sourcePath, entry.type);
  const marker = newManagedMarker(entry, batchId, stageMeta.manifestRelative);
  writeJson(stageMeta.marker, marker);
  writeJson(stageMeta.manifest, manifest);

  const stageActual = getManifestData(stagePath, entry.type, [
    stageMeta.markerRelative,
    stageMeta.manifestRelative,
  ]);
  const stageComparison = compareManifest(manifest, stageActual);
  if (!stageComparison.clean) {
    throw new Error(`Stage verification failed for ${entry.id}: ${stageComparison.issues.join("; ")}`);
  }

  backupExisting(entry, destinationPath, backupRoot);
  movePath(stagePath, destinationPath);
}

function publishPromptFile(entry, sourcePath, destinationPath, destinationParent, stageLeaf, backupRoot, batchId) {
  const stageDir = path.join(destinationParent, stageLeaf);
  removePath(stageDir);
  fs.mkdirSync(stageDir, { recursive: true });

  const stageFile = path.join(stageDir, path.basename(destinationPath));
  copyRecursive(sourcePath, stageFile);

  const stageMeta = getMetaPaths(stageFile, entry.type);
  const manifest = getManifestData(sourcePath, entry.type);
  const marker = newManagedMarker(entry, batchId, path.basename(stageMeta.manifest));
  writeJson(stageMeta.marker, marker);
  writeJson(stageMeta.manifest, manifest);

  backupExisting(entry, destinationPath, backupRoot);
  movePath(stageFile, destinationPath);
  movePath(stageMeta.marker, `${destinationPath}.nemo-managed.json`);
  movePath(stageMeta.manifest, `${destinationPath}.nemo-manifest.json`);
  removePath(stageDir);
}

function backupExisting(entry, destinationPath, backupRoot) {
  const meta = getMetaPaths(destinationPath, entry.type);

  if (entry.type === "skill_dir") {
    if (fs.existsSync(destinationPath)) {
      movePath(destinationPath, path.join(backupRoot, entry.destination));
    }
    for (const metaPath of [meta.marker, meta.manifest]) {
      if (fs.existsSync(metaPath)) {
        movePath(metaPath, path.join(backupRoot, path.relative(path.dirname(backupRoot), metaPath)));
      }
    }
    return;
  }

  if (fs.existsSync(destinationPath)) {
    movePath(destinationPath, path.join(backupRoot, "files", path.basename(destinationPath)));
  }
  for (const metaPath of [meta.marker, meta.manifest]) {
    if (fs.existsSync(metaPath)) {
      movePath(metaPath, path.join(backupRoot, "files", path.basename(metaPath)));
    }
  }
}

function printHelp() {
  process.stdout.write(`Usage: node scripts/publish-to-vault.mjs [options]

Options:
  --repo-root <path>       Source repo root (default: parent of scripts/)
  --vault-root <path>      Obsidian vault root (required)
  --mapping-path <path>    Mapping JSON path (default: <repo>/docs/mapping.json)
  --entry-id <id[,id]>     Publish selected entry ids; repeatable
  --only-migrate-now       Select all migrate_now entries
  --mode <mode>            FailOnConflict | OverwriteManagedClean | ForceManagedDrift | ForceUnmanaged
  --batch-id <id>          Backup batch id
  --dry-run                Show selected actions without writing
  --help                   Show this help
`);
}
