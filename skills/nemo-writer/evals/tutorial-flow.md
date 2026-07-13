# Eval: Tutorial Flow Contract

This lightweight fixture guards against smooth tutorial prose that breaks operation logic.

## Case: Login Section Explains Future Smoke Test

### Prompt Shape

Revise this tutorial section:

```md
## 04 登录和健康检查

装好以后，先确认登录状态和基本环境。这里不需要立刻让 Codex 处理真实项目；真正的测试放到后面的空目录烟雾测试。
```

### Expected Writer Behavior

The revised draft should:

- keep the section focused on login status and environment checks,
- remove article-arrangement commentary,
- not mention that the real test happens later,
- not introduce task execution or smoke-test actions into the login section.

### Expected Revision

```md
## 04 登录和健康检查

装好以后，先确认登录状态和基本环境。
```

### Failure Signals

The writer output fails if it keeps or recreates sentences like:

- `这里不需要立刻让 Codex 处理真实项目`
- `真正的测试放到后面`
- `后面再做烟雾测试`
- `不放进第一篇`

The writer output also fails if it asks the reader to run a task in the login section.

## Case: Usage Section Uses Article Plan And Vague Audience

### Prompt Shape

Revise this tutorial sentence for a beginner Codex article:

```md
第一篇里，CLI 不是主要查看入口。对普通读者来说，优先看 Codex App 和官方 usage 页面就够了。
```

### Expected Writer Behavior

The revised draft should:

- remove article-arrangement wording such as `第一篇里`,
- replace vague audience wording such as `普通读者` with the article's reader name,
- keep the useful operation rule: check usage in Codex App and the official usage page first,
- avoid over-explaining why CLI is not covered.

### Expected Revision

```md
新手查用量时，先看 Codex App 和官方 usage 页面就够了；CLI 暂时不用管。
```

### Failure Signals

The writer output fails if it keeps or recreates:

- `第一篇里`
- `本文先不`
- `这篇不展开`
- `普通读者`
