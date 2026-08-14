# game-page-expander

在 grow 后按真实机会有限批量扩页并重走上线观察门。它是 `game-site-pipeline` 套件的阶段入口，不复制中央状态机。

## 适用边界

- 起点：`grow`，且增长决定包含有效 GSC/关键词机会；单篇手动流程已被证明。
- 终点：本地扩页期间保持 `grow`；重走 QA、launch、telemetry 后回到 `observing`。
- 不适用：关键词一换就复制同一篇内容；没有真实来源也批量填充数值、技能或打法；一开始就写自动抓取/生成脚本替代尚未跑通的手工流程。

## 你可以直接这样说

- “这个站已经 grow，规划至少十个内页并按同类几个一批扩页”
- “用真实长尾机会批量做内页，先人工审核首批五页”
- “扩页后重走 QA、launch 和 telemetry，再回 observing”

## 安装 Installation

本 Skill 与中央依赖都应从 canonical repository 以 symlink 暴露，不能复制目录：

```bash
ln -s /absolute/path/to/nemo-skills/skills/game-page-expander /absolute/path/to/project/.agents/skills/game-page-expander
ln -s /absolute/path/to/nemo-skills/skills/game-site-pipeline /absolute/path/to/project/.agents/skills/game-site-pipeline
```

当前是本地套件。未来单独发布后，发现命令才会类似：

```bash
npx skills add <owner/repository> --skill game-page-expander
```

## 工作方式

1. 运行中央 `status`/`validate`，确认当前为 `grow`，并从已批准 growth decision 中提取真实 query/page/长尾机会。hold、retire、无 valid data 或单篇尚做不好时停止。
2. 先列至少 10 个候选内页：稳定 page ID、对应搜索词、用户问题、页面类型、预期独特信息和内部链接位置。去重 intent；不能仅换名字复制。
3. 写一份可复用的同类内页生产契约/提示：固定结构、必备字段、来源要求、格式、禁止编造、待确认标记和项目内容格式。它是生产约束，不是事实来源。
4. 以同类 2–3 个页面为一批调用 `$game-site-planner` expansion mode 更新矩阵，再用 `$game-site-evidence` 建双来源和 claim 证据，最后用 `$game-site-builder` 生成差异化内容与 manifest；每批失败即停。

## 输出

- 至少十个内页的意图清单和有限批次计划
- 可复用但证据受限的页面生产契约
- 更新后的矩阵、证据、内容、QA 和人审结果
- 重发/telemetry handoff，或最终 observing gate

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

- 本 Skill 负责编排扩页批次；每类产物仍由对应阶段 Skill 写入。
- 没有精确授权时只做到本地 QA，不推送、不部署、不改 DNS。
- 不修改候选锁，不扩展 hold/retire 项目，不自动抓取受限来源。
