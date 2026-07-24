# Eval: Concept Explainer Contract

This fixture guards against a polished but interchangeable concept explainer.

## Case: Stronger Model Does Not Make Skills Obsolete

### Prompt Shape

Write a Nemo-style concept explainer from these documented materials:

- OpenAI's Prompting and GPT-5.6 guidance says to remove redundant process instructions while retaining context, constraints, approval boundaries, and success criteria.
- The author is writing the article in an Obsidian workflow where facts need source records, unverified model data cannot be added, and a draft must not be published automatically.
- The reader asks whether GPT-5.6 makes long prompts and Superpowers-like Skills unnecessary.

### Expected Writer Behavior

The draft should:

- open from the documented writing scene or the reader's concrete confusion, then use it to separate generic model reasoning from local rules;
- explain what can be removed from a Prompt and what still needs to be made explicit;
- use one primary decision device. A comparison table and a decision checklist may coexist only when they answer different questions;
- give Superpowers a bounded use case instead of declaring it universally obsolete or universally required;
- end with a concrete change to the reader's next task, not a restatement that Prompt and Skill both matter.

### Failure Signals

The writer output fails if it:

- opens with a finished thesis and never returns to a source-backed scene or confusion;
- claims GPT-5.6 knows private project rules, permissions, or acceptance criteria;
- stacks a task-routing table and a multi-question checklist that both decide when to use Prompt, Skill, or planning;
- finishes with a generic summary card that only repeats the central conclusion;
- invents benchmark numbers, first-hand tests, screenshots, or user quotes.
