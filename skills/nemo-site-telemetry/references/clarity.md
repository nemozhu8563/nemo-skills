# Microsoft Clarity Onboarding And Verification

## Resource discovery

1. 确认 Clarity account/organization 与目标 production origin。
2. 查找精确匹配的 project；存在则复用或恢复，不按相似名称选择。
3. 仅在用户已要求接入且没有精确 project 时创建。
4. 从 Settings → Setup 读取官方 tracking code/Project ID；不要自行推断 ID。

Project ID 会进入前端 tracking URL，不是账号密钥。登录 cookie、组织权限和 API token 仍是秘密。

## Code contract

- 在 production 页面 `<head>` 中加载一次项目 tracking code；
- 使用 build-time exact origin gate 与 runtime guard；
- local/preview 不输出 Project ID、Clarity marker 或远程 tag；
- 与 NPM/GTM/第三方平台安装方式查重，避免手写 tag 与插件双重安装；
- 根据站点现有 CMP/Consent Mode 传递 consent，不用示例值覆盖真实用户选择。

## Consent v2

当前官方推荐调用：

```javascript
window.clarity('consentv2', {
  ad_Storage: 'granted | denied',
  analytics_Storage: 'granted | denied'
});
```

字段大小写按官方 API 保留。没有广告用途时 `ad_Storage=denied`；`analytics_Storage` 来自用户选择/既有政策。Clarity 在 no-consent mode 下可以有限跟踪且不使用一方/三方 cookie；不要把“无 cookie”写成“完全无数据采集”。

## Evidence ladder

1. `clarity.setup`：精确 project existing/created/resumed，代码与 production build 读回一致。
2. `clarity.tag_loaded`：生产页面成功加载目标 Clarity tag；只证明客户端脚本层。
3. `clarity.production_request`：交互时 Network 出现 `POST https://www.clarity.ms/collect`；这是 transport 证据。
4. `clarity.recording`：目标 project 的 Recordings/Dashboard/live users 出现对应会话或数据；这是 provider 端证据。

Microsoft 官方安装页称添加代码后可立即查看项目数据，并给出 `/collect` POST 与 Dashboard/Recordings 两种验证方法。实际未读回时仍写 `pending` 或 `missing_evidence`，不以文档承诺替代当前证据。

## Failure modes

- tag loaded 但无 collect：检查 runtime gate、consent、Content Security Policy、拦截器和初始化顺序。
- collect 存在但无 recording：确认 project ID、目标 organization、bot exclusion、consent mode 与读取窗口；等待并回读，不创建第二个 project。
- 多页录屏未关联：检查 cookie setting 与 consent；Clarity 官方说明 cookies 关闭且未传 consent 时不会把 recordings 链为多页 session。
- preview 出现 collect：视为隔离失败，修复 gate 后重新部署验证。
