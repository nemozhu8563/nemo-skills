# web-business-telemetry

核验 GSC/GA、索引与观察窗口并安排复查。它是 `web-business-pipeline` 套件的阶段入口，不复制中央状态机。

## 适用边界

- 起点：初次建站为 `deployed`；复查可从 `hold`；优化/扩展重发可从 `grow` 且 launch readback 已更新。
- 终点：初次依次进入 `telemetry_verified` 与 `observing`；复查或优化/扩展返回 `observing`。
- 不适用：把 property 创建成功说成已有流量；用零填补尚未返回的数据；在没有授权时创建 GSC/GA 或读取其他站点。

## 你可以直接这样说

- “部署完成后核验 GSC/GA property 并进入 telemetry_verified”
- “检查 sitemap 和索引，没数据就安排第 7 天与第 14 天复盘”
- “更新 analytics-snapshot.json，再把 hold 项目带回 observing”

## 安装 Installation

本 Skill 与中央依赖都应从 canonical repository 以 symlink 暴露，不能复制目录：

```bash
ln -s /absolute/path/to/nemo-skills/skills/web-business-telemetry /absolute/path/to/project/.agents/skills/web-business-telemetry
ln -s /absolute/path/to/nemo-skills/skills/web-business-pipeline /absolute/path/to/project/.agents/skills/web-business-pipeline
```

当前是本地套件。未来单独发布后，发现命令才会类似：

```bash
npx skills add <owner/repository> --skill web-business-telemetry
```

## 工作方式

1. 运行中央 `status`/`validate`，核对部署 URL、canonical origin、source revision 与 HTTP readback。初次、hold 复查和 grow 优化/扩展三种模式必须明确，不能混用旧 snapshot。
2. 优先查找并读取用户已有的准确 GSC/GA property。`setup_mode: existing` 只记录 readback；若必须创建，则 `gsc_setup` 和 `ga_setup` 分别取得精确授权，不能用 deployment 授权代替。
3. 分别记录 GSC 与 GA 的 property ID、setup status、setup mode、readback time、data status、时间区间和真实指标。只读取页面/API 明确返回的值；无数据、权限错误和请求失败是不同状态。
4. 单独检查 sitemap 可达性、robots、canonical、内部链接、页面状态码和 GSC 索引证据。普通内容页不得使用 Google Indexing API；URL Inspection 或 sitemap 提交也不能冒充已收录。

## 输出

- GSC 与 GA 独立的 property readback
- 索引、sitemap 和技术检查证据
- 带真实时间区间的 analytics-snapshot.json
- telemetry_verified/observing gate 和下一复查日期

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

- 只访问用户授权站点的 property 和公共 URL，不扩大到其他账号/站点。
- 不保存 OAuth token、Cookie、密码、service-account key 或浏览器存储。
- 不做 grow/hold/retire 决定，不提交普通页面到 Google Indexing API，不申请广告。
