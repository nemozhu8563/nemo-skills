---
name: book-learning-loop
description: Use when the user wants to import a book into an Obsidian vault and turn it into a closed learning loop: source preservation, course map, dynamic lessons, study sessions, absorption into 03_Notes, application, and archive. Trigger phrases include 学一本书, 读一本书, 学习系统, 课程拆解, 学习闭环, book learning, and AI 家教.
---

# Book Learning Loop

Turn one book into an Obsidian-based learning system. The skill is book-agnostic: it manages the loop from original text to course material, study sessions, durable judgment, application, and archive.

## Source Of Truth

This skill is managed from the sibling `nemo-skills` repository. Edit the source skill there, then publish into the vault. Do not hand-edit the generated vault copy.

## Helper Scripts

Run these from the vault root after publishing, or pass `--vault <vault-root>` explicitly.

```bash
node .agents/skills/book-learning-loop/scripts/verify-project.mjs --vault . --book <book-title>
node .agents/skills/book-learning-loop/scripts/close-lesson-checklist.mjs --vault . --session <session-md>
node .agents/skills/book-learning-loop/scripts/check-absorption-gate.mjs --vault . --session <session-md>
```

- `verify-project.mjs`: checks that the source package, intake files, project files, roles, sessions, and logs exist.
- `close-lesson-checklist.mjs`: prints the fixed closeout checklist for `progress.md`, `review_queue.md`, `application_log.md`, and next-lesson review.
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

## Git And Copyright Boundary

When importing a copyrighted commercial book into a vault that is also a git repository:

- copy the full book into the vault only when the user wants local sync/management
- add or verify a git ignore rule for `02_Sources/_books/**/source/`
- keep `book.md`, `manifest.json`, course maps, learning records, and absorbed notes trackable unless the user says otherwise
- do not quote long copyrighted passages in generated notes; use short excerpts only when needed for learning context

## Scale Workflow

### 1. Import The Book

Create a source package:

```text
02_Sources/_books/<book-slug>/book.md
02_Sources/_books/<book-slug>/source/
02_Sources/_books/<book-slug>/manifest.json
```

`book.md` should include:

- YAML frontmatter: `type: book_source`, `status`, `title`, `author`, `created`, `source_path`, `project`
- original source path
- local source path
- chapter index
- current learning status
- links to course map and learning project

`manifest.json` should include:

- original path
- imported source path
- imported assets path when present
- import timestamp
- line count
- checksum when practical

### 2. Initialize The Learning Project

Before designing curriculum, create the active project shell:

```text
04_Projects/学习/<book-title>/initialization.md
04_Projects/学习/<book-title>/progress.md
04_Projects/学习/<book-title>/review_queue.md
04_Projects/学习/<book-title>/application_log.md
```

`initialization.md` should state:

- why this book is being learned
- what is already known
- what is still unknown
- what must be asked before curriculum design
- current phase, such as `role_interview`

At this stage, do not create the official course map or lesson materials yet. If you need to sketch them, mark them clearly as drafts.

### 3. Run The Role And Preference Interview

The agent must ask questions before finalizing the learner profile, role contract, course map, or teaching decisions.

Create:

```text
04_Projects/学习/<book-title>/role_interview.md
```

Collect information for four roles:

- `system_operator`: how the AI learning system itself should behave
- `learner`: the user's learning goal, preference, constraints, weak spots, and desired pressure level
- `school_runner`: the program owner's view: what counts as success, assessment, cadence, archive, and continuation rules
- `teacher`: teaching persona, strictness, speaking style, examples, and boundaries
- `classmate` or peer role when useful: a practice partner, counterparty, skeptical reader, customer, or error mirror that creates productive friction without taking over the teacher role

Do not infer these silently if the user is actively designing the system. Ask in small batches and write answers back into `role_interview.md`.

### 4. Capture Learning Preference

Create or update:

```text
04_Projects/学习/<book-title>/learner_profile.md
```

Capture:

- why the user wants to learn this book
- target use cases
- preferred teaching style
- desired pressure level
- session length
- output preference
- known weak spots
- examples that should be grounded in the user's real work

