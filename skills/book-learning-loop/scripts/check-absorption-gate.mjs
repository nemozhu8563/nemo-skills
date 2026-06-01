#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 2) {
  args.set(process.argv[i], process.argv[i + 1]);
}

const vault = path.resolve(args.get("--vault") || process.cwd());
const sessionArg = args.get("--session");

if (!sessionArg) {
  console.error("Usage: node scripts/check-absorption-gate.mjs --vault <vault-root> --session <session-md>");
  process.exit(2);
}

const sessionPath = path.isAbsolute(sessionArg) ? sessionArg : path.join(vault, sessionArg);
const text = fs.readFileSync(sessionPath, "utf8");
const issues = [];

if (!/^status:\s*completed\b/m.test(text)) {
  issues.push("session frontmatter is not status: completed");
}

if (!/Feynman Summary|费曼复述/.test(text)) {
  issues.push("missing Feynman summary section");
}

if (!/学习者费曼复述|Learner Feynman|User Feynman/.test(text)) {
  issues.push("missing learner's own Feynman summary");
}

if (!/老师判定|Coach Diagnosis|Teacher Diagnosis/.test(text)) {
  issues.push("missing teacher/coach diagnosis of the Feynman summary");
}

const noteLinks = [...text.matchAll(/\[\[(03_Notes\/[^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]/g)].map((m) => m[1]);
if (noteLinks.length === 0) {
  issues.push("missing promoted 03_Notes link");
}

for (const link of noteLinks) {
  const notePath = path.join(vault, `${link}.md`);
  if (!fs.existsSync(notePath)) {
    issues.push(`promoted note does not exist: ${link}.md`);
  }
}

const result = {
  ok: issues.length === 0,
  session: path.relative(vault, sessionPath),
  promoted_notes: noteLinks,
  issues,
};

console.log(JSON.stringify(result, null, 2));
process.exit(result.ok ? 0 : 1);
