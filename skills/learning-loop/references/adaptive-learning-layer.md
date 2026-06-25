# Adaptive Learning Layer

Use this reference when carrying feedback-driven learning behavior into book sessions or the lightweight topic fallback.

## Job

Adapt the next learning move to the learner's real feedback without weakening the book-first classroom loop.

This layer owns:

- extracting real learner feedback
- choosing the next teaching depth
- running lightweight topic learning when no book source exists
- keeping topic articles separate from source-backed book sessions

It does not own:

- replacing book mode when a book project already exists
- promoting notes into `03_Notes` without the Feynman gate
- turning a live book lesson into a generic article sequence

## Feedback Extraction

Before deciding the next move, read the latest available learning state:

- book mode: `progress.md`, `review_queue.md`, the latest session note, and any explicit learner feedback
- topic fallback mode: `00-学习计划.md` and the highest numbered article

Ignore template prompt lines such as:

```text
你可以写：
请写在这行下面：
1. 哪里看懂了？
2. 哪里没看懂？
3. 哪个地方想展开？
4. 这个主题和你的真实问题有什么关系？
```

Only learner-written text after the prompt counts as feedback. If there is no real feedback, ask for it. If the user explicitly says to continue anyway, continue from visible context and state that limitation in the generated article or session note.

## Learning Gradient

Choose the next move from the feedback signal:

| Learner signal | Next move |
|---|---|
| Did not understand, concepts are mixed, many questions | Lower abstraction, use a concrete example, slow down |
| Understands but feels no pull | Change angle and connect to the learner's real problem |
| Understands and asks how to apply it | Add cases, judgment rules, and practice scenarios |
| Clearly mastered it | Raise concept density or move to the next layer |
| Raises a specific question | Answer the question first, then continue the learning path |
| Feedback is thin | Keep the current difficulty and make a small step |

In book mode, map the gradient to the teacher-led progression in `classroom-facilitation.md`: `Repair`, `Apply`, `Transfer`, `Feynman`, or `Close`.

In topic fallback mode, map the gradient to the next numbered article.

## Topic Fallback Routing

Use topic fallback only when the user wants continuous learning but there is no book source, no course map, and no active book-learning project.

Target directory:

```text
04_Projects/学习/_topics/<topic-title>/
```

Structure:

```text
<topic-title>/
  00-学习计划.md
  01.md
  02.md
  assets/
```

Rules:

- Article filenames are two-digit numbers: `01.md`, `02.md`, `03.md`.
- Do not skip numbers.
- Next article number equals the largest existing article number plus one.
- Keep topic fallback as a learning article sequence, not a source-backed book classroom.
- If a real book source is later added, migrate into book mode by creating the source package, role contract, curriculum, and sessions.

## Topic Plan Template

```markdown
# <topic-title>｜学习计划

## 学习目标

<可检查的能力目标。>

## 当前进度

- 当前文章：<number>
- 最近更新：<date>
- 下一步：<next direction>

## 学习路径

1. <stage one>
2. <stage two>
3. <stage three>

## 反馈摘要

| 文章 | 用户反馈 | 下一步调整 |
|---|---|---|
| 01 | <summary> | <adjustment> |
```

## Topic Article Template

```markdown
# <number>｜<title>

## 这一篇要解决的问题

<1-3 句话说明本篇要解决什么。>

## 正文

<正文内容。>

## 小结

<3-5 条收束。>

## 下一篇预告

<下一篇准备推进到哪里。>

---

## 学习反馈

你可以写：

1. 哪里看懂了？
2. 哪里没看懂？
3. 哪个地方想展开？
4. 这个主题和你的真实问题有什么关系？

请写在这行下面：
```

## Chinese Teaching Style

- Use Chinese unless the user asks otherwise.
- Write like a clear, experienced teacher, not a textbook outline.
- Prefer direct conclusions, causes, conditions, and concrete examples.
- Avoid empty correction posture.
- Avoid repetitive contrast formulas such as `不是...而是...`, `不在于...在于...`, `不需要...需要...`, and `真正的...是...` unless analyzing the formula itself or quoting source material.
- Put spaces between Chinese and English or numbers when practical.
