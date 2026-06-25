# Absorption And Notes

Use this reference when deciding whether a completed lesson should produce durable `03_Notes` knowledge.

## Hard Rule

The agent must not promote a lesson summary into `03_Notes` merely because the discussion produced good-sounding conclusions.

The learner must first produce a Feynman-style summary in their own words:

- what the lesson was about
- what rule they think they learned
- how the rule worked in the current case
- where else they can use it
- what they are still unsure about

The agent's role is to diagnose, correct, expand, and then write the final card only from the learner's demonstrated understanding.

Until that happens, keep the item in the session note or `review_queue.md` as an absorption candidate.

## Promote Only

- a concept the user can explain in their own words
- a distinction that changes future judgment
- a method tested in a real or representative scenario
- a reusable rule connected to existing MOCs

## Do Not Promote

- raw chapter summaries
- copied book passages
- untested claims
- session transcripts

## Feynman Absorption Script

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

## Knowledge Layer

When durable absorption is needed, use the vault's `llm-wiki` / note-ingest workflow rather than bypassing knowledge-layer rules.
