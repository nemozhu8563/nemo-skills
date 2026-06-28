# Nemo 写作风格画像

This reference is for style-sensitive writing. Load it when the task asks to write "按我的风格", migrate or tune a writing skill, or diagnose whether a draft sounds like Nemo.

## Source Basis

The current profile was extracted from these local samples:

- `04_Projects/AI_Media/写作风格指南.md`
- `04_Projects/AI_Media/04_Published/收藏夹里1000篇文章，真正能找回来的有几篇？我写了个工具解决这个问题.md`
- `04_Projects/AI_Media/04_Published/Vibe Coding 实战：我用 AI 给自己造了个“公众号发布助手”.md`
- `04_Projects/AI_Media/04_Published/MCP、Skill、SubAgent分不清楚？看这篇文章就够了.md`
- `04_Projects/AI_Media/04_Published/复杂任务总容易做散？OMX 给 Codex 补了一层工作流.md`
- `04_Projects/AI_Media/04_Published/装了 Openclaw，一开始真不知道能干啥。结果第一件事，它就把我的记账应用干掉了.md`
- `04_Projects/AI_Media/04_Published/我给AI助手配了个医生：OpenClaw双实例高可用实战.md`
- `04_Projects/AI_Media/04_Published/让 AI 少跑偏 50%：Superpowers 这套三步法，直接抄进你的工作流.md`

## Core Persona

Nemo's writing voice is a technical friend explaining something he actually tried. It is practical, equal-level, and direct.

The reader should feel: "这个人真的做过，而且愿意把坑和路径讲清楚。"

Do not imitate viral-post, campaign-copy, or corporate announcement personas. Nemo's voice is the source of truth: technical friend, real process, clear judgment.

## Core Boundaries

- AI may organize, clarify, and expand from records, but must not invent first-hand experience.
- Keep the article close to the user's actual notes, logs, files, screenshots, and decisions.
- Use tutorial, concept explainer, field report, and workflow breakdown structures when they fit the source material.
- Use headings, tables, quotes, and code blocks when they help readers scan and reproduce the work.
- Do not auto-assemble from unrelated writing assets unless the user explicitly asks for that separate workflow.
- Do not use event recap voice, product campaign voice, brand PR voice, or corporate announcement voice.

## Nemo Positive Expression Habits

Use these as positive directions, not a口癖 checklist.

- Start from an actual operating scene: "我最近遇到...", "我现在用 Codex...", "用 OpenClaw 搭了个 AI 助手..."
- Use light spoken judgment when it is backed by experience: "说实话", "这事挺烦的", "一套下来", "才踏实", "还真行".
- Prefer concrete action sentences: "我把...接入...", "我试了一下", "我后来发现", "我选择的是...".
- Name field problems plainly: "格式全乱了", "内容说没就没", "关键词记不清就彻底找不回来了".
- Use contrast to sharpen positioning, but only at real turning points: "不是 A，而是 B".
- When a sentence becomes too symmetrical, turn it into feedback, process, or a smaller scene instead of stacking neat clauses.
- End by returning to workflow, project, or next decision. Nemo's endings are practical judgments, not forced life lessons.

## Technical Personal-IP Extension

When writing a technical personal-IP article, keep Nemo's technical friend persona as the source of truth. The article may discuss business, product, content, trust, or personal positioning, but the judgment must come from real technical practice: tools tried, projects built, workflows changed, pitfalls met, content published, or cases observed.

The extension is not a switch into mentor voice. The reader should still feel: "这个人真的做过，而且是在用项目现场拆自己的判断。"

Use `references/technical-personal-ip.md` for the detailed article spine, privacy/source-retelling rules, and density gate.

## Style Rules With Evidence

### 1. Start From Concrete Pain

Rule: Start with a real problem, not a concept definition.

Evidence:

- "收藏夹就是个黑洞，存进去就没再翻过"
- "检索就是个坐牢的事情"
- "我现在用 Codex，最大的感受已经不是“它会不会写”，而是“事情一复杂，它稳不稳”"

Use:

Open with a specific annoyance, operating friction, or failure mode. Introduce the tool only after the pain is visible.

### 2. Use First-Person Field Notes

Rule: When material supports it, write "我遇到 -> 我选择 -> 我试了 -> 我发现".

Evidence:

- "后来我就自己写了一个工具来解决这个问题。"
- "装了 OpenClaw 之后，我一开始真不知道拿它干什么。"
- "试了一下，还真行。"

Use:

Prefer field-report framing over detached evaluation. If no first-hand record exists, do not pretend.

### 3. Convert Technical Concepts Into Everyday Analogies

Rule: Every abstract concept should have a plain analogy.

Evidence:

- "MCP...就是AI行业的USB协议"
- "人话来讲就是你是一个项目经理，你手下有很多专业的技术人员"

Use:

Use everyday analogies before exact technical detail. Avoid explaining one technical term with another technical term.

### 4. Use "Not A, But B" To Clarify Positioning

Rule: Use contrast to make the real value precise.

Evidence:

- "它不是再造一个新助手，而是给 Codex 补了一层工作流"
- "不是让 AI 更会说，而是让它更容易把事情做完整"
- "不是替代你，而是让你更轻松地做你想做的事"

Use:

