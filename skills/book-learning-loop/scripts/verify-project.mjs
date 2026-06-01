#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 2) {
  args.set(process.argv[i], process.argv[i + 1]);
}

const vault = path.resolve(args.get("--vault") || process.cwd());
const book = args.get("--book");

if (!book) {
  console.error("Usage: node scripts/verify-project.mjs --vault <vault-root> --book <book-title>");
  process.exit(2);
}

const required = [
  `02_Sources/_books/${book}/book.md`,
  `02_Sources/_books/${book}/manifest.json`,
  `02_Sources/_books/${book}/source`,
  `02_Sources/_intake/books/${book}/course-map.md`,
  `02_Sources/_intake/books/${book}/lessons`,
  `04_Projects/学习/${book}/${book}.md`,
  `04_Projects/学习/${book}/initialization.md`,
  `04_Projects/学习/${book}/learner_profile.md`,
  `04_Projects/学习/${book}/role_interview.md`,
  `04_Projects/学习/${book}/role_contract.md`,
  `04_Projects/学习/${book}/teaching_decisions.md`,
  `04_Projects/学习/${book}/curriculum.md`,
  `04_Projects/学习/${book}/progress.md`,
  `04_Projects/学习/${book}/review_queue.md`,
  `04_Projects/学习/${book}/application_log.md`,
  `04_Projects/学习/${book}/sessions`,
  `04_Projects/学习/${book}/roles`,
];

const missing = required.filter((rel) => !fs.existsSync(path.join(vault, rel)));

const result = {
  ok: missing.length === 0,
  vault,
  book,
  checked: required.length,
  missing,
};

console.log(JSON.stringify(result, null, 2));
process.exit(result.ok ? 0 : 1);