If preferences are still unknown, mark the file as `needs_interview` and do not proceed to official curriculum.

### 5. Define Roles

```text
04_Projects/学习/<book-title>/role_contract.md
04_Projects/学习/<book-title>/roles/
```

This step is a hard checkpoint. Do not start the first lesson until the project has an explicit role/persona contract.

The contract should define:

- system operator role
- learner role
- school runner / program director role
- teacher roles
- optional classmate / peer-practice roles when requested or useful
- each role's job
- personality and speaking style
- strictness
- how it responds when the user is vague, avoidant, or wrong
- how roles hand off to each other
- boundaries: what they must not do

Roles serve learning. Do not let roleplay or emotional interaction override the book, the user's goals, or the application loop.

Default teacher role split:

- `socratic_coach.md`: asks one question at a time, exposes understanding gaps, avoids long lectures first
- `concept_teacher.md`: explains book concepts with concise examples after the user has attempted an answer
- `application_coach.md`: turns each lesson into a real application in writing, business, work, or communication
- `classmate.md` when requested: creates peer pressure through naive questions, counterparty objections, or intentionally flawed answers that the user must diagnose

### 6. Create Teaching Decisions

```text
04_Projects/学习/<book-title>/teaching_decisions.md
```

Teaching decisions translate the role interview into course-design rules:

- what the course optimizes for
- what to skip, compress, or emphasize
- how much Socratic questioning versus explanation
- whether to use writing, business, personal communication, or project examples first
- when to pause for review
- what counts as enough mastery for the next lesson
- what can be promoted to `03_Notes`

### 7. Build The Book Map

Only after steps 3-6, read the table of contents and headings, then create:

```text
02_Sources/_intake/books/<book-slug>/course-map.md
```

The map should contain:

- book thesis in 3-5 bullets
- module structure
- chapter list
- which chapters are foundations, practice, advanced material, or optional
- expected ability outcomes
- final application/assessment idea
- links to `learner_profile.md`, `role_contract.md`, and `teaching_decisions.md`

Do not generate every lesson in full at this stage unless the user explicitly asks.

### 8. Create The Curriculum

Create:

```text
04_Projects/学习/<book-title>/curriculum.md
```

The curriculum should be a global route, not a fully locked lesson script:

- module order
- likely lesson sequence
- chapters that may be merged
- review checkpoints
- application milestones
- final project/assessment
- rule for when the next lesson is adjusted

### 9. Generate Current Lesson

For the next session only, create:

```text
02_Sources/_intake/books/<book-slug>/lessons/lesson-XX-<short-title>.md
```

Each lesson should include:

- source chapter range
- learning objective
- key concepts
- Socratic question sequence
- explanation anchors
- short practice task
- application prompt
- absorption candidates
- next-session decision criteria

Question quality rule:

- The first question of a lesson must be answerable by a concrete scene, not by interpreting an abstract contrast.
- Avoid opening with phrases like "you thought you were expressing, but were actually persuading" unless you immediately define the test.
- A good first question names the action surface, the counterparty, and the expected reaction, for example: "When did you recently send a message, explain a plan, write an article, or introduce a product because you wanted someone to reply, agree, book, pay, forward, or accept a plan?"

### 10. Run A Study Session

Create one session note under:

```text
04_Projects/学习/<book-title>/sessions/YYYY-MM-DD-lesson-XX.md
```

Before starting, verify `learner_profile.md`, `role_contract.md`, and the role files exist and are consistent with the user's stated preference. If not, stop at role design; do not open with lesson questions.

Session flow:

1. state lesson goal
2. state the core concept in teacher first-person voice
3. explain why the next question matters for the lesson
4. ask one concrete question
5. wait for the user's answer
6. diagnose the answer
7. explain only what is needed
8. run one application exercise
9. run a transfer check in a second scenario
10. request a Feynman summary before absorption
11. update the session summary
12. update `progress.md`, `review_queue.md`, and `application_log.md`

Do not let the session become only interrogation or sentence polishing. The teacher must keep the blackboard visible:

```text
Lesson goal:
Core concept:
Why this exercise matters:
Your case:
My diagnosis:
Next small exercise:
```

