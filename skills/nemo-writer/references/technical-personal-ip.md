# Nemo 技术型个人 IP 写作

This reference is for articles that are grounded in real technical practice, AI workflows, project work, content work, or entrepreneurial observation, but whose real purpose is a personal judgment about product, business, content, or positioning.

Use this only after `SKILL.md` has routed the article to technical personal-IP mode. Do not load it for ordinary practical tutorials unless the user explicitly wants a business or personal-IP reflection.

## When To Use

Use this mode when the source material looks like one of these:

- A technical project or AI workflow changed how Nemo thinks about business, product, content, or personal positioning.
- A conference, group discussion, client case, or project review triggered a concrete judgment about how Nemo should build.
- The article is not mainly teaching readers to reproduce a workflow, but explaining what Nemo realized after doing or observing real work.
- The article needs to connect tools, projects, content, and business links without becoming a meeting recap or business sermon.

Do not use this mode when the article's main promise is reproducible operation. That belongs to technical experiment mode.

## Article Spine

Build the article around one clear transformation:

```text
现场触发
-> 我以前怎么理解
-> 现在发现哪里不对
-> 一个具体案例说明机制
-> 回到我自己的项目
-> 接下来我会怎么调整
```

The article should still feel like Nemo: real scene first, concrete action second, judgment third. The business or personal-IP insight must grow out of actual projects, tools, workflows, pitfalls, or content practice.

## Topic Gate

Before drafting, check whether the article sits in the overlap of reader entrance, Nemo's judgment, and real evidence.

Use this rule:

```text
入口让给读者，判断留给自己。
用户需求决定入口，Nemo 的真实判断决定正文主线，实践证据决定能不能发布。
```

Do not reduce this to "write whatever users are stuck on." User demand is only the entrance. The article still needs Nemo's own reason to care and real material that can repay the click.

Classify the topic before drafting:

| Situation | Action |
| --- | --- |
| Nemo wants to write it, readers have a visible entrance, and there is real material | Prioritize for WeChat longform. |
| Nemo wants to write it, but the reader entrance is weak | Keep it as X/thread/notes, or find a real entrance before making it a WeChat article. |
| Readers are stuck, but Nemo has no practice or judgment | Do not write as first-hand personal-IP. Run the experiment, gather sources, or make it a research note. |
| Readers are stuck, but Nemo disagrees with the demand | Write a counter-judgment only if the article explains why the question itself is flawed. |
| Nemo wants to express a judgment, but the public entry is unclear | Connect it to a hotspot, repeated mistake, tool pitfall, cost, failed default action, or decision boundary. |

For WeChat personal-IP longform, big hotspots and repeated user questions are valid entrances because they reveal attention, search, and cognitive demand. They are not the content itself. The article must turn the entrance into Nemo's own use, pitfall, effect, judgment change, and boundary.

Use this spine for demand-aware personal-IP pieces:

```text
读者入口
-> 真实触发
-> 我以前怎么理解
-> 现在发现哪里不对
-> 真实使用 / 踩坑 / 案例
-> 效果或判断变化
-> 适用边界
-> 我接下来怎么调整
```

## Core Moves

### 1. Start From A Real Trigger

Open with a scene, sentence, project moment, or operational friction.

Good directions:

- "我听到这里的时候，被狠狠地震了一下。"
- "我最近发现一个挺尴尬的问题。"
- "我折腾了这么多项目以后，才发现自己真正没跑通的是另一件事。"

Avoid abstract openings like:

- "从更深层次来看..."
- "这背后反映出..."
- "在当前 AI 时代..."

### 2. Name The Old Misunderstanding

The old misunderstanding should be specific, not a slogan.

Useful shapes:

- "我以前会觉得，只要 AI 够强，我就能靠工具效率跑出优势。"
- "我以前很容易焦虑内容没有流量，以为内容的目标就是带来更多曝光。"
- "我以前会把一个项目做出来，当成事情已经完成了。"

Do not repeat the old misunderstanding in five different ways. State it once, then move to mechanism.

### 3. Explain The New Mechanism

Technical personal-IP articles need mechanism, not only attitude.

Mechanism examples:

- AI is a lever; it only compounds a business that already has a support point.
- Content is not only a traffic machine; it is also a trust surface that lets others inspect your ability.
- A project is a product even before it earns money, because it can accumulate workflow, judgment, assets, audience trust, and reusable experience.

Explain why the mechanism changes decisions. If it does not change what Nemo will do next, it is probably decoration.

### 4. Use Cases As Proof, Not Ornament

Cases should prove the mechanism. They should not be inserted as anecdotes after the conclusion is already finished.

When using a case, answer at least two of these:

- What was the assumed product?
- Who was supposed to pay?
- What was not verified yet?
- What cost was taken on too early?
- What did the case reveal about product chain, profit model, trust, or conversion path?

For example, a奶茶甜品店 case is not about judging that specific store. It can show what happens when a project has many categories, people, and upfront cost before the core product has been verified.

### 5. For Product/Pricing Essays, Find The Real Cost Unit

When writing about AI product pricing, do not lock the article on the visible artifact too early, such as a price page, pricing table, subscription tier, or SaaS package. Those are downstream surfaces. First identify the cost, responsibility, or delivery boundary that makes pricing hard.

Good anchors:

- A failed generation: "重新生成一次，到底该不该扣钱？"
- A hidden process cost: "用户买的是最后能用，平台付成本却发生在每一次尝试里。"
- A responsibility boundary: "失败重生成、修改轮次、材料质量、新增需求，分别算谁的成本？"
- A first sale decision: "先用项目制交付一小批结果，验证修改、验收和材料边界。"

Avoid anchoring the whole article on:

- "价格页写得越完整越容易跑偏"
- "不要先做价格页"
- "99 还是 199"
- "套餐怎么分"

These can appear as consequences, but they should not become the center of the argument unless the source material is actually about UI/copywriting for the pricing page.

Better transformation:

```text
Weak: 价格页写得越完整，越容易把自己带偏。
Better: 如果失败重生成、修改轮次、材料质量和新增需求都没算清楚，99 和 199 都只是猜。
```

For AI generation products, treat call/token/generation-based pricing as a valid default, not as a strawman. The sharper question is when the user is buying API/tool usage and when they are buying a deliverable process. If the article criticizes call-based pricing, it must explain which responsibility the product has promised beyond calls.

### 6. Compress Repeated Reframing

Do not restate the same reframe in three consecutive forms. A common weak pattern is:

```text
这件事看起来很小。
它表面上是在问 A。
但我后来发现，它其实是在问 B。
真正的问题是 C。
```

Use one clean turn instead:

```text
这件事看起来是在问“重新生成一次算不算额度”。
但它真正暴露出来的，是 AI 生成类产品最难算的一笔账：用户买的是“最后能用”，平台的成本却发生在每一次尝试里。
那失败的这一轮，到底该谁承担？
```

When the current sentence already contains the reframe, delete the extra "表面/其实/真正" sentence. The reader only needs one turn from scene to mechanism.

## Nemo Positive Voice Habits

Use Nemo's natural direction as a positive style target:

- Real operation/context openings: "我最近遇到...", "我听到这里的时候...", "我后来发现..."
- Light spoken judgment: "说实话", "这事挺烦的", "才踏实", "还真行"
- Concrete actions: "我把...接入...", "我试了一下", "我选择...", "我拆开看..."
- Field problems: "格式全乱了", "内容说没就没", "一套下来..."
- Contrast at turning points sparingly. If several paragraphs use "不是 A，而是 B", rewrite with scene, cost, consequence, or a concrete question instead.
- Restrained endings: return to what changes in the workflow, project, content strategy, or next decision.

Do not turn these into a口癖 checklist. They are directions for rhythm and judgment.

## Privacy And Source Retelling

Do not expose source-processing traces in the article.

Avoid phrases like:

- "截图里看到"
- "公开来讲"
- "不能公开讲"
- "不方便公开"
- "我现在发给你的图片"

Use natural public narration instead:

- "后来我在创业群里看到有人聊起..."
- "分享里有一个案例让我印象很深。"
- "有人提到一个项目，一开始看起来很热闹..."

When material includes sensitive revenue links, private cashflow, client information, internal URLs, account data, or details the user says cannot be public:

- Do not name the sensitive link.
- Do not hint at it with awkward defensive wording.
- Convert it into a public-safe judgment, such as "我还没有把手上的项目串成一条清晰变现链路" or "这件事提醒我，项目不能只停留在经验堆叠，还要有可验证的业务闭环。"

The reader should see the insight, not the redaction.

## Density Gate

Every paragraph should add at least one new function:

- Claim: a new judgment or position.
- Example: a concrete case or scene.
- Mechanism: why the thing works that way.
- Boundary: when the point applies or does not apply.
- Consequence: what happens if the point is ignored.
- Decision: what Nemo will do differently.

If several paragraphs all say "AI 不是业务" or "内容不是流量" without adding mechanism, case, boundary, consequence, or decision, cut or deepen them.

## Output Shape

For full articles, default to this structure:

1. Title: first-person hook, concrete tension, or practical judgment.
2. Opening: the triggering scene or sentence.
3. Old misunderstanding: what Nemo used to believe and why it made sense at the time.
4. New mechanism: what changed after the source event or project observation.
5. Case: one or two concrete cases that prove the mechanism.
6. My projects: how this maps back to Nemo's current tools, sites, content, workflow, or business chain.
7. Next decision: what Nemo will adjust next.

Use headings when they help scanability, but the article should still read as one coherent personal field note, not as a report.

## Self-Check

Before accepting the draft:

- Is the reader entrance clear: search need, hotspot, repeated mistake, visible cost, or practical curiosity?
- Does the main line still come from Nemo's own judgment instead of simply chasing demand?
- Does the article repay the entrance with real practice, pitfalls, effect, judgment change, or boundary?
- Does the article start from a real trigger rather than a broad concept?
- Is the old misunderstanding specific and not repeated endlessly?
- Does the new mechanism explain why decisions change?
- Do cases prove the mechanism instead of decorating it?
- Does the article return to Nemo's actual projects, tools, content, or business chain?
- Are privacy-sensitive details converted into public-safe judgment?
- Does every paragraph add a new function?
- Is the sincerity strong enough: not treating readers as fools, not using claims Nemo would not endorse, and giving readers a real benefit while accumulating Nemo's judgment, trust, or opportunity?
- Does the ending state what changes next, without forcing a life lesson?