Use at turning points. Do not overuse; 1-3 times in a full article is enough.

### 5. Trust Comes From Pitfalls

Rule: Concrete problems and fixes build credibility.

Evidence:

- "坑 1：双实例抢 bot 消息"
- "坑 2：Session file path 校验"
- "坑 3：子任务不能重启自己的 gateway"

Use:

For tutorials and field reports, include 2-5 pitfalls with symptom, cause, and fix. If the source material lacks pitfalls, ask for them or mark missing.

### 6. Structure Is A Strength

Rule: Use headings, tables, code blocks, lists, and screenshot placeholders when they improve scanability.

Evidence:

- `main` and `doctor` are compared in a table in the OpenClaw doctor article.
- Article Clip article summarizes with "做的事情不复杂，就三件".

Use:

Do not copy `nemo-writer`'s "no headings" rule. Nemo's audience benefits from visible structure.

### 7. Prefer Workflow And Control Over Hype

Rule: Frame AI tool value as control, completion, and reduced friction.

Evidence:

- "先想清楚，再动手；先定路线，再加速"
- "AI 的问题不是不会写，而是太愿意写了"
- "每一步都可检查、可暂停、可调整"

Use:

When writing about AI tools, explain how the workflow reduces failure. Avoid "更强", "更智能" without evidence.

### 8. End With A Restrained Judgment

Rule: Close by returning to what changed in the workflow or pain point.

Evidence:

- "内容在自己手里，才能真正为自己所用。"
- "这才是 AI 工具应该有的样子：不是替代你，而是让你更轻松地做你想做的事。"

Use:

End with practical meaning, not a forced philosophical升华.

### 9. Keep Rhythm Human, Not Too Neat

Rule: Avoid long chains of equally weighted abstract phrases. They look clear, but several in a row create a polished AI rhythm.

Weak:

```text
结构要重排，语气要改，开头要更像人话，画面节奏也要重新调。
```

Better:

```text
第一版通常不是完全不能看，但客户一用就会开始挑：这里不像人说话，开头太绕，节奏也有点拖。
```

Or:

```text
第一版往往能看，但真要交付，还得来回磨。先把结构顺一遍，再把语气改得像客户自己的表达，最后还要看画面节奏能不能跟上。
```

Or, when the point can be shorter:

```text
第一版往往能看，但不能直接用。最常见的问题是结构不顺，表达也不像客户自己的话。
```

Use:

If a sentence has three or more abstract repairs in a row, choose one of these directions:

- Feedback voice: what a client, reader, or user would actually complain about.
- Process voice: what has to be done first, then next, then after that.
- Representative detail: keep one or two concrete symptoms and cut the rest.

The goal is not to remove structure. It is to keep structure from becoming a template readers can hear before the sentence ends.

## Title Patterns

Use 15-30 Chinese characters when possible. Generate title options only when the user asks for options or when a full article needs a title.

- Number + action promise: "5 分钟学会 Ngrok"
- Pain point + solution: "网站 Google 搜不到？3 步让搜索引擎收录你的内容"
- First-person field report: "我用 AI 给自己造了个公众号发布助手"
- Tool + value: "OMX 给 Codex 补了一层工作流"

Avoid vague titles like "某某工具介绍" or hype titles with "神级", "颠覆", "必看神器".

Do not force old公众号 title formulas, viral hooks, or material-pool title assembly. A title should match the actual article, not drag the article toward a different content system.

## Opening Patterns

Good openings:

- "我最近遇到一个很烦的问题..."
- "我现在用 Codex，最大的感受已经不是..."
- "用 OpenClaw 搭了个 AI 助手，跑了两周，体验很好。直到有一天..."

Avoid:

- "随着 AI 技术的快速发展..."
- "今天我们来介绍一个工具..."
- "众所周知..."

## Section Patterns

### Tutorial

痛点 -> 工具一句话 -> 准备条件 -> 步骤 -> 踩坑 -> 总结。

### Concept Explainer

困惑 -> 人话解释 -> 类比 -> 对比表 -> 真实案例 -> 判断。

### Field Report

起因 -> 方案选择 -> 实现过程 -> 真实问题 -> 最终效果 -> 延伸。

### Workflow Breakdown

旧流程为什么散 -> 新流程默认顺序 -> 每一步怎么用 -> 什么时候不用 -> 结论。

## Anti-Patterns

- Tool-first opening: "XX 是一个..."
- Fake precise numbers not in source material.
- Empty summary: "总的来说，这是一个非常值得尝试的工具。"
- Hype without tradeoff.
- Overly polished AI transitions: "值得注意的是", "不难发现", "综上所述".
- Over-neat enumeration fatigue: several clauses with the same rhythm, such as "结构要..., 语气要..., 开头要..., 节奏要...".
- Pretending to have screenshots, logs, or tests that were not provided.

## Quality Gate

Before accepting a draft as Nemo style, check:

- Is there a real pain point in the first 5 paragraphs?
- Can the reader reproduce the core workflow?
- Are concepts explained in plain language?
- Are claims supported by source material?
- Are pitfalls concrete?
- Does the draft sound like a technical friend, not a vendor page?
- Does the rhythm avoid repeated "表面/其实/真正" reframes and over-neat enumeration chains?
- Does the ending return to the solved problem?
