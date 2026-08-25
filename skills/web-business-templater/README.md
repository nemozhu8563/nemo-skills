# web-business-templater

把跑通站点拆成框架、配置和内容三层模板。它是 `web-business-pipeline` 套件的阶段入口，不复制中央状态机。

## 适用边界

- 起点：`grow` 且第一个站点已有人工批准的有效数据决策。
- 终点：进入 `templated`。
- 不适用：把首个尚无数据的站点提前抽成框架；连同项目内容、品牌、来源和统计 ID 一起复制；以模板化为理由自动批量建十个站。

## 你可以直接这样说

- “把这个 grow Web 业务做三层分离并抽成本地模板”
- “抽出产品配置，让导航、SEO 和 sitemap 动态生成”
- “用第二个虚拟产品做替换测试，确认 template_readiness 再进入 templated”

## 安装 Installation

本 Skill 与中央依赖都应从 canonical repository 以 symlink 暴露，不能复制目录：

```bash
ln -s /absolute/path/to/nemo-skills/skills/web-business-templater /absolute/path/to/project/.agents/skills/web-business-templater
ln -s /absolute/path/to/nemo-skills/skills/web-business-pipeline /absolute/path/to/project/.agents/skills/web-business-pipeline
```

当前是本地套件。未来单独发布后，发现命令才会类似：

```bash
npx skills add <owner/repository> --skill web-business-templater
```

## 工作方式

1. 运行中央 `status`/`validate`，确认当前为 `grow`；未跑通、hold 或 retire 的项目不能因代码可复制就模板化。
2. 盘点站点并分三层：框架层（布局、组件、生成逻辑）、配置层（产品名、主题、导航、官方链接、SEO、locale）、内容层（各页事实、文案、翻译和来源）。先记录边界再改代码。
3. 把产品名、主题、官方链接、导航、SEO 标题/描述等硬编码集中到配置；页面、路由、导航、结构化数据和 sitemap 从配置/内容动态生成。只做当前模板所需的最小重构。
4. 从模板中移除或参数化产品专属品牌、文案、截图、价格/数值、source IDs、domain、GSC/GA property、广告 ID、环境配置和任何 secret。内容层不得作为示例默认发布。

## 输出

- 框架/配置/内容三层边界清单
- 无产品身份和凭证的本地模板
- 第二产品 substitution test 与残留扫描证据
- 批准后的 template_readiness 和 templated gate

## 验证

```bash
python3 /absolute/path/to/qiaomu-meta-skill/scripts/validate_skill.py .
python3 /absolute/path/to/qiaomu-meta-skill/scripts/trigger_eval.py . --output reports/trigger-eval.json
python3 /absolute/path/to/qiaomu-meta-skill/scripts/export_skill_ir.py . --output reports/skill-ir.json
```

## Troubleshooting

- 找不到中央 CLI：确认 `WEB_BUSINESS_PIPELINE_SKILL_DIR` 或同级 `web-business-pipeline` symlink 可读；不要复制 CLI。
- 当前状态不匹配：运行中央 `status`，回到 `$web-business-pipeline` 重新路由。
- gate 失败：保留当前状态，修正报告中的具体 evidence 缺口后重试。
- 用户要求越过边界：只执行当前已明确授权且属于本 Skill 的动作，其他动作交给对应阶段。

## 风险边界

- 只写用户明确指定的本地模板目录和项目模板就绪记录。
- 保留原站可运行，重构需小步、可回滚并通过现有测试。
- 不创建远端仓库、不发布 package、不部署第二站、不购买域名。
