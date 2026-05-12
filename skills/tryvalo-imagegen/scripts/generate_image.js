#!/usr/bin/env bun

import { existsSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { homedir } from "node:os";

const DEFAULT_BASE_URL = "https://api.tryvalo.com";
const DEFAULT_MODEL = "gpt-image-2";
const SKILL_NAME = "tryvalo-imagegen";

function printHelp() {
  console.log(`TryValo image generation

Usage:
  bun scripts/generate_image.js --prompt "A glass perfume bottle" --output image.png
  bun scripts/generate_image.js "A landscape poster" --size landscape --output poster.png

Options:
  --prompt <text>              Prompt text. Positional prompt also works.
  --output <path>              Save image to a local file.
  --model <id>                 Default: TRYVALO_IMAGE_MODEL or gpt-image-2.
  --size <size>                1024x1024, 1536x1024, 1024x1536, auto,
                               square, landscape, portrait.
  --quality <value>            Default: high.
  --n <count>                  Default: 1.
  --response-format <value>    url or b64_json. Auto defaults to b64_json
                               when --output is set, otherwise url.
  --watermark <true|false>     Send watermark flag for compatible channels.
  --base-url <url>             Default: TRYVALO_BASE_URL or https://api.tryvalo.com.
  --token <token>              Prefer env vars instead of this.
  --json                       Print JSON summary.
  --dry-run                    Print request payload without calling API.
  --help                       Show this help.

Env:
  TRYVALO_API_KEY / TRYVALO_TOKEN / NEW_API_TOKEN
  TRYVALO_BASE_URL / NEW_API_BASE_URL
  TRYVALO_IMAGE_MODEL / NEW_API_IMAGE_MODEL

Env files:
  ~/nemo-skills/tryvalo-imagegen.env
`);
}

function parseArgs(argv) {
  const args = {
    promptParts: [],
    quality: undefined,
    size: undefined,
    n: undefined,
    responseFormat: undefined,
    output: undefined,
    model: undefined,
    baseUrl: undefined,
    token: undefined,
    watermark: undefined,
    json: false,
    dryRun: false,
    help: false,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else if (arg === "--json") {
      args.json = true;
    } else if (arg === "--dry-run") {
      args.dryRun = true;
    } else if (arg.startsWith("--")) {
      const eq = arg.indexOf("=");
      const key = eq === -1 ? arg.slice(2) : arg.slice(2, eq);
      const value = eq === -1 ? argv[++i] : arg.slice(eq + 1);
      if (value === undefined) {
        fail(`Missing value for --${key}`);
      }
      assignOption(args, key, value);
    } else {
      args.promptParts.push(arg);
    }
  }

  return args;
}

function assignOption(args, key, value) {
  switch (key) {
    case "prompt":
    case "p":
      args.promptParts.push(value);
      break;
    case "output":
    case "o":
      args.output = value;
      break;
    case "model":
    case "m":
      args.model = value;
      break;
    case "size":
      args.size = value;
      break;
    case "quality":
      args.quality = value;
      break;
    case "n":
      args.n = value;
      break;
    case "response-format":
    case "response_format":
      args.responseFormat = value;
      break;
    case "watermark":
      args.watermark = parseBoolean(value, "--watermark");
      break;
    case "base-url":
    case "base_url":
      args.baseUrl = value;
      break;
    case "token":
      args.token = value;
      break;
    default:
      fail(`Unknown option: --${key}`);
  }
}

function parseBoolean(value, label) {
  const normalized = String(value).toLowerCase().trim();
  if (["true", "1", "yes", "y"].includes(normalized)) return true;
  if (["false", "0", "no", "n"].includes(normalized)) return false;
  fail(`${label} must be true or false`);
}

function loadEnvFiles() {
  const candidates = [join(homedir(), "nemo-skills", `${SKILL_NAME}.env`)];

  for (const file of candidates) {
    if (!existsSync(file)) continue;
    const text = readFileSync(file, "utf8");
    for (const line of text.split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const match = trimmed.match(/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/);
      if (!match) continue;
      const [, key, rawValue] = match;
      if (process.env[key]) continue;
      process.env[key] = stripEnvQuotes(rawValue.trim());
    }
  }
}

function stripEnvQuotes(value) {
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1);
  }
  return value;
}

function normalizeSize(size) {
  const value = String(size || "1024x1024").trim().toLowerCase();
  const aliases = new Map([
    ["square", "1024x1024"],
    ["方图", "1024x1024"],
    ["1:1", "1024x1024"],
    ["landscape", "1536x1024"],
    ["横版", "1536x1024"],
    ["16:9", "1536x1024"],
    ["portrait", "1024x1536"],
    ["竖版", "1024x1536"],
    ["9:16", "1024x1536"],
  ]);

  const normalized = aliases.get(value) || value;
  const blocked = new Set(["2k", "4k", "2048x2048", "4096x4096"]);
  if (blocked.has(normalized)) {
    fail(
      `gpt-image-2 does not accept size=${size}. Use 1536x1024, 1024x1536, or 1024x1024, then upscale downstream.`,
    );
  }

  const allowed = new Set(["auto", "1024x1024", "1536x1024", "1024x1536"]);
  if (!allowed.has(normalized)) {
    fail(
      `Unsupported size: ${size}. Allowed: auto, 1024x1024, 1536x1024, 1024x1536, square, landscape, portrait.`,
    );
  }
  return normalized;
}

