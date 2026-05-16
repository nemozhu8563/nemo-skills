# 中文文章质检 Rubric

## 1. 真颗粒度 vs 话术颗粒度

Judge whether the draft truly sees more structure, or only performs structure.

True granularity:

- turns one vague issue into multiple distinguishable mechanisms
- gives boundaries, exceptions, or failure cases
- shows how the author reached the conclusion
- provides examples that change the reader's understanding
- compresses where compression is possible

Rhetorical granularity:

- repeats one idea through synonyms
- uses neat triads to simulate completeness
- uses value words instead of mechanisms
- ends every section with a polished judgment sentence
- makes the reader feel clarity without giving them a new handle

Useful question: after deleting this paragraph, what specific thinking tool disappears?

## 2. Sentence Function Test

For every suspicious pair of adjacent sentences, ask what job each sentence performs.

Common functions:

- introduce topic
- narrow question
- make claim
- give reason
- give example
- define boundary
- answer objection
- transition
- summarize
- intensify emotion

If two adjacent sentences perform the same function and the second does not add new detail, mark it as functional repetition.

Typical pattern:

```text
所以我不会问：X。
我会先问：Y。
```

Both sentences are "change the question". Usually merge them.

## 3. Mechanism Test

A claim has enough depth only when at least one of these is present:

- cause: why this happens
- process: how it unfolds step by step
- boundary: when it stops being true
- contrast: what similar thing it is not
- example: where it appears in real life
- consequence: what decision changes because of it

If a paragraph only states a correct conclusion, mark it as "claim without mechanism".

## 4. Evidence and Scene Test

Look for signs that the author has actually met the problem:

- a book, tool, note, project, conversation, mistake, or decision appears
- the author admits a hesitation or a boundary
- the article names a concrete use case instead of a universal lesson
- the example is not merely decorative; it changes the argument

If the article has no scene, it may still be logically correct, but it will feel sealed and interchangeable.

## 5. AI Fingerprint Overlay

Use this layer when the user asks for AI flavor or references `dbs-ai-check`.

High-frequency patterns:

- over-neat "A, B, C" categories
- repeated "not X, but Y"
- too many perfect transitions
- conclusion wrapped as a portable protocol
- every paragraph has a mini golden sentence
- no visible uncertainty
- example placeholders instead of real examples

Do not mechanically punish these patterns. Mark them only when they make the article smoother than its thinking.

## 6. Rewrite Guidance

Prefer these fixes:

- merge duplicate transitions
- replace one abstract sentence with one concrete example
- keep one key category and cut decorative sibling categories
- add a boundary sentence: "这只适用于..."
- add a friction sentence: "我还没完全想清楚的是..."
- turn a slogan into a decision criterion

Avoid these fixes:

- adding more adjectives
- adding a new framework name
- polishing all roughness away
- inventing a personal scene
- turning every issue into a three-bullet summary

## 7. Final Priority Rule

Always tell the user the first fix with the highest leverage.

Usually the order is:

1. fix repeated function
2. add mechanism to the central claim
3. add one real example
4. roughen the too-perfect ending
5. shorten decorative rhythm
