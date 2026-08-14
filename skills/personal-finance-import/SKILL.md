---
name: personal-finance-import
description: Import Alipay CSV or WeChat Pay XLSX exports into the personal finance Feishu Base ledger, applying the shared mapping, skip, cash-out, dedupe, preview, and write-verification rules.
metadata:
  author: Nemo
  mode: Scaffold
---

# Personal Finance Import

Use this skill when a payment export should become rows in the Feishu Base table `账单明细`.

## Target

- Base: `E3cybN8XwaAeFjseGaGcYCq5njg`
- Table: `tblFfz5AExy4ziSp` (`账单明细`)
- Fields: `日期`, `月份`, `统计月份`, `收支类型`, `金额`, `一级分类`, `渠道`, `来源`, `账本`, `备注`

## Contract

1. Read the current Base fields and records before writing.
2. Parse the provider export with `scripts/prepare-import.mjs`; use the stable rules in `references/import-policy.md`.
3. Produce payload, summary, preview, and dedupe results before any write.
4. Write only after the user explicitly asks to import or continue after preview; then verify count and representative rows.

Use `LARK_CLI_NO_PROXY=1` for every `lark-cli` command. Normal imports write ledger records only; they do not modify Feishu dashboards or views.

## Commands

```bash
node scripts/prepare-import.mjs --provider alipay --input /path/to/export.csv --out-dir /tmp/personal-finance-import
PERSONAL_FINANCE_PYTHON=python3 node scripts/prepare-import.mjs --provider wechat --input /path/to/export.xlsx --out-dir /tmp/personal-finance-import
```

The generated `feishu-cashbook-payload.json` uses natural-month `月份` and `统计月份` values derived from `日期`. The generated `import-summary.json` reports daily rows, cash-out rows, skipped rows, and reasons.

## Exclusions

Do not route budgeting, investment analysis, repayment planning, or manual finance coaching here. Do not infer cash-out from merchant names; the export marker `标签=输出` is authoritative.
