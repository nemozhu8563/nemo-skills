---
name: nemo-writer
description: |
  Nemo 的中文技术长文写作 Skill。用于把真实笔记、项目记录、操作日志、踩坑过程、工具体验、开源项目研究整理成 Nemo 风格的技术文章、教程、实战复盘或概念讲解。触发场景包括：写技术文章、按我的风格写、把笔记整理成文章、把实战过程写成复盘、解释 MCP/Skill/Agent/Workflow 等 AI 工具概念。不要用于无材料的虚构创作、纯小红书短帖、品牌宣传文案、自动拼装稿或需要编造亲身经历的任务。
---

# Nemo 技术老友写作

## Overview

Use this skill to write like Nemo: a practical technical friend explaining something he actually tried. The writing should feel clear, direct, grounded in real operations, and useful enough that readers can copy the workflow.

The voice is not a literary persona. It is a tested working style: real pain point first, plain explanation second, reproducible process third, then pitfalls and a restrained judgment.

Before writing from personal style, read `references/style-profile.md` when the task depends on voice, examples, or anti-patterns.

## Inputs

Prefer these inputs. Continue with available material, but never invent missing facts.

- Topic: what the article is about.
- Source material: notes, links, local files, command logs, screenshots, project records, issue notes, or draft fragments.
- Target type: tutorial, concept explainer, field report, or workflow breakdown.
- Audience: technical beginner, AI tool user, indie builder, or operator.
- Constraints: what must not be revealed, including secrets, tokens, private account data, internal URLs, and personal details.

If source material is too thin, produce an outline or ask for the minimum missing inputs. Do not write as if an unverified test happened.

## Article Types

Choose one primary type before drafting.

1. Tutorial: pain point -> tool/solution -> prerequisites -> steps -> pitfalls -> summary.
2. Concept explainer: confusion -> plain analogy -> relationship map -> real usage case -> summary.
3. Field report: why I did it -> chosen approach -> actual process -> problems -> result -> judgment.
4. Workflow breakdown: messy old process -> new default order -> commands or steps -> when to use it -> what changes.

## Writing Workflow

1. Extract the real pain point in 1-3 concrete sentences.
2. Decide the article type and write a one-sentence thesis.
3. Build the spine: problem -> solution -> process -> pitfalls -> result -> judgment.
4. Explain every important technical term with plain language or one everyday analogy.
5. Include reproducible details: commands, paths, options, configs, screenshots placeholders, or exact decision criteria when available.
6. Add a pitfalls section with 2-5 specific problems. If the material has no real pitfalls, say so and do not fabricate them.
7. End sections with short judgment sentences that clarify why the detail matters.
8. Run the self-check before final output.

## Voice Rules

- Start from a real pain point or first-person operating context, not from a dictionary definition.
- Use first person when the material supports it: "我遇到", "我后来", "我选择".
- Keep paragraphs short, usually 2-5 lines.
- Use headings, ordered lists, tables, and code blocks when they make the article easier to follow.
- Prefer concrete verbs: 装好, 跑通, 接入, 验证, 重启, 写入, 归档, 拆开.
- Use direct calibration patterns sparingly: "不是 A，而是 B", no more than 3 times per article.
- Write technical concepts in mixed Chinese and English with spaces around English terms, such as `Claude Code`, `MCP`, `API`.
- Use screenshots placeholders as `[截图：展示什么]` when screenshots are needed but not provided.
- Keep the ending restrained. Return to the solved pain point instead of forcing a life lesson.

## Forbidden Moves

- Do not invent personal experience, logs, test results, numbers, errors, screenshots, or user quotes.
- Do not expose secrets, tokens, API keys, private account identifiers, or hidden operational details.
- Do not use empty openings like "随着技术的发展", "在当今时代", "众所周知".
- Do not turn a tool into a万能 solution. Always mention fit and limits when relevant.
- Do not use marketing overclaim words like "神器", "颠覆", "神级", unless the user explicitly asks for a hype style.
- Do not write a fake "踩坑提醒" if no pitfall evidence exists.
- Do not auto-assemble drafts from unrelated writing assets unless the user explicitly asks for that workflow.
- Do not switch into campaign, brand-copy, or corporate announcement voice.
- Do not add emoji.

## Output Shape

For full articles, output:

1. Title: 15-30 Chinese characters when possible, with a concrete promise, number, pain point, or first-person hook.
2. Opening: 2-5 short paragraphs from a real pain point or operating scene.
3. Body: use the selected article type structure.
4. Pitfalls: concrete problems and fixes for tutorials and field reports.
5. Summary: 3-5 bullets stating what readers can take away.
6. Closing judgment: 1-3 restrained sentences.

For outlines, output:

1. Working title.
2. Core thesis.
3. Reader pain point.
4. Section plan with 5-8 sections.
5. Missing material list.

## Self-Check

Before finalizing, verify:

- The opening starts from a real pain point or scene.
- The article has a clear spine, not a pile of notes.
- Every factual claim is supported by provided material or marked as unknown.
- Every important technical concept has a plain explanation or analogy.
- Steps are reproducible where the article promises a tutorial.
- Pitfalls are concrete and evidence-backed.
- The tone is direct and practical, not sermon-like.
- The article avoids hype and empty abstractions.
- No secrets or sensitive details are exposed.
- The ending is useful and restrained.

## References

- Read `references/style-profile.md` for extracted Nemo voice rules, evidence from existing local articles, reusable mechanisms from `nemo-writer`, and anti-patterns.