## Fixed Classroom Scripts

Use these scripts as stable classroom moves. Adapt wording to the book and user case, but preserve the function.

### Lesson Opening Script

Before asking the first question, say:

```text
This lesson is about: <one ability>.
You are not learning <common misunderstanding>.
You are learning to do <observable action>.
We will use your case only as training material, not as the whole lesson.
By the end, you should be able to <transfer outcome>.
```

### Question Repair Script

If the user says the question is unclear, do not defend it. Repair it:

```text
You are right. That question is not operational.
The test is: <decision rule>.
Answer it with: <concrete format>.
```

### Diagnosis Script

Every diagnosis should separate:

```text
Pass:
Not yet:
Why it matters:
Next correction:
```

Avoid only saying "not good enough"; identify the exact failure mode.

### Concept Return Script

After 2-3 turns of case work, return to the lesson concept:

```text
Pause. This is the course point:
<concept>
Your case shows it because <case mapping>.
This is not about optimizing one sentence; it is about learning <transferable skill>.
```

### Feynman Absorption Script

Before writing to `03_Notes`, ask:

```text
Use your own words:
1. What was this lesson about?
2. What rule did you learn?
3. How did it work in your current case?
4. Where else can you use it?
5. What is still unclear?
```

Only after this summary should the agent diagnose absorption and write a durable card.

### Progress Update Script

At the end of a lesson, update:

- session status
- `progress.md`: recently completed lesson, current state, next action
- `review_queue.md`: what to review before the next lesson
- `application_log.md`: what real or representative scenario was practiced
- `03_Notes`: only after Feynman summary passes

### Goal Split Scaffold

When the user mixes several desired outcomes, force this scaffold before any wording exercise:

```text
Surface target:
Middle target:
Deep target:
This round's main battlefield:
This round is not trying to:
```

If the user cannot choose the main battlefield, do not continue to sentence writing or lesson expansion.

### Anti-Wording-Polish Script

When the session starts turning into wording optimization, stop and say:

```text
Pause. We are not polishing the sentence yet.
The question is:
- what goal this sentence serves
- what stage this conversation is in
- what resistance the other person has
```

Only return to wording after these three are clear.

### Review Queue Opening Script

Before starting a new lesson, spend three minutes on `review_queue.md`:

```text
Before new content, we recover one pending trigger:
<review_queue item>
Answer only:
1. current stage
2. main resistance
3. next target
```

If the learner fails the review item twice, pause the new lesson and run a micro-review.

### Mode Boundary

Keep setup and classroom voices separate:

- `scale/setup mode`: importing, initializing, designing roles, mapping curriculum, updating project status.
- `classroom/session mode`: teaching in first-person teacher voice, diagnosing answers, running exercises, requesting Feynman summaries.

In classroom mode, do not lead with file-write narration. Mention background updates only briefly after the teaching move.

### 11. Absorb Judgment

After a lesson, decide whether anything should enter `03_Notes`.

Hard rule: the agent must not promote a lesson summary into `03_Notes` merely because the discussion produced good-sounding conclusions. The learner must first produce a Feynman-style summary in their own words:

- what the lesson was about
- what rule they think they learned
- how the rule worked in the current case
- where else they can use it
- what they are still unsure about

The agent's role is to diagnose, correct, expand, and then write the final card only from the learner's demonstrated understanding. Until that happens, keep the item in the session note or `review_queue.md` as an absorption candidate.

Promote only:

- a concept the user can explain in their own words
- a distinction that changes future judgment
- a method tested in a real or representative scenario
- a reusable rule connected to existing MOCs

Do not promote:

- raw chapter summaries
- copied book passages
- untested claims
- session transcripts

When durable absorption is needed, use the vault's `llm-wiki` / note-ingest workflow rather than bypassing knowledge-layer rules.

### 12. Archive

When a book is complete or paused:

- move completed or stale process notes into the project's `_archive/` when useful
- keep `book.md`, `course-map.md`, `curriculum.md`, `progress.md`, and durable `03_Notes` links discoverable
- add a short final review: what changed, what was applied, what still needs practice

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
