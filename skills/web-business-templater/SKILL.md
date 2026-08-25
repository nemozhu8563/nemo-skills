---
name: web-business-templater
description: "Extract a reusable local site template from a proven grow Web business by separating framework, per-project configuration, and independent content, removing project-specific branding, sources, telemetry IDs, domains, and secrets, then verifying a second-product substitution before marking templated. Use for Web 站点模板化、框架配置内容三层分离、抽站点模板、第二产品替换测试、动态导航 sitemap SEO、template_readiness；not for templating an unvalidated site, copying product-specific content, publishing a template, mass-cloning sites, or treating a working codebase as reusable proof."
---

# Web Business Templater

把第一个已验证 Web 业务中真正通用的基础设施提炼出来，同时显式排除项目专属品牌、内容、证据、域名和统计身份。

## Dependency And Scope

- 机器契约来自同级必需依赖 `web-business-pipeline`；优先使用 `WEB_BUSINESS_PIPELINE_SKILL_DIR`，其次解析 `../web-business-pipeline` 或项目 `.agents/skills/web-business-pipeline`。
- 写入前必须运行中央 `scripts/pipeline.py status --project-dir <project-dir>` 和 `validate`。依赖不存在、当前状态不匹配或中央校验失败时停止。
- 起点：`grow` 且第一个站点已有人工批准的有效数据决策。
- 终点：进入 `templated`。
- 本 Skill 所有产物：`用户指定的本地模板目录`、`analytics-snapshot.json 中的 template_readiness`、`中央 transition 追加的 decision-log.md`。不得直接编辑 `pipeline-state.json`；授权和状态只能由中央 CLI 写入。

## Router Rules

- framework, configuration and content layers are explicit
- project-specific assets, claims, sources, domains and telemetry IDs are excluded
- navigation, routes, SEO and sitemap derive from config/content
- a second-product substitution test is reviewed before approval
- 完整全链路或当前阶段不明时，回到 `$web-business-pipeline`；机会发现仍由匹配的上游方法负责，只有 Steam/Roblox 游戏找词才使用 `$game-keyword-radar`。
- 同一项目同一时间只允许一个阶段 Skill 写产物；发现上游契约错误时停止并交回总编排器。

## Compact Workflow

1. 运行中央 `status`/`validate`，确认当前为 `grow`；未跑通、hold 或 retire 的项目不能因代码可复制就模板化。
2. 盘点站点并分三层：框架层（布局、组件、生成逻辑）、配置层（产品名、主题、导航、官方链接、SEO、locale）、内容层（各页事实、文案、翻译和来源）。先记录边界再改代码。
3. 把产品名、主题、官方链接、导航、SEO 标题/描述等硬编码集中到配置；页面、路由、导航、结构化数据和 sitemap 从配置/内容动态生成。只做当前模板所需的最小重构。
4. 从模板中移除或参数化产品专属品牌、文案、截图、价格/数值、source IDs、domain、GSC/GA property、广告 ID、环境配置和任何 secret。内容层不得作为示例默认发布。
5. 在隔离的本地目标中用第二个虚拟/无商标产品配置做 substitution test：验证只改配置与内容即可切换，框架无需项目专属改动；运行 build、links、assets、SEO、sitemap 和残留扫描。
6. 展示 reusable scope、product-specific exclusions、测试结果和仍需手工替换项。用户明确批准后写入 template_readiness 的 approved/by/at 字段。
7. 运行 `gate --target templated` 并转移。不得因为模板目录存在就通过，也不因本地通过自动发布、创建仓库或复制第二个真实站。

中央命令形态：

```bash
python3 "$WEB_BUSINESS_PIPELINE_SKILL_DIR/scripts/pipeline.py" status --project-dir <project-dir>
python3 "$WEB_BUSINESS_PIPELINE_SKILL_DIR/scripts/pipeline.py" validate --project-dir <project-dir>
```

## Output Contract

- 框架/配置/内容三层边界清单
- 无产品身份和凭证的本地模板
- 第二产品 substitution test 与残留扫描证据
- 批准后的 template_readiness 和 templated gate
- 最终回复分开列出：已验证事实、推断、人工决定、missing evidence、当前状态和下一阶段。
- 文件存在、模型判断、计划执行或授权记录都不能冒充 gate 通过、真实执行或线上回读。

## Write And Action Boundary

- 只写用户明确指定的本地模板目录和项目模板就绪记录。
- 保留原站可运行，重构需小步、可回滚并通过现有测试。
- 不创建远端仓库、不发布 package、不部署第二站、不购买域名。
- 网络：none; public repository publication or package release is out of scope。
- 交互：required for reusable scope, product-specific exclusions, destination, and final substitution-test approval。
- 临时日志、缓存和浏览器会话不得写进站点项目、Skill 目录或 Obsidian vault。

## Non-goals

- 把首个尚无数据的站点提前抽成框架
- 连同项目内容、品牌、来源和统计 ID 一起复制
- 以模板化为理由自动批量建十个站
