# X 短推规则

This reference turns the old X short-post prompt into reusable execution rules.

## Types

### 判断立场型

Use for a durable `03_Notes` synthesis, a well-supported personal view, or a current event where Nemo has a clear position. It does not need to come from a published article, a project recap, or first-hand operational experience.

Structure:

```text
可争论判断 -> 一个让判断站得住的具体理由/反例/分配关系 -> 这会改变什么 -> 一句有压力的收束
```

Good signs:

- The first sentence gives readers something they can agree with, oppose, or extend; it does not introduce an article or tool.
- It carries one claim, not a compressed article outline.
- The note behind it supplies the reasoning, but the post only needs the decisive hinge, not a full proof chain.
- It has reply surface: a reader can bring their own counterexample, local experience, or opposing criterion.

Reject or re-angle when:

- The draft mainly says “我写了一篇/做了一个工具”，but the reader cannot see a broader judgment.
- It is a neutral explainer, a project changelog, or an article abstract wearing short paragraphs.
- It gives a conclusion without a visible reason, scene, contrast, or stake.

### 方法判断型

Use for AI tools, project reviews, content systems, business judgment, workflow lessons, and technical personal-IP fragments.

Structure:

```text
真实摩擦 -> 中心判断 -> 机制解释 -> 可执行提醒
```

Good signs:

- The post exposes a real friction, not a generic opinion.
- The middle completes a理解替换: from the surface problem to the variable that changes the result.
- The ending gives a judgment standard, smallest action, or useful warning.
- Visible actions appear when possible: 剪藏, 检索, 改提示词, 跑脚本, 看日志, 改字段, 发推, 复盘, 沉淀模板, 复用素材.

### 情绪判断型

Use for bullying, relationship, family, social rules, victims, shame, pressure, anger, and other大众议题 where over-structuring kills the post.

Do not force:

```text
机制解释 -> 可执行提醒
```

Prefer:

```text
刺痛场景 -> 第一反应 -> 有记忆点的对照/比喻 -> 压住边界 -> 留一句冷判断
```

The job is not to finish the whole theory. The job is to make the reader feel: “这句话说出了我隐约知道但没说出来的东西。”

### 实时提醒型

Use for incidents, tool risks, version accidents, security warnings, and temporary avoidance.

Structure:

```text
背景 -> 风险 -> 看哪里 -> 临时处理 -> 边界/当前状态
```

Short-post body should include enough for a reader to judge risk and act. Put full evidence chains in comments, long-form notes, or follow-ups.

## Nemo Account Fit

Nemo is not a pure technical account and not a pure emotional-opinion account.

- Technical, AI, knowledge base, automation, and content systems build credibility and differentiation.
- Social rules, wealth, relationship, emotion, family, and desire can be broader entry points.
- Both lanes should share the same bottom style: real observation, hard judgment, mechanism awareness, reusable reminder.

Do not use topics where there is no observation入口. A hot social claim without a source, scene, or usable judgment should be rejected or rewritten as a question.

## Quote 评论型

Use when a quote tweet already carries the event, original video, source claim, or public figure's words. The quote provides the factual hook; Nemo's body must add a judgment that makes the quote worth reading.

Structure:

```text
直接进入判断 -> 谁得到什么 / 谁承担什么 -> 为什么两者会割裂 -> 一句可争论的收束
```

Rules:

- Do not repeat the quoted author, event, or summary in the body unless a detail is essential to understand Nemo's judgment.
- Do not open with “这段视频/这条推文/某某说了什么”；读者已经能从 quote 看到。
- Prefer a concrete distribution conflict over a list of consequences. For infrastructure, ask who gets revenue, capacity, convenience, or control, and who carries land, water, noise, power, price, risk, or administrative obligations.
- When beneficiaries and bearers are different groups, name that mismatch plainly. Avoid empty labels such as “制度性问题” or “值得反思”.
- Keep attribution in the quote itself. Do not write another person's experience as Nemo's first-hand experience.
- Do not force a solution when the value is exposing an unresolved conflict. End on the judgment, not a generic call to action.

Example direction:

Weak:

```text
数据中心会带来电网、土地和噪声问题。
```

Stronger:

```text
当受益者可以跨区域配置资源，承担者却必须留在原地，“支持发展”很容易变成一笔没有对价的义务。
```

### 判断句的落地法

For social, infrastructure, business, and public-policy quote posts, do not stop at “有代价”. Complete the sentence with a visible allocation:

```text
谁获得权利、收益、便利或控制 -> 谁承担成本、风险、约束或义务
```

The second half should remain concrete enough that a reader can disagree with it. “权利和义务没有落在同一群人身上” works only after the post has shown what each side actually receives or bears.

## Chinese Texture

Use:

- Short sentences, pauses, repetition, turns, and口气.
- Human phrases before mechanism labels.
- Concrete human scenes before abstract claims.

Prefer:

- “他大概已经求救过很多次了”
- “死后才被看见”
- “还活着、还记账、还要说法”

Avoid:

- “这反映了求助机制失效”
- “社会对无害受害者的纪念机制”
- “该事件暴露出制度性问题”

Good Chinese does not have to be symmetrical. It needs direction, pressure, and breath.

## Common Anti-Patterns

- Writing every post as a mini essay.
- Opening with “真正的问题是”, “本质上”, “核心在于”, “底层逻辑”.
- Using “太浅了”, “说小了”, “扎心了” instead of making the reader feel the point.
- Turning a social topic into a clean argument table.
- Making every paragraph progress too neatly.
- Removing pain, anger, hesitation, and coldness to make the idea clearer.
- Adding a forced “可执行建议” to a post whose value is emotional recognition.

## Output Defaults

- One post: under 300 Chinese characters.
- No emoji.
- No fake data.
- No invented personal experience.
- No Markdown heading inside the post.
- If versions are requested: 3-5 versions with distinct intent.

## Example Direction

Weak:

```text
这反映了社会对受害者追责机制的缺失。
```

Stronger:

```text
别把求助和追责的路都堵死了，最后又问他为什么只剩下自毁。
```

Weak:

```text
这个问题不能只从性格软弱解释。
```

Stronger:

```text
我第一反应不是他为什么不反抗，而是他大概已经求救过很多次了。
```
