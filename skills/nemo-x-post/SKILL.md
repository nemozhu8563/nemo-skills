---
name: nemo-x-post
description: |
  Nemo 的中文 X 短推写作 Skill。用于把知识库片段、文章素材、项目复盘、原始想法、评论观点、社会观察或已有初稿，诊断并改写成适合发 X/Twitter 的中文短推。适合处理“帮我写一条推”“按我的风格改短推”“诊断这个推文文案”“给我几个 X 版本”“这个观点怎么发 X”等请求。不要用于长文写作、公众号文章、纯小红书标题、真实发布到 X、无材料虚构经历或需要自动点击发布的任务。
---

# Nemo X 短推写作

## Overview

Use this skill to turn real material into a Chinese X short post in Nemo's public voice: grounded, direct, scene-first, and resistant to AI-polished structure.

This skill is for writing and editing. It does not post to X. Use `baoyu-post-to-x` for browser-assisted publishing.

When the request depends on Nemo's voice, read the shared style profile from `../nemo-writer/references/style-profile.md` first. Then read `references/short-post-rules.md`.

## Inputs

Work with the material the user provides. Do not invent facts, personal experience, screenshots, numbers, or source claims.

Useful inputs:

- Raw idea, note, clipping, article fragment, project record, comment, screenshot text, or draft.
- Target platform: usually X/Twitter.
- Desired shape: one final post, several versions, diagnosis only, or edit from existing draft.
- Constraints: words to keep, angle to avoid, boundary statements, privacy limits.

If the user only gives a vague topic, produce a short angle diagnosis first instead of pretending there is enough material for a finished post.

## Workflow

1. Identify the post type:
   - `方法判断型`: AI tools, project reviews, content systems, business judgment, workflow lessons.
   - `情绪判断型`: bullying, relationship, family, social rules, victims, shame, pressure, anger.
   - `实时提醒型`: incidents, tool risks, version accidents, security warnings, temporary avoidance.
2. Extract one main conflict. 一条短推只服务一个主要传播目标。
3. Choose the structure:
   - 方法判断型: real friction -> central judgment -> mechanism -> usable reminder.
   - 情绪判断型:刺痛场景 -> 第一反应 -> memorable contrast/metaphor -> boundary -> cold judgment.
   - 实时提醒型: background -> risk -> where to check -> temporary handling -> current boundary.
4. If there is a draft, diagnose before rewriting: what is strong, what is AI-like, what should be cut.
5. Write the requested output. Default to one polished post unless the user asks for versions.
6. Run the self-check before finalizing.

## Voice Rules

- Start from a concrete scene, pain, conflict, or first reaction.
- Let emotion arrive before abstract reasoning on social or relationship topics.
- 把结构藏在语气里，不要让每一段都像一个整齐步骤。
- Prefer human phrasing over mechanism labels.
- Keep paragraphs short and easy to post.
- Use contrast sparingly. Do not chain “不是 A，而是 B”.
- Preserve necessary boundaries, especially when topics involve violence, self-harm, revenge, legal risk, or public accusation.
- For technical or project posts, keep Nemo's practical friend voice: real operation, clear judgment, reproducible detail where available.

## Forbidden Moves

- Do not write a polished analysis report when the user needs a short post.
- Do not use AI structure phrases such as “本质上”, “真正的问题是”, “如果只解释成”, “核心在于”, “底层逻辑” unless the user's draft intentionally uses them.
- Do not use webby filler such as “太浅了”, “说小了”, “扎心了” as a substitute for real judgment.
- Do not force every sentence into a polished catchphrase.
- Do not add emoji.
- Do not encourage private revenge, doxxing, harassment, vigilantism, or self-harm.
- Do not fabricate first-person experience or pretend a source was read.

## Output Shapes

For diagnosis:

1. `判断`: can post / needs edit / should re-angle.
2. `强处`: 1-3 concrete points.
3. `问题`: 1-3 concrete points.
4. `改法`: the next smallest rewrite move.

For rewrite:

- Output only the post unless the user asks for diagnosis too.
- Stay under 300 Chinese characters by default.
- No Markdown headings inside the post.

For versions:

- Give 3-5 versions with distinct intent, such as 克制、有怒气、普通人发推、文学感、传播更尖锐.
- Add one short note per version only if the user asks for comparison.

## Self-Check

Before finalizing, verify:

- Did the post type match the material?
- Is there one clear conflict instead of several competing points?
- Does the opening sound like a human reaction or a scene, not a thesis sentence?
- For 情绪判断型, did emotion arrive before reasoning?
- Are abstract claims grounded in visible human situations?
- Is the language free of obvious AI scaffolding?
- Are legal, violence, self-harm, and accusation boundaries handled without diluting the point?
- Did the output avoid invented facts and fake personal experience?

## References

- Read `references/short-post-rules.md` for detailed structures, anti-patterns, and examples.
- Read `../nemo-writer/references/style-profile.md` when the user asks for Nemo style, or when the post comes from technical practice, AI tools, projects, workflows, content systems, or personal-IP judgment.
