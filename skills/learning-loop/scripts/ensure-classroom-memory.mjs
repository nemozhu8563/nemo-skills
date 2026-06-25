#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 2) {
  args.set(process.argv[i], process.argv[i + 1]);
}

const vault = path.resolve(args.get("--vault") || process.cwd());
const bookTitle = args.get("--book-title") || args.get("--book");

if (!bookTitle) {
  console.error("Usage: node scripts/ensure-classroom-memory.mjs --vault <vault-root> --book-title <book-title>");
  process.exit(2);
}

const projectDir = path.join(vault, "04_Projects", "学习", bookTitle);
const memoryPath = path.join(projectDir, "classroom_memory.md");

if (!fs.existsSync(projectDir)) {
  console.error(`Project directory not found: ${path.relative(vault, projectDir)}`);
  process.exit(1);
}

const created = !fs.existsSync(memoryPath);
if (created) {
  fs.writeFileSync(memoryPath, template(bookTitle), "utf8");
}

console.log(JSON.stringify({
  ok: true,
  path: path.relative(vault, memoryPath),
  created,
}, null, 2));

function template(title) {
  const today = new Date().toISOString().slice(0, 10);
  return `---
type: classroom_memory
status: active
created: ${today}
project: "[[04_Projects/学习/${title}/${title}|${title}]]"
---

# Classroom Memory - ${title}

## Teacher Memory

- 待记录：学习者常见卡点、有效追问方式、必须回炉的判断。

## Classmate Memory

- 待记录：有用的笨问题、典型错误答案、反方客户或读者质疑。

## Shared Classroom Memory

- 待记录：反复使用的真实场景、下次开课要自然带回的问题、课堂声音偏好。

## Last Updated

- lesson: pending
- session: pending
- updated_at: ${today}
`;
}
