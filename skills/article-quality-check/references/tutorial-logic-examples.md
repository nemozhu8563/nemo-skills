# Tutorial Operation Logic Examples

Use this reference when checking tutorials, setup guides, how-to articles, workflow guides, and step-by-step technical explainers.

Tutorial logic has two layers:

- Argument logic: claims, reasons, examples, boundaries, and consequences.
- Operation logic: step order, section ownership, reader action, and success criteria.

Both must be smooth. A sentence can sound natural and still break operation logic.

## Tutorial Operation Logic Check

For each section, identify:

1. Reader action: what should the reader do or confirm here?
2. Allowed content: what belongs in this section?
3. Success check: what proves this section is complete?
4. Drift: does any sentence explain article arrangement or belong to another section?
5. Reader perspective: does the sentence speak to the reader's next action, or to the author's article plan?
6. Audience name: does the draft use the article's actual reader name instead of a vague label?

## Labels

Use these labels when they apply:

- `操作逻辑不通`: the section flow or step order does not work.
- `步骤归属错位`: a sentence or action belongs in another section.
- `章节目标漂移`: the section starts serving another goal.
- `教程自我说明`: the sentence explains article arrangement instead of reader action.
- `读者视角漂移`: the sentence is written from the author's plan instead of the reader's current action.
- `读者称呼不准`: the draft uses a vague audience label when a clearer reader name is available.
- `桥接句补丁`: a smooth transition was added to patch structure, but it adds no useful operation.

Severity calibration:

- `教程自我说明`, `读者视角漂移`, and `步骤归属错位` are `强信号` by default in tutorials. They must be handled, not softened into style advice.

## Calibration Cases

### Case 1: Arrangement Commentary In A Login Section

Input:

```text
装好以后，先确认登录状态和基本环境。这里不需要立刻让 Codex 处理真实项目；真正的测试放到后面的空目录烟雾测试。
```

Expected diagnosis:

```text
问题：操作逻辑不通 / 教程自我说明 / 步骤归属错位
原因：当前节应该只确认登录状态和基本环境，后半句在解释文章安排，并把后面 smoke test 的任务提前带入。
建议：删掉后半句，只保留“装好以后，先确认登录状态和基本环境。”
```

### Case 2: Smoke Test Mixed Into Login Check

Input:

```text
登录完成后，先让 Codex 解释当前目录里有什么，确认它能正常发起一个低风险任务。
```

Expected diagnosis:

```text
问题：步骤归属错位
原因：这是任务执行验证，不是登录状态检查。
建议：登录节只保留登录状态、账号状态、环境检查；任务验证移到烟雾测试节。
```

### Case 3: Article Planning Instead Of Operation Boundary

Input:

```text
这个复杂配置后面再讲，第一篇不展开。
```

Expected diagnosis:

```text
问题：教程自我说明 / 桥接句补丁
原因：这句话解释作者如何安排文章，没有告诉读者当前应该怎么处理。
建议：改成操作规则，例如“第一次安装先保留默认配置；确认能打开和登录后，再处理复杂配置。”
```

### Case 4: Article Plan And Vague Audience Name

Input:

```text
第一篇里，CLI 不是主要查看入口。对普通读者来说，优先看 Codex App 和官方 usage 页面就够了。
```

Expected diagnosis:

```text
问题：教程自我说明 / 读者视角漂移 / 读者称呼不准
级别：强信号
原因：“第一篇里”是在解释文章安排，不是给读者当前动作。“普通读者”太泛，应该使用文章里的目标读者称呼。
建议：改成“新手查用量时，先看 Codex App 和官方 usage 页面就够了；CLI 暂时不用管。”
```

## Required Review Behavior

When checking a tutorial, do not stop at wording polish. Explicitly state whether the draft has:

- argument logic problems,
- operation logic problems,
- or both.

Article-arrangement commentary is not a minor style issue in tutorials. Flag it as a strong operation-logic problem and give a reader-facing replacement.
