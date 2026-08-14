# game-candidate-lock

人工确认合格候选并生成不可变主词锁。它是 `game-site-pipeline` 套件的阶段入口，不复制中央状态机。

## 适用边界

- 起点：合格雷达候选，且当前项目尚无 `candidate-lock.json`。
- 终点：创建 `candidate_locked`。
- 不适用：替用户从多个候选中静默选赢家；把一次热度尖峰或模型判断当作合格证据；为修正候选而覆盖 candidate-lock.json。

## 你可以直接这样说

- “把这个雷达合格候选做 candidate lock，我精确确认 game:arcane-odyssey”
- “核对 Steam app ID 后生成 candidate-lock.json，批准人写 Nemo”
- “从 game-keyword-radar 候选进入建站，先做主词人工确认和平台身份锁定”

## 安装 Installation

本 Skill 与中央依赖都应从 canonical repository 以 symlink 暴露，不能复制目录：

```bash
ln -s /absolute/path/to/nemo-skills/skills/game-candidate-lock /absolute/path/to/project/.agents/skills/game-candidate-lock
ln -s /absolute/path/to/nemo-skills/skills/game-site-pipeline /absolute/path/to/project/.agents/skills/game-site-pipeline
```

当前是本地套件。未来单独发布后，发现命令才会类似：

```bash
npx skills add <owner/repository> --skill game-candidate-lock
```

## 工作方式

1. 读取雷达报告和候选行，逐项核对：Trends 为 `rising`、Semrush Volume 为真实正数且数据库明确、KD `<30`、真实长尾词 `>=10`、SERP 为 `open|mixed`、可靠来源 `>=2`。
2. 保留稳定的 `game:<slug>` key，并至少记录一个平台身份。Steam 使用 app ID；Roblox 使用 universe/place 等能够消歧的稳定 ID。相同标题不能合并成同一平台实体。
3. 若当前用户指令没有精确确认候选 key、批准人和具体理由，展示 key、名称、平台 ID 与资格证据后提出一个阻塞式确认问题；用户回答前不得运行 `init`。
4. 从中央模板 `templates/candidate-input.example.json` 准备输入，替换全部示例值并删除 `example_only`。保留真实 `source_report`；缺失字段不估算。

## 输出

- 不可变、可哈希的候选身份
- 由用户原话支持的批准记录
- 中央 CLI 的 validate/status 结果
- 下一步 planner handoff 与所有 missing evidence

## 验证

```bash
python3 /absolute/path/to/qiaomu-meta-skill/scripts/validate_skill.py .
python3 /absolute/path/to/qiaomu-meta-skill/scripts/trigger_eval.py . --output reports/trigger-eval.json
python3 /absolute/path/to/qiaomu-meta-skill/scripts/export_skill_ir.py . --output reports/skill-ir.json
```

## Troubleshooting

- 找不到中央 CLI：确认 `GAME_SITE_PIPELINE_SKILL_DIR` 或同级 `game-site-pipeline` symlink 可读；不要复制 CLI。
- 当前状态不匹配：运行中央 `status`，回到 `$game-site-pipeline` 重新路由。
- gate 失败：保留当前状态，修正报告中的具体 evidence 缺口后重试。
- 用户要求越过边界：只执行当前已明确授权且属于本 Skill 的动作，其他动作交给对应阶段。

## 风险边界

- 只在用户指定的新项目目录创建三类中央产物。
- 不得改写雷达历史、候选报告或已有锁；换词时创建新项目。
- 不执行搜索、购买、Git、部署、DNS、统计配置或广告动作。
