#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 2) {
  args.set(process.argv[i], process.argv[i + 1]);
}

const vault = path.resolve(args.get("--vault") || process.cwd());
const sessionArg = args.get("--session");
const nextSessionArg = args.get("--next-session");
const strict = args.has("--strict");

if (!sessionArg) {
  console.error("Usage: node scripts/close-lesson-checklist.mjs --vault <vault-root> --session <session-md> [--next-session <session-md>] [--strict]");
  process.exit(2);
}

const sessionPath = path.isAbsolute(sessionArg) ? sessionArg : path.join(vault, sessionArg);
const text = fs.readFileSync(sessionPath, "utf8");
const projectDir = path.dirname(path.dirname(sessionPath));
const progressPath = path.join(projectDir, "progress.md");
const reviewPath = path.join(projectDir, "review_queue.md");
const applicationPath = path.join(projectDir, "application_log.md");
const promotedLinks = [...text.matchAll(/\[\[(03_Notes\/[^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]/g)].map((m) => m[1]);
const lessonNumber = extractLessonNumber(text);

function fileContainsAny(file, needles) {
  if (!fs.existsSync(file)) return false;
  const content = fs.readFileSync(file, "utf8");
  return needles.length === 0 ? false : needles.some((needle) => content.includes(needle));
}

function extractLessonNumber(content) {
  const match = content.match(/\bLesson\s*0*(\d+)\b/i) || content.match(/\blesson-0*(\d+)\b/i);
  return match ? Number(match[1]) : null;
}

function reviewQueueHasCloseout(file, noteLinks, currentLessonNumber) {
  if (!fs.existsSync(file)) return false;
  const content = fs.readFileSync(file, "utf8");
  if (noteLinks.length > 0 && noteLinks.some((link) => content.includes(link))) return true;

  if (!currentLessonNumber) return false;
  const lessonPattern = new RegExp(`Lesson\\s*0*${currentLessonNumber}\\b[^\\n]*(待练习|卡点|复习|回炉|预备|remaining practice|review)`, "i");
  return lessonPattern.test(content);
}

function nextSessionStartsWithReview(sessionFile) {
  const content = fs.readFileSync(sessionFile, "utf8");
  const reviewIndex = content.search(/##\s*(Review Queue Recovery|课前复习|复习恢复|Review)/i);
  if (reviewIndex === -1) return false;

  const firstClassroomContent = content.search(/##\s*(Classroom Opening|Current Question|User Answer|Coach Diagnosis|课堂开场|当前问题)/i);
  return firstClassroomContent === -1 || reviewIndex < firstClassroomContent;
}

const checks = [
  ["Session status is completed", /^status:\s*completed\b/m.test(text)],
  ["Final checkpoint exists", /## Final Checkpoint/.test(text)],
  ["Feynman summary exists", /Feynman Summary|费曼复述/.test(text)],
  ["Teacher diagnosis exists", /老师判定|Coach Diagnosis|Teacher Diagnosis/.test(text)],
  ["03_Notes promoted link exists when absorbed", promotedLinks.length > 0],
  ["progress.md references the absorbed result", fileContainsAny(progressPath, promotedLinks)],
  ["review_queue.md references promoted notes or lesson-specific remaining practice", reviewQueueHasCloseout(reviewPath, promotedLinks, lessonNumber)],
  ["application_log.md references the absorbed result", fileContainsAny(applicationPath, promotedLinks)],
];

console.log(`# Close Lesson Checklist\n`);
console.log(`Session: ${path.relative(vault, sessionPath)}\n`);
for (const [label, ok] of checks) {
  console.log(`- [${ok ? "x" : " "}] ${label}`);
}

let optionalOk = null;
if (nextSessionArg) {
  const nextSessionPath = path.isAbsolute(nextSessionArg) ? nextSessionArg : path.join(vault, nextSessionArg);
  optionalOk = nextSessionStartsWithReview(nextSessionPath);
  console.log(`- [${optionalOk ? "x" : " "}] next session opens with review_queue before classroom content`);
  console.log(`  Next session: ${path.relative(vault, nextSessionPath)}`);
} else {
  console.log(`- [-] next session review_queue opening not checked; pass --next-session <session-md> after the next lesson file exists`);
}

const requiredOk = checks.every(([, ok]) => ok);
if (strict && (!requiredOk || optionalOk === false)) {
  process.exit(1);
}
