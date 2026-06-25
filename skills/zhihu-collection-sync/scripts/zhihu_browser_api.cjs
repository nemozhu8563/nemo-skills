#!/usr/bin/env node

const path = require("node:path");
const readline = require("node:readline");

function loadChromium() {
  const candidates = [
    "playwright",
    "C:/Program Files/nodejs/node_modules/article-clip/node_modules/playwright",
  ];
  for (const candidate of candidates) {
    try {
      return require(candidate).chromium;
    } catch {
      // Try the next known install location.
    }
  }
  return null;
}

const chromium = loadChromium();

function defaultSessionDir() {
  if (process.env.ZHIHU_SESSION_DIR) return process.env.ZHIHU_SESSION_DIR;
  if (process.platform === "darwin") {
    return path.join(process.env.HOME || "", "Library", "Caches", "nemo-automations", "zhihu-collection-sync", "browser-session");
  }
  return path.join(process.env.LOCALAPPDATA || "", "article-clip", "session-edge");
}

function defaultBrowserChannel() {
  if (process.env.ZHIHU_BROWSER_CHANNEL) return process.env.ZHIHU_BROWSER_CHANNEL;
  return process.platform === "darwin" ? "chrome" : "msedge";
}

function parseArgs(argv) {
  const args = {
    command: "",
    peopleToken: "",
    collectionId: "",
    columnId: "",
    offset: 0,
    limit: 20,
    interactiveLogin: false,
    sessionDir: defaultSessionDir(),
    browserChannel: defaultBrowserChannel(),
    cdpUrl: process.env.CHROME_CDP_URL || "http://127.0.0.1:9222",
    webAccessUrl: process.env.WEB_ACCESS_PROXY_URL || "http://localhost:3456",
  };
  for (let index = 2; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!args.command && !arg.startsWith("--")) {
      args.command = arg;
      continue;
    }
    if (arg === "--people-token") args.peopleToken = argv[++index];
    else if (arg === "--collection-id") args.collectionId = argv[++index];
    else if (arg === "--column-id") args.columnId = argv[++index];
    else if (arg === "--offset") args.offset = Number(argv[++index] || "0");
    else if (arg === "--limit") args.limit = Number(argv[++index] || "20");
    else if (arg === "--interactive-login") args.interactiveLogin = true;
    else if (arg === "--session-dir") args.sessionDir = argv[++index];
    else if (arg === "--browser-channel") args.browserChannel = argv[++index];
    else if (arg === "--cdp-url") args.cdpUrl = argv[++index];
    else if (arg === "--web-access-url") args.webAccessUrl = argv[++index];
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
  if (args.command === "list-column-items") {
    if (!args.columnId) throw new Error("--column-id is required for list-column-items");
    return {
      referer: `https://www.zhihu.com/column/${args.columnId}`,
      url: `https://www.zhihu.com/api/v4/columns/${args.columnId}/items?offset=${args.offset}&limit=${args.limit}`,
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

async function fetchJsonWithPlaywright(args, request) {
  if (!chromium) return null;
  const context = await chromium.launchPersistentContext(args.sessionDir, {
    channel: args.browserChannel,
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

async function cdpCall(wsUrl, method, params = {}) {
  const socket = new WebSocket(wsUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", reject, { once: true });
  });

  let nextId = 1;
  try {
    return await new Promise((resolve, reject) => {
      const id = nextId++;
      const timer = setTimeout(() => reject(new Error(`CDP call timed out: ${method}`)), 60000);
      socket.addEventListener("message", function onMessage(event) {
        const payload = JSON.parse(event.data);
        if (payload.id !== id) return;
        clearTimeout(timer);
        socket.removeEventListener("message", onMessage);
        if (payload.error) reject(new Error(JSON.stringify(payload.error)));
        else resolve(payload.result);
      });
      socket.send(JSON.stringify({ id, method, params }));
    });
  } finally {
    socket.close();
  }
}

async function fetchJsonWithCdp(args, request) {
  const baseUrl = args.cdpUrl.replace(/\/$/, "");
  const targetResponse = await fetch(`${baseUrl}/json/new?${encodeURIComponent(request.referer)}`, {
    method: "PUT",
  });
  if (!targetResponse.ok) {
    throw new Error(`Could not create Chrome CDP target at ${baseUrl} (${targetResponse.status})`);
  }
  const target = await targetResponse.json();
  if (!target.webSocketDebuggerUrl) {
    throw new Error(`Chrome CDP target did not include webSocketDebuggerUrl: ${JSON.stringify(target)}`);
  }

  try {
    await new Promise((resolve) => setTimeout(resolve, 3000));
    const expression = `(${async ({ requestUrl, referer }) => {
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
    }})(${JSON.stringify({ requestUrl: request.url, referer: request.referer })})`;
    const evaluated = await cdpCall(target.webSocketDebuggerUrl, "Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
    });
    return evaluated.result.value;
  } finally {
    if (target.id) {
      await fetch(`${baseUrl}/json/close/${target.id}`).catch(() => {});
    }
  }
}

async function fetchJsonWithWebAccess(args, request) {
  const baseUrl = args.webAccessUrl.replace(/\/$/, "");
  const targetResponse = await fetch(`${baseUrl}/new`, {
    method: "POST",
    body: request.referer,
  });
  if (!targetResponse.ok) {
    throw new Error(`Could not create web-access target at ${baseUrl} (${targetResponse.status})`);
  }
  const target = await targetResponse.json();
  const targetId = target.id || target.targetId || target.target || target.data?.id;
  if (!targetId) {
    throw new Error(`web-access /new did not return a target id: ${JSON.stringify(target)}`);
  }

  try {
    await new Promise((resolve) => setTimeout(resolve, 3000));
    const expression = `(${async ({ requestUrl, referer }) => {
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
    }})(${JSON.stringify({ requestUrl: request.url, referer: request.referer })})`;
    const evalResponse = await fetch(`${baseUrl}/eval?target=${encodeURIComponent(targetId)}`, {
      method: "POST",
      body: expression,
    });
    const evalText = await evalResponse.text();
    if (!evalResponse.ok) {
      throw new Error(`web-access /eval failed (${evalResponse.status}): ${evalText}`);
    }
    const payload = JSON.parse(evalText);
    return Object.prototype.hasOwnProperty.call(payload, "value") ? payload.value : payload;
  } finally {
    await fetch(`${baseUrl}/close?target=${encodeURIComponent(targetId)}`).catch(() => {});
  }
}

async function main() {
  const args = parseArgs(process.argv);
  const request = buildRequest(args);
  if (chromium) {
    await fetchJsonWithPlaywright(args, request);
    return;
  }

  let result;
  try {
    result = await fetchJsonWithWebAccess(args, request);
  } catch (webAccessError) {
    try {
      result = await fetchJsonWithCdp(args, request);
    } catch (cdpError) {
      const error = new Error(`Browser fetch failed. web-access: ${webAccessError.message}; raw CDP: ${cdpError.message}`);
      throw error;
    }
  }
  if (!result.ok) {
    const error = new Error(`Zhihu API request failed (${result.status})`);
    error.details = result.text;
    throw error;
  }
  process.stdout.write(result.text);
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
