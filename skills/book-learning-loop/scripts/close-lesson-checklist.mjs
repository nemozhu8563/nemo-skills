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
  console.error("Usage: node scripts/close-lesson-checklist.mjs --vault <vault-root> --session <session-md>");
  process.exit(2);
}

const sessionPath = path.isAbsolute(sessionArg) ? sessionArg : path.join(vault, sessionArg);
const text = fs.readFileSync(sessionPath, "utf8");
const projectDir = path.dirname(path.dirname(sessionPath));
const progressPath = path.join(projectDir, "progress.md");
const reviewPath = path.join(projectDir, "review_queue.md");
const applicationPath = path.join(projectDir, "application_log.md");
const promotedLinks = [...text.matchAll(/\[\[(03_Notes\/[^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]/g)].map((m) => m[1]);

function fileContainsAny(file, needles) {
  if (!fs.existsSync(file)) return false;
  const content = fs.readFileSync(file, "utf8");
  return needles.length === 0 ? false : needles.some((needle) => content.includes(needle));
}

const checks = [
  ["Session status is completed", /^status:\s*completed\b/m.test(text)],
  ["Final checkpoint exists", /## Final Checkpoint/.test(text)],
  ["Feynman summary exists", /Feynman Summary|费曼复述/.test(text)],
  ["Teacher diagnosis exists", /老师判定|Coach Diagnosis|Teacher Diagnosis/.test(text)],
  ["03_Notes promoted link exists when absorbed", promotedLinks.length > 0],
  ["progress.md references the absorbed result", fileContainsAny(progressPath, promotedLinks)],
  ["review_queue.md references the absorbed result or remaining practice", fileContainsAny(reviewPath, promotedLinks)],
  ["application_log.md references the absorbed result", fileContainsAny(applicationPath, promotedLinks)],
];

console.log(`# Close Lesson Checklist\n`);
console.log(`Session: ${path.relative(vault, sessionPath)}\n`);
for (const [label, ok] of checks) {
  console.log(`- [${ok ? "x" : " "}] ${label}`);
}
console.log(`- [ ] next lesson opens with review_queue before new content`);
