# Book Learning Lifecycle

Use this reference for setup mode: importing, initializing, designing roles, mapping curriculum, generating current lesson material, and archiving.

## 1. Import The Book

Use `references/import-and-copyright.md` for the source package and copyright boundary.

## 2. Initialize The Learning Project

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

## 3. Run The Role And Preference Interview

The agent must ask questions before finalizing the learner profile, role contract, course map, or teaching decisions.

When the user wants a stronger teacher, study companion, persona, or motivational learning experience, read `references/learning-experience-roles.md` before writing the role contract. Extract functional roles and experience mechanics; do not copy a specific character setup unless the user explicitly asks for it.

Create:

```text
04_Projects/学习/<book-title>/role_interview.md
```

Collect information for these roles:

- `system_operator`: how the AI learning system itself should behave
- `learner`: the user's learning goal, preference, constraints, weak spots, and desired pressure level
- `school_runner`: the program owner's view: success, assessment, cadence, archive, and continuation rules
- `teacher`: teaching persona, strictness, speaking style, examples, and boundaries
- `study_companion` or peer role when useful: a practice partner, naive questioner, progress witness, skeptical reader, customer, or error mirror that creates productive friction and persistence without taking over the teacher role

Do not infer these silently if the user is actively designing the system. Ask in small batches and write answers back into `role_interview.md`.

## 4. Capture Learning Preference

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

## 5. Define Roles

Create:

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
- optional study companion / peer-practice roles when requested or useful
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
- `study_companion.md` or `classmate.md` when requested: creates continuity and productive friction through naive questions, progress witnessing, counterparty objections, or intentionally flawed answers that the user must diagnose

## 6. Create Teaching Decisions

Create:

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

## 7. Build The Book Map

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

## 8. Create The Curriculum

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

## 9. Generate Current Lesson

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
- A good first question names the action surface, the counterparty, and the expected reaction.

## Archive

When a book is complete or paused:

- move completed or stale process notes into the project's `_archive/` when useful
- keep `book.md`, `course-map.md`, `curriculum.md`, `progress.md`, and durable `03_Notes` links discoverable
- add a short final review: what changed, what was applied, what still needs practice
