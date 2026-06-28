---
name: nemo-writer
description: |
  Nemo 的中文技术长文写作 Skill。用于把真实笔记、项目记录、操作日志、踩坑过程、工具体验、开源项目研究整理成 Nemo 风格的技术实验文章、教程、实战复盘或概念讲解；也用于从真实技术实践、AI 工具使用、项目记录、内容创作或独立创业观察中，提炼技术型个人 IP 文章、业务认知复盘和项目判断。触发场景包括：写技术文章、按我的风格写、把笔记整理成文章、把实战过程写成复盘、解释 MCP/Skill/Agent/Workflow 等 AI 工具概念、从项目实践写个人判断、为 Nemo 风格公众号长文拟定或筛选标题。公众号标题必须服务点击和阅读理由，同时守住个人 IP 的真实判断边界；不要套用小红书标题公式、硬转成交，或用“克制”掩盖标题没有吸引力。不要用于无材料的虚构创作、纯小红书短帖、品牌宣传文案、自动拼装稿或需要编造亲身经历的任务。
---

# Nemo 技术老友写作

## Overview

Use this skill to write like Nemo: a practical technical friend explaining something he actually tried. The writing should feel clear, direct, grounded in real operations, and useful enough that readers can copy the workflow or understand the project judgment behind it.

The voice is not a literary persona. It is a tested working style: real pain point first, plain explanation second, reproducible process third, then pitfalls and a restrained judgment.

Before writing from personal style, read `references/style-profile.md` when the task depends on voice, examples, or anti-patterns.

For WeChat/公众号 longform titles, title selection, or publish-ready title checks, read `references/wechat-longform-title.md`. This applies especially when the user asks for a title, asks whether a title is good enough, or the article is a technical personal-IP essay.

## Inputs

Prefer these inputs. Continue with available material, but never invent missing facts.

- Topic: what the article is about.
- Source material: notes, links, local files, command logs, screenshots, project records, issue notes, or draft fragments.
- Target type: technical experiment, tutorial, concept explainer, field report, workflow breakdown, or technical personal-IP essay.
- Audience: technical beginner, AI tool user, indie builder, or operator.
- Constraints: what must not be revealed, including secrets, tokens, private account data, internal URLs, and personal details.

If source material is too thin, produce an outline or ask for the minimum missing inputs. Do not write as if an unverified test happened.

## Article Types

Choose one primary type before drafting. First decide whether the article is a **技术实验** or a **技术型个人 IP** essay.

Technical experiments are practical/reproducible articles. Use them when the reader should understand how a tool, project, workflow, or experiment was run and how to reuse the path.

1. Tutorial: pain point -> tool/solution -> prerequisites -> steps -> pitfalls -> summary.
2. Concept explainer: confusion -> plain analogy -> relationship map -> real usage case -> summary.
3. Field report: why I did it -> chosen approach -> actual process -> problems -> result -> judgment.
4. Workflow breakdown: messy old process -> new default order -> commands or steps -> when to use it -> what changes.
5. Technical personal-IP essay: real technical/project scene -> old misunderstanding -> new mechanism -> key case -> my projects -> next decision.

For technical personal-IP essays, read `references/technical-personal-ip.md` before drafting.

## Writing Workflow

1. Extract the real pain point, scene, or triggering moment in 1-3 concrete sentences.
2. Decide the mode:
   - Use technical experiment when the article teaches or reviews a reproducible tool, project, workflow, or operating process.
   - Use technical personal-IP when the article is grounded in real technical/project practice but the point is a business, product, content, or identity judgment.
3. For technical personal-IP or WeChat longform, identify the reader entrance before drafting: what the right reader is searching, stuck on, curious about, afraid of missing, or seeing in a current hotspot.
4. For AI_Media, WeChat longform, or technical personal-IP drafts inside the Obsidian vault, run a short expression-asset fit pass before writing the opening and ending:
   - Search `04_Projects/AI_Media/80_Assets/hooks.md`, `arguments.md`, and `quotes.md` for topic-adjacent openings, argument shapes, judgment sentences, and ending moves.
   - Use `04_Projects/AI_Media/00_System/写作范式.md` and `平台特征.md` for opening and ending rules when available.
   - Borrow only the useful structure or move, not the wording. If no asset fits the topic, say briefly that the asset pass was skipped or produced no usable match; do not force an unrelated hook.
