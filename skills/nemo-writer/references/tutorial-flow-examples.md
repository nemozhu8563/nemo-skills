# Tutorial Flow Examples

Use this reference when writing or revising tutorials, setup guides, and step-by-step workflow articles.

The goal is not to collect pretty sentences. The goal is to prevent smooth prose from breaking the reader's operation flow.

## Section Contract

Before drafting a tutorial section, define:

- Reader action: what the reader should do or confirm in this section.
- Allowed content: what belongs in this section.
- Success check: what proves the section is complete.
- Out of scope: what belongs in another section.

Every paragraph should serve the current reader action. If a sentence only explains why the article is arranged a certain way, delete it or convert it into an operation rule.

## Bad And Better Examples

### Tutorial Arrangement Commentary

Bad:

```text
装好以后，先确认登录状态和基本环境。这里不需要立刻让 Codex 处理真实项目；真正的测试放到后面的空目录烟雾测试。
```

Problem:

The second sentence explains article arrangement. It does not help the reader complete the current section.

Better:

```text
装好以后，先确认登录状态和基本环境。
```

Principle:

If a sentence says "这里不需要", "后面再讲", "真正的测试放到后面", "第一篇里", "本文先不", "这篇不展开", or "不放进第一篇", treat it as a strong failure signal. Tutorial sections should say what the reader does now.

### Step Belongs To Another Section

Bad:

```text
登录完成后，先让它解释当前目录里有什么，确认 Codex 能发起低风险任务。
```

Problem:

This is a smoke test, not a login check. It belongs in the smoke-test section.

Better:

```text
登录完成后，检查当前登录状态：

codex login status
```

Principle:

Login checks confirm identity and environment. Task execution belongs in smoke tests or first-task sections.

### Boundary As Operation Rule

Bad:

```text
这个复杂配置后面再讲，第一篇不展开。
```

Problem:

The sentence talks about article planning, not reader action.

Better:

```text
第一次安装先保留默认配置；确认能打开和登录后，再处理复杂配置。
```

Principle:

When a boundary is necessary, phrase it as an operation rule: what to keep, skip, confirm, or postpone.

### Reader Perspective And Audience Name

Bad:

```text
第一篇里，CLI 不是主要查看入口。对普通读者来说，优先看 Codex App 和官方 usage 页面就够了。
```

Problem:

The first sentence talks about article arrangement. "普通读者" is vague when the article is already written for beginners.

Better:

```text
新手查用量时，先看 Codex App 和官方 usage 页面就够了；CLI 暂时不用管。
```

Principle:

Use the reader name that matches the article, such as "新手", "第一次安装 Codex 的人", or the user's specified audience. Do not replace it with a vague label like "普通读者".

## Final Tutorial Check

Before accepting a tutorial draft, verify:

- Each section has one reader action.
- Each step belongs to the current section.
- Success checks match the section action.
- Argument logic is clear: claims have reasons and boundaries.
- Operation logic is clear: the reader can follow the order without being pulled into future sections.
- The section speaks from the reader's next action, not from the author's article plan.
- Audience labels match the article's actual reader.
