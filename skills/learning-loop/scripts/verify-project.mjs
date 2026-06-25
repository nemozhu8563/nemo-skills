#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 2) {
  args.set(process.argv[i], process.argv[i + 1]);
}

const vault = path.resolve(args.get("--vault") || process.cwd());
const legacyBook = args.get("--book");
const bookTitle = args.get("--book-title") || legacyBook;
const bookSlug = args.get("--book-slug") || legacyBook || bookTitle;

if (!bookTitle || !bookSlug) {
  console.error("Usage: node scripts/verify-project.mjs --vault <vault-root> --book-title <book-title> [--book-slug <book-slug>]");
  console.error("Compat: --book <book-title-or-slug> is still accepted when title and slug are the same.");
  process.exit(2);
}

const required = [
  `02_Sources/_books/${bookSlug}/book.md`,
  `02_Sources/_books/${bookSlug}/manifest.json`,
  `02_Sources/_books/${bookSlug}/source`,
  `02_Sources/_intake/books/${bookSlug}/course-map.md`,
  `02_Sources/_intake/books/${bookSlug}/lessons`,
  `04_Projects/学习/${bookTitle}/${bookTitle}.md`,
  `04_Projects/学习/${bookTitle}/initialization.md`,
  `04_Projects/学习/${bookTitle}/learner_profile.md`,
  `04_Projects/学习/${bookTitle}/role_interview.md`,
  `04_Projects/学习/${bookTitle}/role_contract.md`,
  `04_Projects/学习/${bookTitle}/teaching_decisions.md`,
  `04_Projects/学习/${bookTitle}/curriculum.md`,
  `04_Projects/学习/${bookTitle}/progress.md`,
  `04_Projects/学习/${bookTitle}/review_queue.md`,
  `04_Projects/学习/${bookTitle}/application_log.md`,
  `04_Projects/学习/${bookTitle}/classroom_memory.md`,
  `04_Projects/学习/${bookTitle}/sessions`,
  `04_Projects/学习/${bookTitle}/roles`,
];

const missing = required.filter((rel) => !fs.existsSync(path.join(vault, rel)));

const result = {
  ok: missing.length === 0,
  vault,
  book_title: bookTitle,
  book_slug: bookSlug,
  checked: required.length,
  missing,
};

console.log(JSON.stringify(result, null, 2));
process.exit(result.ok ? 0 : 1);