5. Decide the article type and write a one-sentence thesis.
6. For technical experiments, build the spine: problem -> solution -> process -> pitfalls -> result -> judgment.
7. For technical personal-IP essays, load `references/technical-personal-ip.md` and use its spine.
8. Explain every important technical term with plain language or one everyday analogy.
9. Include reproducible details when the article promises a practical path: commands, paths, options, configs, screenshots placeholders, or exact decision criteria when available.
10. Add a pitfalls section with 2-5 specific problems for tutorials and field reports. If the material has no real pitfalls, say so and do not fabricate them.
11. End sections with short judgment sentences that clarify why the detail matters.
12. Run the self-check before final output.

## Voice Rules

- Start from a real pain point or first-person operating context, not from a dictionary definition.
- Use first person when the material supports it: "我遇到", "我后来", "我选择".
- Keep paragraphs short, usually 2-5 lines.
- Use headings, ordered lists, tables, and code blocks when they make the article easier to follow.
- Prefer concrete verbs: 装好, 跑通, 接入, 验证, 重启, 写入, 归档, 拆开.
- Use direct calibration patterns sparingly. Avoid repeated "不是 A，而是 B" logic; prefer scene, consequence, cost, boundary, or next-action sentences.
- Avoid over-neat enumeration chains. When a sentence stacks several abstract repairs or judgments, convert it into user feedback, a process sequence, or one concrete symptom.
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
- Do not auto-assemble drafts from unrelated writing assets. For local asset-bank use, borrow only topic-fit structure and record the fit or skip; never let the asset drag the article away from the real material.
- Do not switch into campaign, brand-copy, or corporate announcement voice.
- Do not add emoji.

## Output Shape

For full articles, output a complete draft by default. Only output an outline, excerpt, title set, or revision advice when the user explicitly asks for that shape.

For technical experiments, output:

1. Title: generate and choose with `references/wechat-longform-title.md` when the target is WeChat/公众号 longform; otherwise use 15-30 Chinese characters when possible, with a concrete promise, number, pain point, or first-person hook.
2. Opening: 2-5 short paragraphs from a real pain point or operating scene.
3. Body: use the selected article type structure.
4. Pitfalls: concrete problems and fixes for tutorials and field reports.
5. Summary: 3-5 bullets stating what readers can take away.
6. Closing judgment: 1-3 restrained sentences.

For technical personal-IP essays, output the shape defined in `references/technical-personal-ip.md`.

For outlines, output:

1. Working title.
2. Core thesis.
3. Reader pain point.
4. Section plan with 5-8 sections.
5. Missing material list.

## Self-Check

Before finalizing, verify:

- The opening starts from a real pain point or scene.
- For AI_Media, WeChat longform, or technical personal-IP drafts in the vault, the opening and ending were checked against topic-fit local assets or an explicit no-fit/skip note was made.
- The article has a clear spine, not a pile of notes.
- The selected mode is correct: technical experiment for practical/reproducible work, technical personal-IP for project-grounded judgment.
- For WeChat/公众号 longform, the title creates a concrete click reason from the article's tension or judgment, without turning the piece into generic growth-copy, sales-copy, or Xiaohongshu bait.
- For technical personal-IP or WeChat longform, the reader entrance is clear, but the main judgment still comes from Nemo's real practice rather than demand-chasing.
- The article repays the click with real practice, pitfalls, effects, judgment change, or boundaries instead of generic commentary.
- The article is sincere in the strong sense: it does not manipulate readers, does not make claims Nemo would not endorse, and still gives both reader and creator a legitimate gain.
- Every factual claim is supported by provided material or marked as unknown.
- Every important technical concept has a plain explanation or analogy.
- Steps are reproducible where the article promises a tutorial.
- Pitfalls are concrete and evidence-backed.
- The tone is direct and practical, not sermon-like.
- The article avoids hype and empty abstractions.
- The draft does not fall into repeated calibration phrases such as "不是 A，而是 B".
- The draft avoids over-neat enumeration chains and repeated reframing; where possible, lists of abstract fixes become scene, feedback, process, cost, or consequence.
- No secrets or sensitive details are exposed.
- The ending is useful and restrained.

## References

- Read `references/style-profile.md` for extracted Nemo voice rules, evidence from existing local articles, reusable mechanisms from `nemo-writer`, and anti-patterns.
- Read `references/technical-personal-ip.md` when the article should turn real technical practice, AI workflow, project work, content work, or entrepreneurial observation into a Nemo-style personal judgment article.
- Read `references/wechat-longform-title.md` when creating, selecting, or checking titles for WeChat/公众号 longform and Nemo technical personal-IP articles.
