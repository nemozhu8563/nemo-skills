#!/usr/bin/env node

const path = require("node:path");
const readline = require("node:readline");
const { chromium } = require("C:/Program Files/nodejs/node_modules/article-clip/node_modules/playwright");

function parseArgs(argv) {
  const args = {
    command: "",
    peopleToken: "",
    collectionId: "",
    offset: 0,
    limit: 20,
    interactiveLogin: false,
    sessionDir: path.join(process.env.LOCALAPPDATA || "", "article-clip", "session-edge"),
  };
  for (let index = 2; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!args.command && !arg.startsWith("--")) {
      args.command = arg;
      continue;
    }
    if (arg === "--people-token") args.peopleToken = argv[++index];
    else if (arg === "--collection-id") args.collectionId = argv[++index];
    else if (arg === "--offset") args.offset = Number(argv[++index] || "0");
    else if (arg === "--limit") args.limit = Number(argv[++index] || "20");
    else if (arg === "--interactive-login") args.interactiveLogin = true;
    else if (arg === "--session-dir") args.sessionDir = argv[++index];
  }
  return args;
}

function buildRequest(args) {
  if (args.command === "list-collections") {
    if (!args.peopleToken) throw new Error("--people-token is required for list-collections");
    const params = `include=data%5B*%5D.updated_time%2Canswer_count%2Cfollower_count%2Ccreator%2Cdescription%2Cis_following%2Ccomment_count%2Ccreated_time%3Bdata%5B*%5D.creator.kvip_info%3Bdata%5B*%5D.creator.vip_info&offset=${args.offset}&limit=${args.limit}`;
    return {
      referer: `https://www.zhihu.com/people/${args.peopleToken}/collections`,
      url: `https://www.zhihu.com/api/v4/people/${args.peopleToken}/collections?${params}`,
    };
  }
  if (args.command === "list-items") {
    if (!args.collectionId) throw new Error("--collection-id is required for list-items");
    return {
      referer: `https://www.zhihu.com/collection/${args.collectionId}`,
      url: `https://www.zhihu.com/api/v4/collections/${args.collectionId}/items?offset=${args.offset}&limit=${args.limit}`,
    };
  }
  throw new Error(`Unknown command: ${args.command}`);
}

async function waitForEnter(prompt) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  await new Promise((resolve) => rl.question(prompt, () => resolve()));
  rl.close();
}

async function fetchJson(page, request) {
  return page.evaluate(async ({ requestUrl, referer }) => {
    try {
      const response = await fetch(requestUrl, {
        credentials: "include",
        headers: {
          accept: "application/json, text/plain, */*",
          referer,
          "x-requested-with": "fetch",
        },
      });
      const text = await response.text();
      return { ok: response.ok, status: response.status, text };
    } catch (error) {
      return { ok: false, status: 0, text: String(error) };
    }
  }, { requestUrl: request.url, referer: request.referer });
}

async function main() {
  const args = parseArgs(process.argv);
  const request = buildRequest(args);
  const context = await chromium.launchPersistentContext(args.sessionDir, {
    channel: "msedge",
    headless: false,
    viewport: { width: 1280, height: 800 },
    args: [
      "--disable-blink-features=AutomationControlled",
      "--no-first-run",
      "--no-default-browser-check",
    ],
  });

  try {
    const page = context.pages()[0] || await context.newPage();
    await page.goto(request.referer, { waitUntil: "load", timeout: 60000 });
    await page.waitForTimeout(3000);

    let result = await fetchJson(page, request);
    if (result.status === 401 && args.interactiveLogin) {
      await page.goto(`https://www.zhihu.com/signin?next=${encodeURIComponent(request.referer)}`, {
        waitUntil: "load",
        timeout: 60000,
      });
      await waitForEnter("Zhihu login required. Complete login in the browser, then press Enter to continue...");
      await page.goto(request.referer, { waitUntil: "load", timeout: 60000 });
      await page.waitForTimeout(3000);
      result = await fetchJson(page, request);
    }

    if (!result.ok) {
      const error = new Error(`Zhihu API request failed (${result.status})`);
      error.details = result.text;
      throw error;
    }

    process.stdout.write(result.text);
  } finally {
    await context.close();
  }
}

main().catch((error) => {
  process.stderr.write(
    JSON.stringify(
      {
        error: String(error.message || error),
        details: error.details || null,
      },
      null,
      2,
    ) + "\n",
  );
  process.exit(1);
});
