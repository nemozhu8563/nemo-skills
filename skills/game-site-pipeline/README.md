# game-site-pipeline

`game-site-pipeline` 是热词游戏站的本地总编排与治理层。它接收 `game-keyword-radar` 中已经过人工确认的一个候选，把十个阶段 Skill 串在同一套可恢复状态机上。

它不会替你调用注册商、部署平台或 Google 产品。所有对外动作都先形成独立授权记录，实际执行和真实回读仍由对应工具或人工完成。

## 适用边界

- 适用：已经有候选，准备做页面矩阵、内容站、上线门禁和第 7/14 天复盘。
- 先用 `game-keyword-radar`：仍在找 Steam/Roblox 游戏词、查 Trends/Semrush 或筛候选。
- 不适用：普通企业站、纯 SEO 问答、自动买域名或“一键发布”。

## 阶段 Skill

| 入口 | 负责内容 |
|---|---|
| `game-candidate-lock` | 人工确认候选并生成不可变锁 |
| `game-site-planner` | SERP/竞品研究、页面矩阵和页面功能契约 |
| `game-site-evidence` | 逐页双来源与 claim 级证据 |
| `game-site-builder` | 页面实现和内容清单 |
| `game-site-qa` | 本地构建、链接、资产、视觉、内容审核和部署就绪 |
| `game-site-launch` | 逐项授权的 Git/部署/域名/DNS 与线上回读 |
| `game-site-telemetry` | GSC/GA、索引、观察窗口和复查 |
| `game-site-growth` | `grow`、`hold`、`retire` 数据决策 |
| `game-site-templater` | 可复用基础设施与游戏专属内容拆分 |
| `game-page-expander` | `grow` 后的有限批量扩页及重新上线编排 |

完整路由和扩页复用规则见 `references/skill-suite.md`。

## 你可以直接这样说

- “候选词已经确认了，按全链路做到本地验收。”
- “继续上次的游戏站项目，告诉我下一关还缺什么证据。”
- “用第 14 天 GSC 数据决定 grow、hold 还是 retire。”

## 安装 Installation

该仓库目录是 canonical source。按项目约定，以 symlink 暴露具体 Skill 目录，不要复制：

```bash
ln -s /absolute/path/to/nemo-skills/skills/game-site-pipeline \
  /absolute/path/to/project/.agents/skills/game-site-pipeline
```

确认链接目标中可直接读取 `SKILL.md`。

当前是本地 Skill，不执行公开安装。未来发布后才使用类似命令：

```bash
npx skills add <owner/repository> --skill game-site-pipeline
```

## 快速开始

先从雷达候选整理一份输入：

```bash
cp templates/candidate-input.example.json /tmp/candidate.json
# 编辑 /tmp/candidate.json，删除 example_only 并替换全部示例值
python3 scripts/pipeline.py init \
  --project-dir /absolute/path/to/game-site-project \
  --candidate-file /tmp/candidate.json \
  --approved-by Nemo \
  --confirm-key game:example-game \
  --rationale "人工确认该主词进入建站验证"
```

之后把对应模板复制到项目根目录，填入真实证据，再逐关检查：

```bash
python3 scripts/pipeline.py status --project-dir /absolute/path/to/game-site-project
python3 scripts/pipeline.py gate --project-dir /absolute/path/to/game-site-project --target planned
python3 scripts/pipeline.py transition --project-dir /absolute/path/to/game-site-project \
  --to planned --actor Nemo --reason "页面矩阵和功能契约已复核"
python3 scripts/pipeline.py validate --project-dir /absolute/path/to/game-site-project
```

## 项目产物

| 文件 | 用途 |
|---|---|
| `candidate-lock.json` | 不可变主词、来源报告、资格证据和平台身份 |
| `pipeline-state.json` | 当前状态、历史和逐项授权 |
| `page-matrix.json` | 一页一意图、关键词归属和页面功能契约 |
| `evidence-pack.json` | 来源、逐页覆盖和 claim 级证据 |
| `content-manifest.json` | 页面文件、来源、claim、审核和内容哈希 |
| `launch-report.json` | 本地检查、域名残留、部署、回读与回滚 |
| `analytics-snapshot.json` | GSC/GA 配置回读、观察窗口和增长决策 |
| `decision-log.md` | 人类可读的锁词、授权、转移和撤销记录 |

机器字段定义在 `schemas/`，可复制骨架在 `templates/`。CLI 使用 Python 标准库，不安装依赖。

## 授权记录

下面的命令只记录权限，不会部署：

```bash
python3 scripts/pipeline.py authorize \
  --project-dir /absolute/path/to/game-site-project \
  --action deployment \
  --confirm deployment \
  --granted-by Nemo \
  --scope "仅部署当前已验证 revision 到 preview 项目" \
  --user-instruction "部署这个版本到 preview"
```

记录后，把输出的 `authorization_id` 放入 `launch-report.json`。域名购买、DNS、Git push、部署、GSC、GA 和广告申请互不替代，必须逐项授权。

## 退出码

- `0`：命令成功或门禁通过。
- `2`：输入、契约、门禁或文件系统检查失败。

命令输出统一为 JSON，便于其他 Agent 或 CI 读取。

## 包验证

```bash
python3 -m unittest discover -s tests -v
python3 /absolute/path/to/qiaomu-meta-skill/scripts/validate_skill.py .
python3 /absolute/path/to/qiaomu-meta-skill/scripts/trigger_eval.py . \
  --output reports/trigger-eval.json
python3 /absolute/path/to/qiaomu-meta-skill/scripts/release_check.py . \
  --phase local --run-tests
```

## Troubleshooting

- `candidate-lock.json changed after initialization`：主词锁已被修改。保留旧项目，新建另一个项目重新锁词。
- `keyword cannibalization`：两个页面共享 intent key、主词或别名；合并页面或重新划分意图。
- `missing artifact`：按 `status` 输出补齐当前下一关需要的 JSON，不要直接改状态。
- `unknown authorization`：报告引用的外部动作没有活跃授权；不要伪造 ID，先取得该具体动作的新授权。
- `missing evidence: no valid GSC performance data`：只排查技术项并记录第 7/14 天复盘，不能进入 grow 或 retire。
