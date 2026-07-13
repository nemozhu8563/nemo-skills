# Eval: Tutorial Operation Logic Check

This lightweight fixture verifies that the checker treats tutorial operation flow as logic, not mere style.

## Case: Login Section Explains Future Smoke Test

### Input

```md
## 04 登录和健康检查

装好以后，先确认登录状态和基本环境。这里不需要立刻让 Codex 处理真实项目；真正的测试放到后面的空目录烟雾测试。
```

### Expected Diagnosis

The checker should flag this as:

- `操作逻辑不通`
- `教程自我说明`
- `步骤归属错位`

### Required Reason

The diagnosis should say:

```text
04 节的读者动作是确认登录状态和基本环境。后半句在解释文章安排，并把后面烟雾测试的任务提前带入当前节。
```

### Required Fix

```md
## 04 登录和健康检查

装好以后，先确认登录状态和基本环境。
```

### Failure Signals

The checker output fails if it only labels the issue as:

- wording polish,
- AI flavor,
- tone problem,
- sentence not concise.

It must identify the operation-logic failure.

## Case: Usage Section Uses Article Plan And Vague Audience

### Input

```md
第一篇里，CLI 不是主要查看入口。对普通读者来说，优先看 Codex App 和官方 usage 页面就够了。
```

### Expected Diagnosis

The checker should flag this as:

- `教程自我说明`
- `读者视角漂移`
- `读者称呼不准`
- `强信号`

### Required Reason

The diagnosis should say:

```text
“第一篇里”是在解释文章安排，不是站在读者当前动作上说话；“普通读者”太泛，应该换成文章里的目标读者称呼，例如“新手”。
```

### Required Fix

```md
新手查用量时，先看 Codex App 和官方 usage 页面就够了；CLI 暂时不用管。
```

### Failure Signals

The checker output fails if it:

- treats this only as weak wording polish,
- keeps `第一篇里`,
- keeps `普通读者` when the target reader is beginner/new user,
- does not mark the issue as `强信号`.
