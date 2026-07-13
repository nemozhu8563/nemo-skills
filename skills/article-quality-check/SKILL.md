---
name: article-quality-check
description: |
  中文文章质检 Skill。用于按用户的文章检查方法判断一篇草稿是否有真实信息密度、论证颗粒度、句子功能增量和个人现场感；识别功能重复、顺滑空转、框架先行、结尾总结卡片、AI 味和“看起来很有道理但没新增信息”的段落。触发场景包括：检查文章、按真颗粒度 vs 话术颗粒度判断、看看有没有重复、看看是不是废话、帮我按信息密度审一遍、结合 dbs-ai-check 看文章、优化文章前先诊断。
---

# 中文文章质检

## Overview

Use this skill to audit Chinese drafts before rewriting. The goal is not to make the article look less like AI; the goal is to find where the writing fails to carry new thought.

Default to diagnosis first. Rewrite only when the user explicitly asks for optimization, revision, or a new version.

## Core Standard

Treat good writing as accumulated function, not smooth wording.

Check five layers:

1. Information density: each paragraph should add a claim, example, mechanism, boundary, counterexample, or decision criterion.
2. Argument granularity: important claims should show why they hold, where they apply, and what would break them.
3. Sentence function: adjacent sentences should not perform the same job, especially repeated transitions like "I will not ask X; I will ask Y".
4. Personal evidence: the draft should contain enough lived context, concrete reading, work records, examples, or unresolved hesitation to avoid sounding sealed and frictionless.
5. Operation logic for tutorials: each section should have one reader action, and every sentence should help complete the current action instead of explaining the article arrangement or drifting into another step.

When the user asks to "combine dbs-ai-check" or "check AI flavor", also apply AI-writing fingerprint logic: perfect smoothness, over-neat triads, fixed transitions, fake completeness, and card-like endings.

Read `references/rubric.md` when doing a full audit, when the article is more than 500 Chinese characters, or when the user asks for a standard/methodology-level judgment.

For tutorial/how-to/setup/workflow drafts, also read `references/tutorial-logic-examples.md` and run the Tutorial Operation Logic Check before rewriting.

## Workflow

1. Identify the article type: short essay, 公众号 draft, Zhihu answer, technical explainer, note-to-article draft, or social post.
2. State the overall verdict in plain Chinese: good spine / weak spine / smooth but thin / dense but hard to read / needs examples / operation logic broken.
3. Scan in text order. Quote the exact sentence or paragraph that has a problem.
4. For each issue, name the concrete failure:
   - no new information
   - repeated function
   - claim without mechanism
   - framework not supported by examples
   - operation logic broken
   - step belongs to another section
   - article-arrangement commentary
   - reader-perspective drift
   - audience label mismatch
   - bridge sentence patch
   - section action drift
   - over-neat AI-style rhythm
   - summary-card ending
   - missing personal scene or uncertainty
5. Explain why it weakens the article in one or two direct sentences.
6. If the user asked for optimization, revise only after the diagnosis and keep the rewrite faithful to the user's position.

## Output Shapes

### Diagnosis Only

Use this when the user asks whether the article works, whether it repeats, whether it has AI flavor, or whether it meets the standard.

```markdown
**总体判断**
{1-3 sentences. Say the real problem directly.}

**具体问题**

**第 1 处**
> {quote}

{what this sentence/paragraph is doing, why it is weak, and what kind of material would fix it}
`{label} {severity}`

**第 2 处**
...

**最该先改的地方**
{1-3 concrete priorities}
```

Severity labels:

- `强信号`: hurts the article immediately. In tutorials, article-arrangement commentary, reader-perspective drift, and step ownership errors are strong signals by default because they break the reader's operation flow.
- `中信号`: common AI/smooth-writing pattern; worth fixing.
- `弱信号`: only a risk if the surrounding text is also thin.

### Optimization

Use this when the user asks to optimize or produce a new version.

```markdown
**改动方向**
{briefly list the structural changes}

**优化版**
{revised article}

**保留和改变**
{short note on what was preserved and what was removed}
```

Do not over-polish. Keep useful roughness: a real example, a specific hesitation, or a sentence that sounds like the author thinking.

## Calibration Rules

- Do not count every list of three as a problem. It becomes a problem when it replaces evidence.
- Do not treat plain structure as AI flavor by default. A clear outline is good when each part carries new substance.
- Do not reward length. A shorter paragraph with one precise mechanism is better than a smooth paragraph with five synonyms.
- For tutorials, do not treat operation logic as mere style. If a sentence belongs to another step, explains why the article is arranged a certain way, or interrupts the current reader action, label it as a logic problem and `强信号`.
- For tutorials, check reader perspective. Phrases like "第一篇里", "本文先不", "这篇不展开", and "后面再讲" are article-arrangement commentary and must be handled. Vague audience labels like "普通读者" should be replaced with the article's actual reader name, such as "新手", "第一次安装 Codex 的人", or the user's specified audience.
- Do not rewrite the user's view into a more generic essay. Preserve their actual judgment, including uncertainty.
- Do not invent examples, books, personal experiences, or reading history. If the article needs them, say what kind of example is missing.

## References

- Read `references/rubric.md` for the full inspection rubric, labels, and rewrite guidance.
- Read `references/tutorial-logic-examples.md` for tutorial operation-logic calibration, bad/good examples, and expected labels.
