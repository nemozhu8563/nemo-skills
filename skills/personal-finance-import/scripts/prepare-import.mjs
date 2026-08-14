#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const DEFAULT_FIELDS = ["日期", "月份", "统计月份", "收支类型", "金额", "一级分类", "渠道", "来源", "账本", "备注"];

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      args[key] = true;
    } else {
      args[key] = next;
      i += 1;
    }
  }
  return args;
}

function usage() {
  return `Usage:
node scripts/prepare-import.mjs --provider alipay --input /path/to/export.csv --out-dir /tmp/personal-finance-import
node scripts/prepare-import.mjs --provider wechat --input /path/to/export.xlsx --out-dir /tmp/personal-finance-import
`;
}

function decodeExport(filePath) {
  try {
    return execFileSync("/usr/bin/iconv", ["-f", "GB18030", "-t", "UTF-8", filePath], {
      encoding: "utf8",
      maxBuffer: 20 * 1024 * 1024,
    });
  } catch {
    return fs.readFileSync(filePath, "utf8");
  }
}

function parseCsvLine(line) {
  const cells = [];
  let current = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (quoted) {
      if (char === '"' && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        current += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      cells.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  cells.push(current);
  return cells;
}

function parseCsv(text, headerPrefix) {
  const lines = text.split(/\r?\n/).filter((line) => line.length > 0);
  const headerIndex = lines.findIndex((line) => line.startsWith(headerPrefix));
  if (headerIndex < 0) throw new Error(`Header not found: ${headerPrefix}`);
  const headers = parseCsvLine(lines[headerIndex]);
  return lines.slice(headerIndex + 1).map((line) => {
    const cells = parseCsvLine(line);
    return Object.fromEntries(headers.map((header, index) => [header, cells[index] ?? ""]));
  });
}

function parseWorkbook(input, headerName) {
  const python = process.env.PERSONAL_FINANCE_PYTHON || "python3";
  const script = String.raw`
import json, sys
from openpyxl import load_workbook

path = sys.argv[1]
header_name = sys.argv[2]
wb = load_workbook(path, read_only=True, data_only=True)
ws = wb.active
header_row = None
headers = None
for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
    values = list(row)
    if header_name in values:
        header_row = idx
        headers = ["" if value is None else str(value) for value in values]
        break
if header_row is None:
    raise SystemExit(f"Header not found: {header_name}")
rows = []
for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
    if not row or row[0] is None:
        continue
    item = {}
    for index, header in enumerate(headers):
        if not header:
            continue
        value = row[index] if index < len(row) else None
        item[header] = "" if value is None else str(value)
    rows.append(item)
print(json.dumps({"headers": headers, "rows": rows}, ensure_ascii=False))
`;
  const output = execFileSync(python, ["-c", script, input, headerName], {
    encoding: "utf8",
    maxBuffer: 50 * 1024 * 1024,
  });
  return JSON.parse(output);
}

function parseAmount(value) {
  return Number(String(value || "").replace(/,/g, "").replace(/，/g, ""));
}

function parseDateTime(value) {
  const [datePart, timePart = "00:00"] = String(value || "").trim().split(/\s+/);
  const [year, month, day] = datePart.split(/[/-]/).map(Number);
  const [hour = "00", minute = "00", second = "00"] = timePart.split(":");
  return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")} ${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}:${String(second || "00").padStart(2, "0")}`;
}

function monthFromDateTime(dateTime) {
  return String(dateTime || "").slice(0, 7);
}

function alipayChannel(account) {
  const value = String(account || "").trim();
  if (!value) return "支付宝";
  if (value.includes("花呗")) return "花呗";
  if (value.includes("余额") || value.includes("余额宝") || value.includes("网商")) return "支付宝";
  if (value.includes("招商")) return "招商银行信用卡";
  if (value.includes("兴业")) return "兴业信用卡";
  if (value.includes("中信")) return "中信信用卡";
  if (value.includes("交通")) return "交通银行信用卡";
  if (value.includes("民生") || value.includes("中国民生")) return "民生信用卡";
  if (value.includes("中国银行")) return "中国银行储蓄卡";
  return "其他";
}

function wechatChannel(paymentMethod) {
  const value = String(paymentMethod || "").trim();
  if (!value || value === "/" || value === "零钱" || value === "零钱通") return "微信";
  if (value.includes("招商银行信用卡")) return "招商银行信用卡";
  if (value.includes("兴业银行信用卡")) return "兴业信用卡";
  if (value.includes("中信银行信用卡")) return "中信信用卡";
  if (value.includes("交通银行信用卡")) return "交通银行信用卡";
  if (value.includes("民生银行信用卡")) return "民生信用卡";
  if (value.includes("中国银行储蓄卡")) return "中国银行储蓄卡";
  if (value.includes("民生银行储蓄卡")) return "民生银行储蓄卡";
  if (value.includes("中信银行储蓄卡")) return "中信银行储蓄卡";
  return "其他";
}

function classify(row) {
  const rawCategory = String(row["分类"] || "").trim();
  const type = String(row["收支类型"] || "").trim();
  const note = String(row["备注"] || "").trim();

  if (type === "收入") {
    if (rawCategory === "转账" && parseAmount(row["金额"]) === 165) return "副业";
    if (rawCategory === "转账") return "转账收入";
    if (rawCategory === "生意") return "副业";
    if (rawCategory === "退款" || note.includes("退款")) return "退款";
    return "其他收入";
  }

  const keywordRules = [
    ["日用购物", /拼多多/],
    ["餐饮", /扫二维码付款|扫码付款|扫收钱码付款|罗森|小厨|餐厅|汉堡王|沃尔玛|山姆|盒马|超市|烧鸡|饭|土豆|乳|酸奶|发酵乳|菜馆|岑味|于鸭子|钱大妈|朴朴/],
    ["旅游出行", /博物馆/],
    ["交通", /蓉易洗/],
    ["交通", /天府通|扫码乘车|滴滴|打车|骑行|行程|地铁|机票|停车|车位管理费/],
    ["医疗健康", /医保|医疗|保费|保险|好医保|宠物医疗险|医院|挂号|维生素|药/],
    ["数字服务", /MiniMax|客服QQ|订单号|AIGOCODE|GPT|ChatGPT|Gemini|App Store|Apple Music|云服务器|服务器|软件|会员|码牌|科技|Xesim|聊聊ai/i],
    ["居住缴费", /物业|电费|燃气|气费|话费|房租|国网|国家电网|电力公司|生活缴费/],
    ["社交人情", /红包|人情|礼金/],
    ["娱乐消费", /过载喜剧/],
    ["旅游出行", /酒店|住宿|旅游|旅行/],
    ["学习成长", /知识星球/],
  ];

  for (const [category, matcher] of keywordRules) {
    if (matcher.test(note)) return category;
  }

  if (rawCategory === "餐饮") return "餐饮";
  if (rawCategory === "交通") return "交通";
  if (["购物", "生活日用", "穿搭美容", "生活服务"].includes(rawCategory)) return "日用购物";
  if (rawCategory === "住房") return "居住缴费";
  if (["金融保险", "医疗保健"].includes(rawCategory)) return "医疗健康";
  if (rawCategory === "休闲玩乐") return "娱乐消费";
  if (rawCategory === "学习") return "学习成长";
  return type === "收入" ? "其他收入" : "其他支出";
}

function classifyWechat(row) {
  const type = String(row["收/支"] || "").trim();
  const transactionType = String(row["交易类型"] || "").trim();
  const counterparty = String(row["交易对方"] || "").trim();
  const product = String(row["商品"] || "").trim();
  const note = [transactionType, counterparty, product, String(row["备注"] || "").trim()].join(" ");
  const amount = parseAmount(row["金额(元)"]);

  if (type === "收入") {
    if (transactionType.includes("退款")) return "退款";
    if (amount === 165 && (transactionType.includes("转账") || transactionType.includes("红包"))) return "副业";
    if (transactionType.includes("红包")) return "社交人情";
    if (transactionType.includes("转账") || transactionType.includes("群收款")) return "转账收入";
    return "其他收入";
  }

  if (transactionType.includes("亲属卡交易") && counterparty.includes("刘索朵")) return "餐饮";

  const keywordRules = [
    ["日用购物", /拼多多/],
    ["餐饮", /扫二维码付款|扫码付款|扫收钱码付款|罗森|称心厨房|餐厅|小厨|汉堡王|沃尔玛|山姆|盒马|超市|烧鸡|饭|土豆|乳|酸奶|发酵乳|菜馆|小吃|美团|饿了么|餐饮|食品|酒|烟/],
    ["旅游出行", /博物馆/],
    ["交通", /蓉易洗/],
    ["交通", /天府通|扫码乘车|滴滴|打车|骑行|行程|地铁|机票|停车|车位管理费/],
    ["医疗健康", /医保|医疗|保费|保险|好医保|宠物医疗险|医院|挂号|维生素|药/],
    ["数字服务", /MiniMax|STRIPE|客服QQ|订单号|AIGOCODE|GPT|ChatGPT|Gemini|App Store|Apple Music|云服务器|服务器|软件|会员|码牌|科技|Xesim|Microsoft|office|365/i],
    ["居住缴费", /物业|电费|燃气|气费|话费|房租|中国电信|联通|移动|国网|国家电网|电力公司|生活缴费/],
    ["社交人情", /红包|群红包|转账|亲属卡|群收款|人情|礼金/],
    ["娱乐消费", /粗门|过载喜剧/],
    ["旅游出行", /酒店|住宿|旅游|旅行/],
    ["学习成长", /知识星球/],
  ];

  for (const [category, matcher] of keywordRules) {
    if (matcher.test(note)) return category;
  }

  if (transactionType.includes("红包") || transactionType.includes("转账") || transactionType.includes("亲属卡")) {
    return "社交人情";
  }
  return "其他支出";
}

function buildNote(row) {
  const note = String(row["备注"] || "").trim();
  const rawCategory = String(row["分类"] || "").trim();
  const account = String(row["账户"] || "").trim();
  const parts = [note || rawCategory || ""];
  if (rawCategory && !note.includes(rawCategory) && !["餐饮", "交通"].includes(rawCategory)) {
    parts.push(`支付宝分类:${rawCategory}`);
  }
  if (account) parts.push(`原账户:${account}`);
  return parts.filter(Boolean).join("；");
}

function buildWechatNote(row) {
  const parts = [
    "微信",
    String(row["交易类型"] || "").trim(),
    String(row["交易对方"] || "").trim(),
    String(row["商品"] || "").trim(),
  ].filter((value) => value && value !== "/");
  const sourceNote = String(row["备注"] || "").trim();
  const paymentMethod = String(row["支付方式"] || "").trim();
  if (sourceNote && sourceNote !== "/") parts.push(`微信备注:${sourceNote}`);
  if (paymentMethod && paymentMethod !== "/") parts.push(`原支付方式:${paymentMethod}`);
  return parts.join("｜");
}

function normalizeAlipay(row) {
  const tag = String(row["标签"] || "").trim();
  const type = String(row["收支类型"] || "").trim();
  const rawCategory = String(row["分类"] || "").trim();
  const note = String(row["备注"] || "").trim();

  if (tag === "输出") return { importTarget: "cashout_ledger", reason: "alipay_tag_output" };
  if (type === "收入" && rawCategory === "投资理财" && note.includes("余额宝-收益发放")) {
    return { importTarget: "skip", reason: "yuebao_interest" };
  }
  if (type === "不计收支" || rawCategory === "不计收支") {
    return { importTarget: "skip", reason: "non_income_expense" };
  }

  const dateTime = parseDateTime(row["记录时间"]);
  const month = monthFromDateTime(dateTime);
  return {
    importTarget: "daily_ledger",
    row: [
      dateTime,
      month,
      month,
      type,
      parseAmount(row["金额"]),
      classify(row),
      alipayChannel(row["账户"]),
      "支付宝",
      "私账",
      buildNote(row),
    ],
  };
}

function prepareAlipay(input) {
  const text = decodeExport(input);
  const sourceRows = parseCsv(text, "记录时间,");
  const rows = [];
  const summary = {
    provider: "alipay",
    source_rows: sourceRows.length,
    daily_ledger: 0,
    cashout_ledger: 0,
    skip: 0,
    reasons: {},
  };

  for (const sourceRow of sourceRows) {
    const normalized = normalizeAlipay(sourceRow);
    summary[normalized.importTarget] += 1;
    if (normalized.reason) summary.reasons[normalized.reason] = (summary.reasons[normalized.reason] || 0) + 1;
    if (normalized.importTarget === "daily_ledger") rows.push(normalized.row);
  }

  return { payload: { fields: DEFAULT_FIELDS, rows }, summary };
}

function normalizeWechat(row) {
  const tag = String(row["标签"] || "").trim();
  const flowType = String(row["收/支"] || "").trim();
  const status = String(row["当前状态"] || "").trim();
  const transactionType = String(row["交易类型"] || "").trim();
  const amount = parseAmount(row["金额(元)"]);

  if (tag === "输出") return { importTarget: "cashout_ledger", reason: "wechat_tag_output" };
  if (flowType === "/" || !flowType) return { importTarget: "skip", reason: "neutral_transaction" };
  if (transactionType.includes("退款") || status.includes("退款") || status.includes("退还")) {
    return { importTarget: "skip", reason: "refund_or_returned" };
  }
  if (flowType === "收入" && transactionType.includes("红包") && amount < 5) {
    return { importTarget: "skip", reason: "small_redpacket_income" };
  }

  const dateTime = parseDateTime(row["交易时间"]);
  const month = monthFromDateTime(dateTime);
  return {
    importTarget: "daily_ledger",
    row: [
      dateTime,
      month,
      month,
      flowType,
      amount,
      classifyWechat(row),
      wechatChannel(row["支付方式"]),
      "微信",
      "私账",
      buildWechatNote(row),
    ],
  };
}

function prepareWechat(input) {
  const workbook = parseWorkbook(input, "交易时间");
  const rows = [];
  const summary = {
    provider: "wechat",
    source_rows: workbook.rows.length,
    daily_ledger: 0,
    cashout_ledger: 0,
    skip: 0,
    reasons: {},
  };

  for (const sourceRow of workbook.rows) {
    const normalized = normalizeWechat(sourceRow);
    summary[normalized.importTarget] += 1;
    if (normalized.reason) summary.reasons[normalized.reason] = (summary.reasons[normalized.reason] || 0) + 1;
    if (normalized.importTarget === "daily_ledger") rows.push(normalized.row);
  }

  return { payload: { fields: DEFAULT_FIELDS, rows }, summary };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.input || !args.provider) {
    console.error(usage());
    process.exit(args.help ? 0 : 1);
  }

  const outDir = args["out-dir"] || "/tmp/personal-finance-import";
  fs.mkdirSync(outDir, { recursive: true });

  const { payload, summary } =
    args.provider === "alipay"
      ? prepareAlipay(args.input)
      : args.provider === "wechat"
        ? prepareWechat(args.input)
        : (() => {
            throw new Error(`Provider adapter not implemented yet: ${args.provider}`);
          })();
  const payloadPath = path.join(outDir, "feishu-cashbook-payload.json");
  const summaryPath = path.join(outDir, "import-summary.json");
  fs.writeFileSync(payloadPath, JSON.stringify(payload, null, 2));
  fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
  console.log(JSON.stringify({ payload: payloadPath, summary: summaryPath, ...summary }, null, 2));
}

main();
