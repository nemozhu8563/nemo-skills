# Game Keyword Radar Skill

面向“生财航海－热词游戏站”的本地找词 Skill：从 Steam / Roblox 获取中腰部候选，比较历史动量，再通过 3ue / Semrush 补齐 Volume、KD、Intent、CPC、趋势、相关词和问题词，最终生成合并 Markdown/CSV 报告。

Google Trends 固定全球、Web 搜索、过去 30 天；整体上涨且不是单日尖峰仍是主词复核条件，候选主词与同图基线 `GPTs` 的平均热度对比仅作参考。

它不会保存账号、Cookie 或 Token，也不会把缺失 Semrush 数据估算成真实值。

## 你可以直接这样说

- “运行游戏热词雷达，比较今天和昨天的中腰部候选。”
- “从 Steam 和 Roblox 找一批中腰部游戏词，再用 3ue 的 Semrush 核验前 5 个。”
- “把这批 Semrush Volume、KD 和长尾词回填到雷达，重新出合并报告。”
- “检查哪些词已满足航海的主词复核门槛。”

## 本机安装

本机以 canonical checkout 为源，并从 Obsidian vault 建立软链接：

```bash
ln -s /Users/nemo/Documents/AI/awesome-skills/nemo-skills/skills/game-keyword-radar \
  /Users/nemo/Documents/Obsidian/.agents/skills/game-keyword-radar
```

当前是本地 Skill，不执行公开安装。未来发布后才使用类似命令：

```bash
npx skills add <owner/repository> --skill game-keyword-radar
```

## 运行

```bash
bash scripts/run-radar.sh
bash scripts/run-radar.sh --no-cdp
```

可用环境变量覆盖项目路径：

```bash
GAME_KEYWORD_RADAR_PROJECT_DIR=/path/to/game-keyword-radar bash scripts/run-radar.sh
```

## 验证

```bash
python3 /Users/nemo/Documents/AI/awesome-skills/qiaomu-meta-skill/scripts/validate_skill.py .
python3 /Users/nemo/Documents/AI/awesome-skills/qiaomu-meta-skill/scripts/trigger_eval.py . --output reports/trigger-eval.json
python3 /Users/nemo/Documents/AI/awesome-skills/qiaomu-meta-skill/scripts/export_skill_ir.py . --output reports/skill-ir.json
python3 /Users/nemo/Documents/AI/awesome-skills/qiaomu-meta-skill/scripts/release_check.py . --phase local --run-tests
```

## 数据边界

- Skill 只编排现有项目，不复制雷达核心实现。
- 3ue / Semrush 只使用可见页面和既有浏览器登录态。
- CAPTCHA、额度不足、节点异常或页面读取不稳定时降级为人工查询清单。
- 报告是候选池，不是选词结论。
- 如已完成 `GPTs` 对比，把平均值写入项目 `manual/keyword-validation.csv` 的 `google_trends_candidate_avg_30d`、`google_trends_gpts_avg_30d` 和 `google_trends_checked_at`；缺失、相等或低于 `GPTs` 都不阻断主词复核。

## Prior Art

设计时研究了 `Eronred/aso-skills` 的 `keyword-research` 与 `market-pulse`、`OpenClaudia/openclaudia-skills` 的 `semrush-research`、`nexscope-ai/Amazon-Skills` 的 `amazon-keyword-research`。采用字段分层、多来源持续信号和明确错误状态；没有复制第三方脚本，也没有采用 API Key 强依赖或 Amazon 场景绑定。

## Troubleshooting

- 项目找不到：设置 `GAME_KEYWORD_RADAR_PROJECT_DIR`。
- Steam / Roblox 失败：查看报告的数据源状态；不要把空结果当作无需求。
- Steam 与 Roblox 全部失败：查看本轮快照；日报/CSV 会保留上一份可用结果，命令退出码为 `2`。
- 3ue 页面可打开但无法稳定读取：保留查询页给用户接手，标记 `semrush_status=blocked|partial`，不要循环重试。
- 出现验证码：停止并让用户决定是否处理。
- 报告没有 Semrush 字段：检查 `manual/keyword-validation.csv` 的 `key` 是否与报告完全一致，再重跑雷达。