function endpointFromBaseUrl(baseUrl) {
  const clean = baseUrl.replace(/\/+$/, "");
  if (clean.endsWith("/v1")) return `${clean}/images/generations`;
  return `${clean}/v1/images/generations`;
}

function buildPayload(args) {
  const prompt = args.promptParts.join(" ").trim();
  if (!prompt) fail("Missing prompt. Use --prompt \"...\" or pass a positional prompt.");

  const model =
    args.model ||
    process.env.TRYVALO_IMAGE_MODEL ||
    process.env.NEW_API_IMAGE_MODEL ||
    DEFAULT_MODEL;

  const output = args.output ? resolve(args.output) : undefined;
  const responseFormat = args.responseFormat || (output ? "b64_json" : "url");

  if (!["url", "b64_json"].includes(responseFormat)) {
    fail("--response-format must be url or b64_json");
  }

  const n = Number.parseInt(args.n || "1", 10);
  if (!Number.isInteger(n) || n < 1) fail("--n must be a positive integer");

  const payload = {
    model,
    prompt,
    size: normalizeSize(args.size),
    quality: args.quality || "high",
    n,
    response_format: responseFormat,
  };

  if (args.watermark !== undefined) {
    payload.watermark = args.watermark;
  }

  return { payload, output };
}

async function callImageApi({ payload, token, baseUrl }) {
  const url = endpointFromBaseUrl(baseUrl);
  const response = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const text = await response.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { raw: text };
  }

  if (!response.ok) {
    const details = typeof data === "object" ? JSON.stringify(data) : String(data);
    fail(`API request failed (${response.status}): ${details}`);
  }

  return data;
}

async function saveImage(result, outputPath) {
  const first = result?.data?.[0];
  if (!first) fail("API response did not include data[0]");

  ensureDirectory(dirname(outputPath));

  if (first.b64_json) {
    const base64 = String(first.b64_json).replace(/^data:image\/[a-zA-Z0-9.+-]+;base64,/, "");
    await Bun.write(outputPath, Buffer.from(base64, "base64"));
    return { saved: outputPath, source: "b64_json" };
  }

  if (first.url) {
    const imageResponse = await fetch(first.url);
    if (!imageResponse.ok) {
      fail(`Image download failed (${imageResponse.status}) from ${first.url}`);
    }
    await Bun.write(outputPath, await imageResponse.arrayBuffer());
    return { saved: outputPath, source: "url", url: first.url };
  }

  fail("API response did not include url or b64_json");
}

function ensureDirectory(directory) {
  if (existsSync(directory)) {
    if (statSync(directory).isDirectory()) return;
    fail(`Output parent exists but is not a directory: ${directory}`);
  }

  try {
    mkdirSync(directory, { recursive: true });
  } catch (error) {
    if (error?.code === "EEXIST" && existsSync(directory) && statSync(directory).isDirectory()) {
      return;
    }
    throw error;
  }
}

function summarize(result, saveInfo) {
  const first = result?.data?.[0] || {};
  return {
    saved: saveInfo?.saved,
    source: saveInfo?.source,
    url: saveInfo?.url || first.url,
    has_b64_json: Boolean(first.b64_json),
    revised_prompt: first.revised_prompt || undefined,
    created: result?.created,
  };
}

function fail(message) {
  console.error(`Error: ${message}`);
  process.exit(1);
}

async function main() {
  loadEnvFiles();
  const args = parseArgs(Bun.argv.slice(2));

  if (args.help) {
    printHelp();
    return;
  }

  const { payload, output } = buildPayload(args);
  const baseUrl =
    args.baseUrl ||
    process.env.TRYVALO_BASE_URL ||
    process.env.NEW_API_BASE_URL ||
    DEFAULT_BASE_URL;

  if (args.dryRun) {
    const dryRun = {
      endpoint: endpointFromBaseUrl(baseUrl),
      payload,
      output,
    };
    console.log(args.json ? JSON.stringify(dryRun, null, 2) : dryRun);
    return;
  }

  const token =
    args.token ||
    process.env.TRYVALO_API_KEY ||
    process.env.TRYVALO_TOKEN ||
    process.env.NEW_API_TOKEN;

  if (!token) {
    fail(
      "Missing API token. Set TRYVALO_API_KEY, TRYVALO_TOKEN, or NEW_API_TOKEN in your environment, or put it in ~/nemo-skills/tryvalo-imagegen.env.",
    );
  }

  const result = await callImageApi({ payload, token, baseUrl });
  const saveInfo = output ? await saveImage(result, output) : undefined;
  const summary = summarize(result, saveInfo);

  if (args.json) {
    console.log(JSON.stringify(summary, null, 2));
  } else if (summary.saved) {
    console.log(`Saved image: ${summary.saved}`);
    if (summary.url) console.log(`Source URL: ${summary.url}`);
  } else if (summary.url) {
    console.log(summary.url);
  } else if (summary.has_b64_json) {
    console.log("Image returned as b64_json. Re-run with --output <path> to save it.");
  } else {
    console.log(JSON.stringify(result, null, 2));
  }
}

await main();
