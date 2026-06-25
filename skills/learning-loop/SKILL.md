---
name: learning-loop
description: Use when the user wants to import a book into an Obsidian vault, continue an existing book-learning project, or learn a topic through a feedback-driven learning loop. Book mode handles source preservation, course map, dynamic lessons, live study sessions, review queue recovery, absorption into 03_Notes, application, and archive. Topic fallback handles lightweight plans and numbered learning articles when no source book or book project exists. Trigger phrases include 学一本书, 读一本书, 继续这本书, 接着学习第 N 课, 下一课, 学一个课题, 带我学一个课题, 继续下一篇, 学习系统, 课程拆解, 学习闭环, learning loop, book learning, and AI 家教. Prefer book mode over topic fallback when a project already has progress.md, curriculum.md, role_contract.md, or session files.
---

# Learning Loop

Turn one book into an Obsidian-based learning system. The skill is book-first and source-backed: it manages the loop from original text to course material, study sessions, durable judgment, application, and archive. When there is no book source or active book project, it can run a lighter topic-learning fallback that uses feedback-driven lesson articles without pretending there is a source-backed classroom.

## Source Of Truth

This skill is managed from the sibling `nemo-skills` repository. Edit the source skill there, then publish into the vault. Do not hand-edit the generated vault copy.

## Helper Scripts

Run these from the vault root after publishing, or pass `--vault <vault-root>` explicitly.

```bash
node .agents/skills/learning-loop/scripts/verify-project.mjs --vault . --book-title <book-title> --book-slug <book-slug>
node .agents/skills/learning-loop/scripts/ensure-classroom-memory.mjs --vault . --book-title <book-title>
node .agents/skills/learning-loop/scripts/check-classroom-memory.mjs --vault . --book-title <book-title> [--session <session-md>]
node .agents/skills/learning-loop/scripts/close-lesson-checklist.mjs --vault . --session <session-md> [--next-session <session-md>] [--strict]
node .agents/skills/learning-loop/scripts/check-absorption-gate.mjs --vault . --session <session-md>
```

- `verify-project.mjs`: checks that the source package, intake files, project files, roles, sessions, and logs exist.
  - Use `--book-title` for `04_Projects/学习/<book-title>`.
  - Use `--book-slug` for `02_Sources/_books/<book-slug>` and `02_Sources/_intake/books/<book-slug>`.
  - The old `--book <book-title-or-slug>` form still works when title and slug are identical.
- `ensure-classroom-memory.mjs`: creates `classroom_memory.md` for a book project when it does not exist.
- `check-classroom-memory.mjs`: checks that classroom memory has teacher, classmate, shared, and last-updated sections; pass `--session` to verify the current session is referenced.
- `close-lesson-checklist.mjs`: prints the fixed closeout checklist for `progress.md`, `review_queue.md`, `application_log.md`, and next-lesson review.
  - Pass `--next-session` after the next lesson exists to verify review queue recovery appears before classroom content.
  - Pass `--strict` when the checklist should fail the command on missing required items.
- `check-absorption-gate.mjs`: fails if a completed session has no learner Feynman summary, teacher diagnosis, or promoted `03_Notes` link.

## Core Principle

Use a fixed learning flow, not a fully fixed course.

- Fixed: source package, book map, learning preferences, role contract, session workflow, absorption standard, archive rule.
- Dynamic: lesson depth, examples, review weight, feedback-driven difficulty, whether chapters are merged, and what gets promoted into `03_Notes`.
- Fallback: when no book source exists, use a lightweight topic loop with a plan, numbered lesson articles, and explicit learning feedback. Do not let topic fallback replace source-backed book mode.

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
  classroom_memory.md
  sessions/
  _archive/

03_Notes/
  only durable absorbed judgments, never raw chapter summaries
```

Topic fallback uses a separate, lighter structure:

```text
04_Projects/学习/_topics/<topic-title>/
  00-学习计划.md
  01.md
  02.md
  assets/
```

Definitions:

- `02_Sources/_books` is the preserved source package. It may contain the full book for cross-device sync and stable local management.
- `02_Sources/_intake/books` is derived course material. It is still source-derived material, not personal knowledge.
- `04_Projects/学习` is the active learning project: preferences, roles, progress, session records, review, application, and archive.
- `classroom_memory.md` is the dynamic classroom memory layer: role traits stay in `role_contract.md` and `roles/`, while teacher memory, classmate memory, and shared classroom callbacks accumulate here after real lessons.
- `04_Projects/学习/_topics` is only for non-book topic learning. It may contain lightweight learning plans and numbered articles, but it must not be promoted to a book project unless a source package and curriculum are later created.
- `03_Notes` is only for stable judgments the user has understood, tested, and can reuse.

## Mode Routing

- `import/setup mode`: read `references/import-and-copyright.md` and `references/lifecycle.md`.
- `role/curriculum mode`: read `references/lifecycle.md`; read `references/learning-experience-roles.md` when designing teacher, companion, or persona-driven learning experience.
- `classroom/session mode`: read `references/classroom-facilitation.md`; read `references/learning-experience-roles.md` when the opening, teacher voice, companion role, or motivation loop needs revision.
- `adaptive learning mode`: read `references/adaptive-learning-layer.md` when selecting the next lesson depth from user feedback.
- `topic fallback mode`: read `references/adaptive-learning-layer.md` when the user wants to learn a topic and no book source or active book project exists.
- `absorption/note mode`: read `references/absorption-and-notes.md`.
- `closeout/verification mode`: run the helper scripts before reporting completion.

Keep setup, classroom, and topic-article voices separate. In classroom mode, do not lead with file-write narration; mention background updates only briefly after the teaching move. In topic fallback mode, write concise learning articles and request feedback before generating the next article.

## Hard Gates

- Do not start the first lesson until `learner_profile.md`, `role_contract.md`, and role files exist and match the user's stated preference.
- Do not create the official course map before the role interview and teaching decisions are complete.
- Do not route an existing book project into topic fallback. If `progress.md`, `curriculum.md`, `role_contract.md`, or session files exist, continue book mode.
- Do not promote a lesson into `03_Notes` before the learner produces a Feynman-style summary in their own words.
- Do not let a live lesson turn into article planning, product design, implementation, or wording polish unless the user explicitly switches modes.
- Do not generate the next topic article from template prompts alone; extract only the learner's real feedback, or state that the next article is based on visible context.
- Do not quote long copyrighted passages in generated notes.

## Completion Check

Before saying the learning system is initialized, verify:

- the full book source package exists in `02_Sources/_books`
- the learning project exists in `04_Projects/学习`
- `initialization.md`, `role_interview.md`, `learner_profile.md`, `role_contract.md`, and `teaching_decisions.md` exist
- role and learner profile files are not still `needs_interview`
- the course map exists in `02_Sources/_intake/books` only after the role interview and teaching decisions
- `curriculum.md`, `progress.md`, `review_queue.md`, and `application_log.md` exist
- `classroom_memory.md` exists for projects that use teacher or study companion interaction
- git ignore protects imported full-text source when needed
- internal links point to existing vault files

Before saying a topic fallback article is generated, verify:

- the topic directory exists under `04_Projects/学习/_topics`
- `00-学习计划.md` exists
- the next article number is contiguous
- the article ends with a real `学习反馈` area
- the learning plan records current progress, feedback summary, and next direction

Reference details: `references/lifecycle.md`, `references/import-and-copyright.md`, `references/classroom-facilitation.md`, `references/learning-experience-roles.md`, `references/adaptive-learning-layer.md`, and `references/absorption-and-notes.md`.
