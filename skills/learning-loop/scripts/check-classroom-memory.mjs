#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 2) {
  args.set(process.argv[i], process.argv[i + 1]);
}

const vault = path.resolve(args.get("--vault") || process.cwd());
const bookTitle = args.get("--book-title") || args.get("--book");
const sessionArg = args.get("--session");

if (!bookTitle) {
  console.error("Usage: node scripts/check-classroom-memory.mjs --vault <vault-root> --book-title <book-title> [--session <session-md>]");
  process.exit(2);
}

const memoryPath = path.join(vault, "04_Projects", "学习", bookTitle, "classroom_memory.md");
const issues = [];

if (!fs.existsSync(memoryPath)) {
  issues.push("classroom_memory.md is missing");
} else {
  const text = fs.readFileSync(memoryPath, "utf8");
  const required = [
    ["Teacher Memory", /##\s*Teacher Memory/i],
    ["Classmate Memory", /##\s*Classmate Memory/i],
    ["Shared Classroom Memory", /##\s*Shared Classroom Memory/i],
    ["Last Updated", /##\s*Last Updated/i],
  ];

  for (const [label, pattern] of required) {
    if (!pattern.test(text)) issues.push(`missing section: ${label}`);
  }

  if (sessionArg) {
    const sessionPath = path.isAbsolute(sessionArg) ? sessionArg : path.join(vault, sessionArg);
    const sessionName = path.basename(sessionPath, path.extname(sessionPath));
    const sessionText = fs.existsSync(sessionPath) ? fs.readFileSync(sessionPath, "utf8") : "";
    const lessonMatch = sessionText.match(/\bLesson\s*0*(\d+)\b/i) || sessionText.match(/\blesson-0*(\d+)\b/i);
    const lessonNumber = lessonMatch ? Number(lessonMatch[1]) : null;
    const hasSession = text.includes(sessionName);
    const hasLesson = lessonNumber ? new RegExp(`Lesson\\s*0*${lessonNumber}\\b`, "i").test(text) : false;
    if (!hasSession && !hasLesson) {
      issues.push(`memory does not reference session or lesson: ${sessionName}`);
    }
  }
}

const result = {
  ok: issues.length === 0,
  path: path.relative(vault, memoryPath),
  issues,
};

console.log(JSON.stringify(result, null, 2));
process.exit(result.ok ? 0 : 1);
