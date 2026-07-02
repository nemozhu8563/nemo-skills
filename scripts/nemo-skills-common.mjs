import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
export const DEFAULT_REPO_ROOT = path.resolve(SCRIPT_DIR, "..");
export const WARNING =
  "Managed by nemo-skills. Do not edit here; edit the nemo-skills repo and republish.";
const EXCLUDED_DIRECTORY_NAMES = new Set(["node_modules", "__pycache__"]);

export function parseArgs(argv, spec = {}) {
  const out = { entryIds: [] };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = () => {
      if (i + 1 >= argv.length) throw new Error(`Missing value for ${arg}`);
      i += 1;
      return argv[i];
    };

    switch (arg) {
      case "--repo-root":
        out.repoRoot = next();
        break;
      case "--vault-root":
        out.vaultRoot = next();
        break;
      case "--mapping-path":
        out.mappingPath = next();
        break;
      case "--entry-id":
        out.entryIds.push(...splitList(next()));
        break;
      case "--only-migrate-now":
        out.onlyMigrateNow = true;
        break;
      case "--mode":
        out.mode = next();
        break;
      case "--batch-id":
        out.batchId = next();
        break;
      case "--dry-run":
        out.dryRun = true;
        break;
      case "--help":
      case "-h":
        out.help = true;
        break;
      default:
        if (spec.allowBatchPositional && !out.batchId && !arg.startsWith("--")) {
          out.batchId = arg;
          break;
        }
        throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return out;
}

function splitList(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function loadContext(args = {}) {
  const repoRoot = path.resolve(args.repoRoot || DEFAULT_REPO_ROOT);
  const mappingPath = path.resolve(
    args.mappingPath || path.join(repoRoot, "docs", "mapping.json"),
  );
  const mapping = readJson(mappingPath);
  const vaultRoot = resolveVaultRoot(args.vaultRoot, mapping, repoRoot);

  return { repoRoot, mappingPath, mapping, vaultRoot };
}

function resolveVaultRoot(cliVaultRoot, mapping, repoRoot) {
  if (cliVaultRoot) return path.resolve(cliVaultRoot);
  throw new Error("Missing required --vault-root <path>.");
}

export function selectEntries(mapping, entryIds = [], onlyMigrateNow = false) {
  const wanted = new Set(entryIds);
  let entries = Array.isArray(mapping.entries) ? mapping.entries : [];
  if (onlyMigrateNow) entries = entries.filter((entry) => entry.status === "migrate_now");
  if (wanted.size > 0) entries = entries.filter((entry) => wanted.has(entry.id));
  return entries;
}

export function getMetaPaths(destinationPath, type) {
  if (type === "skill_dir") {
    return {
      marker: path.join(destinationPath, ".nemo-managed.json"),
      manifest: path.join(destinationPath, ".nemo-manifest.json"),
      markerRelative: ".nemo-managed.json",
      manifestRelative: ".nemo-manifest.json",
    };
  }

  return {
    marker: `${destinationPath}.nemo-managed.json`,
    manifest: `${destinationPath}.nemo-manifest.json`,
    markerRelative: path.basename(`${destinationPath}.nemo-managed.json`),
    manifestRelative: path.basename(`${destinationPath}.nemo-manifest.json`),
  };
}

export function getManagedState(entry, destinationPath) {
  const meta = getMetaPaths(destinationPath, entry.type);
  const targetExists = fs.existsSync(destinationPath);
  const markerExists = fs.existsSync(meta.marker);
  const manifestExists = fs.existsSync(meta.manifest);

  if (!targetExists) return { state: "missing", meta };
  if (!markerExists || !manifestExists) return { state: "unmanaged", meta };

  const marker = readJson(meta.marker);
  const managed = marker.managed_by === "nemo-skills" && marker.entry_id === entry.id;
  if (!managed) return { state: "unmanaged", meta, marker };

  return { state: "managed", meta, marker };
}

export function getManifestData(targetPath, type, excludeRelativePaths = []) {
  const exclude = new Set(excludeRelativePaths);
  const files = [];

  if (type === "skill_dir") {
    if (!isDirectory(targetPath)) throw new Error(`Directory not found: ${targetPath}`);
    for (const file of walkFiles(targetPath)) {
      const relative = toRelativePath(targetPath, file);
      if (!exclude.has(relative)) {
        files.push({ path: relative, sha256: sha256File(file) });
      }
    }
  } else {
    if (!isFile(targetPath)) throw new Error(`File not found: ${targetPath}`);
    const name = path.basename(targetPath);
    if (!exclude.has(name)) {
      files.push({ path: name, sha256: sha256File(targetPath) });
    }
  }

  files.sort((a, b) => ordinalCompare(a.path, b.path));
  return {
    generated_at: new Date().toISOString(),
    files,
    file_count: files.length,
  };
}

export function compareManifest(expected, actual) {
  const issues = [];

  if (expected.file_count !== actual.file_count) {
    issues.push(`file_count mismatch expected=${expected.file_count} actual=${actual.file_count}`);
  }

  const expectedPaths = expected.files.map((file) => file.path);
  const actualPaths = actual.files.map((file) => file.path);
  if (
    expectedPaths.length !== actualPaths.length ||
    expectedPaths.some((item, index) => item !== actualPaths[index])
  ) {
    issues.push("path set mismatch");
  }

  const actualMap = new Map(actual.files.map((file) => [file.path, file.sha256]));
  for (const file of expected.files) {
    if (!actualMap.has(file.path)) {
      issues.push(`missing file: ${file.path}`);
      continue;
    }
    if (actualMap.get(file.path) !== file.sha256) {
      issues.push(`hash mismatch: ${file.path}`);
    }
  }

  return { clean: issues.length === 0, issues };
}

export function testEntryDrift(entry, repoRoot, vaultRoot) {
  const sourcePath = path.join(repoRoot, entry.source);
  const destinationPath = path.join(vaultRoot, entry.destination);
  const managedState = getManagedState(entry, destinationPath);

  if (managedState.state !== "managed") {
    return {
      clean: false,
      reason: managedState.state,
      issues: [`destination state is ${managedState.state}`],
    };
  }

  const expected = getManifestData(sourcePath, entry.type);
  const actual =
    entry.type === "skill_dir"
      ? getManifestData(destinationPath, entry.type, [
          managedState.meta.markerRelative,
          managedState.meta.manifestRelative,
        ])
      : getManifestData(destinationPath, entry.type);
  const comparison = compareManifest(expected, actual);

  return {
    clean: comparison.clean,
    reason: comparison.clean ? "clean" : "drift",
    issues: comparison.issues,
    expected,
    actual,
    meta: managedState.meta,
  };
}

export function newManagedMarker(entry, batchId, manifestFileName) {
  return {
    managed_by: "nemo-skills",
    entry_id: entry.id,
    type: entry.type,
    source: entry.source,
    published_at: new Date().toISOString(),
    batch: batchId,
    manifest_file: manifestFileName,
    warning: WARNING,
  };
}

export function ensureParent(targetPath) {
  fs.mkdirSync(path.dirname(targetPath), { recursive: true });
}

export function copyRecursive(source, destination) {
  const stat = fs.statSync(source);
  if (stat.isDirectory()) {
    fs.mkdirSync(destination, { recursive: true });
    for (const item of fs.readdirSync(source)) {
      if (EXCLUDED_DIRECTORY_NAMES.has(item)) continue;
      copyRecursive(path.join(source, item), path.join(destination, item));
    }
    return;
  }
  ensureParent(destination);
  fs.copyFileSync(source, destination);
}

export function removePath(targetPath) {
  if (fs.existsSync(targetPath)) fs.rmSync(targetPath, { recursive: true, force: true });
}

export function movePath(source, destination) {
  ensureParent(destination);
  removePath(destination);
  fs.renameSync(source, destination);
}

export function writeJson(targetPath, data) {
  ensureParent(targetPath);
  fs.writeFileSync(targetPath, `${JSON.stringify(data, null, 2)}\n`, "utf8");
}

export function readJson(targetPath) {
  return JSON.parse(fs.readFileSync(targetPath, "utf8").replace(/^\uFEFF/, ""));
}

export function batchIdNow() {
  const iso = new Date().toISOString();
  return iso.replaceAll("-", "").replaceAll(":", "").replace(/\.\d{3}Z$/, "Z");
}

export function printJson(data) {
  process.stdout.write(`${JSON.stringify(data, null, 2)}\n`);
}

export function fail(message) {
  process.stderr.write(`${message}\n`);
  process.exit(1);
}

function walkFiles(root) {
  const results = [];
  for (const item of fs.readdirSync(root, { withFileTypes: true })) {
    if (item.isDirectory() && EXCLUDED_DIRECTORY_NAMES.has(item.name)) continue;

    const fullPath = path.join(root, item.name);
    if (item.isDirectory()) {
      results.push(...walkFiles(fullPath));
    } else if (item.isFile()) {
      results.push(fullPath);
    }
  }
  return results;
}

function toRelativePath(root, file) {
  return path.relative(root, file).split(path.sep).join("/");
}

function sha256File(file) {
  return createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function isDirectory(targetPath) {
  try {
    return fs.statSync(targetPath).isDirectory();
  } catch {
    return false;
  }
}

function isFile(targetPath) {
  try {
    return fs.statSync(targetPath).isFile();
  } catch {
    return false;
  }
}

function ordinalCompare(a, b) {
  if (a < b) return -1;
  if (a > b) return 1;
  return 0;
}
