# Personal Finance Import Policy

## Ledger Semantics

The daily ledger records real income and spending. It should not absorb cash-out rows because cash-out is a funding movement: credit-card liability increases and available cash or balance increases.

Cash-out rows belong in a separate cash-out ledger once that table exists. Until then, exclude them from `账单明细` and report them in the summary.

## Natural Month Rule

The user uses natural months, not card statement cycles. Always use the transaction occurrence date from the export. Do not add a separate billing-period field for the daily ledger.

`月份` and `统计月份` are derived helpers in `YYYY-MM` format from the transaction date. They are not card statement cycles or separate bookkeeping periods.

## Alipay Rules

Skip:

- `收支类型=不计收支`
- `分类=不计收支`
- `收入 + 投资理财 + 余额宝-收益发放`

Cash-out:

- `标签=输出`

Daily ledger:

- all remaining rows after skip and cash-out rules
- set `来源=支付宝`
- set `月份=YYYY-MM` and `统计月份=YYYY-MM` from `日期`
- `165` yuan transfer income maps to `副业`

## Channel Mapping

Current Alipay account mapping:

| Source account | Feishu channel |
| --- | --- |
| empty | 支付宝 |
| 余额 | 支付宝 |
| 余额宝 | 支付宝 |
| 网商银行 | 支付宝 |
| 花呗 | 花呗 |
| 招商银行 | 招商银行信用卡 |
| 兴业银行 | 兴业信用卡 |
| 中信银行 | 中信信用卡 |
| 交通银行 | 交通银行信用卡 |
| 中国民生银行 | 民生信用卡 |
| 中国银行 | 中国银行储蓄卡 |

Do not infer debit versus credit from a shared bank label unless the user has given a rule. The current user rule treats 交通银行 and 民生 as credit-card channels.

## Category Mapping

Prefer merchant, remark, counterparty, product, and transaction-type signals over raw provider categories when they are stronger. Provider categories are fallback signals because exports often use broad labels such as `其他支出` or generic merchant-consumption rows.

Current specific rules:

| Signal | Category |
| --- | --- |
| 拼多多 | 日用购物 |
| 扫二维码付款 / 扫码付款 / 扫收钱码付款 | 餐饮 |
| 罗森 | 餐饮 |
| 称心厨房 | 餐饮 |
| 蓉易洗 | 交通 |
| 博物馆 | 旅游出行 |
| 宠物医疗险 / 保费 / 保险 | 医疗健康 |
| STRIPE | 数字服务 |
| MiniMax | 数字服务 |
| 知识星球 | 学习成长 |
| 粗门 | 娱乐消费 |
| 过载喜剧 | 娱乐消费 |
| 微信 `亲属卡交易` + 交易对方 `刘索朵` | 餐饮 |
| 国网 / 国家电网 / 电力公司 / 生活缴费 | 居住缴费 |

Keep broad categories stable:

- 餐饮
- 交通
- 日用购物
- 居住缴费
- 医疗健康
- 社交人情
- 娱乐消费
- 旅游出行
- 学习成长
- 数字服务
- 其他支出
- 工资
- 报销
- 副业
- 投资收益
- 转账收入
- 退款
- 奖金
- 其他收入

Do not overfit one-off merchant names unless repeated imports prove the rule.

## WeChat Rules

Skip:

- `收/支=/`
- `交易类型` contains `退款`
- `当前状态` contains `退款` or `退还`
- incoming red packet income below 5 yuan

Cash-out:

- `标签=输出`

Daily ledger:

- all remaining rows after skip and cash-out rules
- set `来源=微信`
- set `月份=YYYY-MM` and `统计月份=YYYY-MM` from `日期`
- incoming red packet income of 5 yuan or more maps to `社交人情`, unless the amount is 165 yuan
- 165 yuan transfer or red packet income maps to `副业`
- `亲属卡交易` with counterparty `刘索朵` maps to `餐饮` (the user's rule treats these as grocery spending)
- apply the specific merchant and remark rules from Category Mapping before falling back to `其他支出`

Current WeChat payment-method mapping:

| Source payment method | Feishu channel |
| --- | --- |
| `/` | 微信 |
| 零钱 | 微信 |
| 零钱通 | 微信 |
| 招商银行信用卡(...) | 招商银行信用卡 |
| 兴业银行信用卡(...) | 兴业信用卡 |
| 中信银行信用卡(...) | 中信信用卡 |
| 交通银行信用卡(...) | 交通银行信用卡 |
| 民生银行信用卡(...) | 民生信用卡 |
| 中国银行储蓄卡(...) | 中国银行储蓄卡 |
| 民生银行储蓄卡(...) | 民生银行储蓄卡 |
| 中信银行储蓄卡(...) | 中信银行储蓄卡 |

## Provider Extension Boundary

When adding another provider:

1. Add a provider adapter that emits the normalized transaction shape.
2. Keep skip/cash-out/dedupe/category policy shared.
3. Add channel mapping for the provider's balance and bound cards.
4. Preserve export-specific transaction IDs in `source_fields`; add them to `备注` only when useful.

## Write Safety

Before writing:

- read current Base fields
- add missing select options intentionally
- read existing records for dedupe
- dry-run batch create

After writing:

- verify total count
- spot-check newly added channels
- report skipped and duplicate counts
- do not update Feishu dashboard or view configuration during normal imports
