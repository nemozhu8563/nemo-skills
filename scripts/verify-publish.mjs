#!/usr/bin/env node
import path from "node:path";
import {
  fail,
  getManagedState,
  loadContext,
  parseArgs,
  printJson,
  selectEntries,
  testEntryDrift,
} from "./nemo-skills-common.mjs";

main().catch((error) => fail(error.stack || error.message));

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    printHelp();
    return;
  }

  const { repoRoot, mapping, vaultRoot } = loadContext(args);
  const entries = selectEntries(mapping, args.entryIds, args.onlyMigrateNow);
  if (entries.length === 0) throw new Error("No entries selected for verification.");

  const results = [];
  let failed = false;

  for (const entry of entries) {
    const destinationPath = path.join(vaultRoot, entry.destination);
    const managedState = getManagedState(entry, destinationPath);

    if (managedState.state !== "managed") {
      failed = true;
      results.push({
        entry_id: entry.id,
        status: "missing_or_unmanaged",
        issues: [`destination state is ${managedState.state}`],
      });
      continue;
    }

    const drift = testEntryDrift(entry, repoRoot, vaultRoot);
    if (!drift.clean) {
      failed = true;
      results.push({ entry_id: entry.id, status: "drift", issues: drift.issues });
      continue;
    }

    results.push({ entry_id: entry.id, status: "clean", issues: [] });
  }

  printJson(results);
  if (failed) process.exit(1);
}

function printHelp() {
  process.stdout.write(`Usage: node scripts/verify-publish.mjs [options]

Options:
  --repo-root <path>       Source repo root (default: parent of scripts/)
  --vault-root <path>      Obsidian vault root
  --mapping-path <path>    Mapping JSON path (default: <repo>/docs/mapping.json)
  --entry-id <id[,id]>     Verify selected entry ids; repeatable
  --only-migrate-now       Select all migrate_now entries
  --help                   Show this help
`);
}
