# game-site-planner

研究 SERP 后产出不蚕食的页面矩阵和功能契约。它是 `game-site-pipeline` 套件的阶段入口，不复制中央状态机。

## 适用边界

- 起点：初次建站为 `candidate_locked`；扩页模式仅由 `$game-page-expander` 在 `grow` 中调用。
- 终点：初次建站进入 `planned`；扩页模式保持 `grow`。
- 不适用：批量抓取或复制竞品内容；在功能契约之外发明 UI 元素；因为模板能生成就增加语言或页面。

## 你可以直接这样说

- “研究这个已锁定游戏的 SERP，做页面规划和 page-matrix.json”
- “给攻略站建立一页一意图的页面矩阵，并先写功能契约”
- “检查 primary keyword、别名和 intent key 是否会关键词蚕食”

## 安装 Installation

本 Skill 与中央依赖都应从 canonical repository 以 symlink 暴露，不能复制目录：

```bash
ln -s /absolute/path/to/nemo-skills/skills/game-site-planner /absolute/path/to/project/.agents/skills/game-site-planner
ln -s /absolute/path/to/nemo-skills/skills/game-site-pipeline /absolute/path/to/project/.agents/skills/game-site-pipeline
```

当前是本地套件。未来单独发布后，发现命令才会类似：

```bash
npx skills add <owner/repository> --skill game-site-planner
```

## 工作方式

1. 运行中央 `status` 和 `validate`。初次模式只接受 `candidate_locked`；扩页模式必须由 `$game-page-expander` 明确传入当前 `grow` 批次。
2. 围绕锁定主词做只读 SERP/竞品研究，记录 query、地区/语言、检查时间、结果 URL、页面类型、搜索意图和未满足需求。竞品只用于信息架构判断，不复制文案、品牌或视觉。
3. 先为每页写功能契约：用户目标、允许字段、允许动作/按钮、允许状态和明确非目标。契约没有的字段、按钮、状态、卡片或导航不得进入后续原型和实现。
4. 写 `page-matrix.json`：每页一个稳定 `page_id`、唯一 `primary_keyword`、别名、`intent_key`、locale 和 search intent。规范化后主词、别名或 intent key 冲突时合并或重划，不继续。

## 输出

- 可追溯 SERP/竞品意图摘要
- 页面级功能契约
- 无关键词蚕食的 page-matrix.json
- planned gate 或 expansion validation 结果

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

- 只写页面矩阵及用户明确要求的本地规划说明。
- 不修改候选锁、证据包、页面实现、状态文件或远端系统。
- 研究是只读；登录、验证码、付费墙或不可控页面出现时停止并报告。
