---
name: book-learning-loop
description: Use when the user wants to import a book into an Obsidian vault or continue an existing book-learning project: source preservation, course map, dynamic lessons, live study sessions, review queue recovery, absorption into 03_Notes, application, and archive. Trigger phrases include 学一本书, 读一本书, 继续这本书, 接着学习第 N 课, 下一课, 学习系统, 课程拆解, 学习闭环, book learning, and AI 家教. Prefer this over generic learning skills when a project already has progress.md, curriculum.md, role_contract.md, or session files.
---

# Book Learning Loop

Turn one book into an Obsidian-based learning system. The skill is book-agnostic: it manages the loop from original text to course material, study sessions, durable judgment, application, and archive.

## Source Of Truth

This skill is managed from the sibling `nemo-skills` repository. Edit the source skill there, then publish into the vault. Do not hand-edit the generated vault copy.

## Helper Scripts

Run these from the vault root after publishing, or pass `--vault <vault-root>` explicitly.

```bash
node .agents/skills/book-learning-loop/scripts/verify-project.mjs --vault . --book-title <book-title> --book-slug <book-slug>
node .agents/skills/book-learning-loop/scripts/close-lesson-checklist.mjs --vault . --session <session-md> [--next-session <session-md>] [--strict]
node .agents/skills/book-learning-loop/scripts/check-absorption-gate.mjs --vault . --session <session-md>
```

- `verify-project.mjs`: checks that the source package, intake files, project files, roles, sessions, and logs exist.
  - Use `--book-title` for `04_Projects/学习/<book-title>`.
  - Use `--book-slug` for `02_Sources/_books/<book-slug>` and `02_Sources/_intake/books/<book-slug>`.
  - The old `--book <book-title-or-slug>` form still works when title and slug are identical.
- `close-lesson-checklist.mjs`: prints the fixed closeout checklist for `progress.md`, `review_queue.md`, `application_log.md`, and next-lesson review.
  - Pass `--next-session` after the next lesson exists to verify review queue recovery appears before classroom content.
  - Pass `--strict` when the checklist should fail the command on missing required items.
- `check-absorption-gate.mjs`: fails if a completed session has no learner Feynman summary, teacher diagnosis, or promoted `03_Notes` link.

## Core Principle

Use a fixed learning flow, not a fully fixed course.

- Fixed: source package, book map, learning preferences, role contract, session workflow, absorption standard, archive rule.
- Dynamic: lesson depth, examples, review weight, whether chapters are merged, and what gets promoted into `03_Notes`.

## Layer Contract

Use this split unless the user explicitly asks for a different structure:

```text
02_Sources/_books/<book-slug>/
  book.md
  source/<original book markdown and assets>
  manifest.json

02_Sources/_intake/books/<book-slug>/
  course-map.md
  lessons/

04_Projects/学习/<book-title>/
  initialization.md
  learner_profile.md
  role_interview.md
  role_contract.md
  roles/
  teaching_decisions.md
  curriculum.md
  progress.md
  review_queue.md
  application_log.md
  sessions/
  _archive/

03_Notes/
  only durable absorbed judgments, never raw chapter summaries
```

Definitions:

- `02_Sources/_books` is the preserved source package. It may contain the full book for cross-device sync and stable local management.
- `02_Sources/_intake/books` is derived course material. It is still source-derived material, not personal knowledge.
- `04_Projects/学习` is the active learning project: preferences, roles, progress, session records, review, application, and archive.
- `03_Notes` is only for stable judgments the user has understood, tested, and can reuse.

## Mode Routing

- `import/setup mode`: read `references/import-and-copyright.md` and `references/lifecycle.md`.
- `role/curriculum mode`: read `references/lifecycle.md`.
- `classroom/session mode`: read `references/classroom-facilitation.md`.
- `absorption/note mode`: read `references/absorption-and-notes.md`.
- `closeout/verification mode`: run the helper scripts before reporting completion.

Keep setup and classroom voices separate. In classroom mode, do not lead with file-write narration; mention background updates only briefly after the teaching move.

## Hard Gates

- Do not start the first lesson until `learner_profile.md`, `role_contract.md`, and role files exist and match the user's stated preference.
- Do not create the official course map before the role interview and teaching decisions are complete.
- Do not promote a lesson into `03_Notes` before the learner produces a Feynman-style summary in their own words.
- Do not let a live lesson turn into article planning, product design, implementation, or wording polish unless the user explicitly switches modes.
- Do not quote long copyrighted passages in generated notes.

## Completion Check

Before saying the learning system is initialized, verify:

- the full book source package exists in `02_Sources/_books`
- the learning project exists in `04_Projects/学习`
- `initialization.md`, `role_interview.md`, `learner_profile.md`, `role_contract.md`, and `teaching_decisions.md` exist
- role and learner profile files are not still `needs_interview`
- the course map exists in `02_Sources/_intake/books` only after the role interview and teaching decisions
- `curriculum.md`, `progress.md`, `review_queue.md`, and `application_log.md` exist
- git ignore protects imported full-text source when needed
- internal links point to existing vault files

Reference details: `references/lifecycle.md`, `references/import-and-copyright.md`, `references/classroom-facilitation.md`, and `references/absorption-and-notes.md`.
