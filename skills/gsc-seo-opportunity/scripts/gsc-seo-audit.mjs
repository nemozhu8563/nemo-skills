#!/usr/bin/env node

import { createServer } from "node:http";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { execFile } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const skillRoot = path.resolve(__dirname, "..");
const runtimeRoot =
  process.env.GSC_SEO_RUNTIME_ROOT ||
  path.join(process.env.HOME || ".", "Library", "Caches", "gsc-seo-opportunity");
const defaultCredentialsPath = path.join(runtimeRoot, "config", "credentials.json");
const defaultTokenPath = path.join(runtimeRoot, "data", "token.json");
const defaultConfigPath = path.join(runtimeRoot, "config", "sites.json");
const defaultOutDir = path.join(runtimeRoot, "reports");
const credentialsPath = process.env.GSC_CREDENTIALS_PATH || defaultCredentialsPath;
const tokenPath = process.env.GSC_TOKEN_PATH || defaultTokenPath;
const scopes = ["https://www.googleapis.com/auth/webmasters.readonly"];

const args = parseArgs(process.argv.slice(2));
const command = args._[0] || "help";

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});

async function main() {
  if (command === "help" || args.help) return printHelp();
  if (command === "auth") return authorize();
  if (command === "sites") return listSites();
  if (command === "audit") return runAudit();
  throw new Error(`Unknown command: ${command}`);
}

async function authorize() {
  const credentials = await readCredentials();
  const client = getClient(credentials);
  const port = Number(args.port || 53682);
  const redirectUri = `http://127.0.0.1:${port}/oauth2callback`;
  const authUrl = new URL("https://accounts.google.com/o/oauth2/v2/auth");
  authUrl.searchParams.set("client_id", client.client_id);
  authUrl.searchParams.set("redirect_uri", redirectUri);
  authUrl.searchParams.set("response_type", "code");
  authUrl.searchParams.set("scope", scopes.join(" "));
  authUrl.searchParams.set("access_type", "offline");
  authUrl.searchParams.set("prompt", "consent");

  const codePromise = waitForOAuthCode(port);
  console.log(`Open this URL to authorize GSC access:\n${authUrl.toString()}`);
  if (args.open !== "false" && process.platform === "darwin") {
    execFile("/usr/bin/open", [authUrl.toString()], () => {});
  }

  const code = await codePromise;
  const token = await exchangeCode({ client, code, redirectUri });
  await writeJson(tokenPath, withExpiry(token));
  console.log(`Saved token: ${tokenPath}`);
}

async function listSites() {
  const accessToken = await getAccessToken();
  const json = await googleJson("https://www.googleapis.com/webmasters/v3/sites", {
    headers: authHeaders(accessToken),
  });
  console.log(JSON.stringify(json, null, 2));
}

async function runAudit() {
  const configPath = args.config || defaultConfigPath;
  const outDir = args.out || defaultOutDir;
  const config = await readJson(configPath, null);
  if (!config) throw new Error(`Missing config: ${configPath}`);
  await mkdir(outDir, { recursive: true });

  const accessToken = await getAccessToken();
  const reportDate = formatDate(new Date());
  const results = [];
  for (const site of config.sites || []) {
    const siteResult = await auditSite({ site, config, accessToken });
    results.push(siteResult);
  }

  const payload = {
    generatedAt: new Date().toISOString(),
    runtimeRoot,
    configPath,
    results,
  };
  const jsonPath = path.join(outDir, `${reportDate}-gsc-seo-opportunities.json`);
  const mdPath = path.join(outDir, `${reportDate}-gsc-seo-opportunities.md`);
  await writeFile(jsonPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  await writeFile(mdPath, renderMarkdown(payload), "utf8");
  console.log(JSON.stringify({ jsonPath, mdPath, sites: results.length }, null, 2));
}

async function auditSite({ site, config, accessToken }) {
  const siteUrl = site.siteUrl;
  if (!siteUrl) throw new Error("sites[].siteUrl is required");
  const endOffsetDays = Number(site.endOffsetDays ?? config.endOffsetDays ?? 2);
  const lookbackDays = Number(site.lookbackDays ?? config.lookbackDays ?? 28);
  const compareDays = Number(site.compareDays ?? config.compareDays ?? lookbackDays);
  const rowLimit = Number(site.rowLimit ?? config.rowLimit ?? 2500);
  const minImpressions = Number(site.minImpressions ?? config.minImpressions ?? 20);
  const maxPerSection = Number(site.maxOpportunitiesPerSection ?? config.maxOpportunitiesPerSection ?? 12);
  const brandTerms = (site.brandTerms || config.brandTerms || []).map((term) => String(term).toLowerCase());

  const currentEnd = daysAgo(endOffsetDays);
  const currentStart = daysAgo(endOffsetDays + lookbackDays - 1);
  const previousEnd = daysAgo(endOffsetDays + lookbackDays);
  const previousStart = daysAgo(endOffsetDays + lookbackDays + compareDays - 1);

  const currentRows = await searchAnalytics({
    accessToken,
    siteUrl,
    startDate: currentStart,
    endDate: currentEnd,
    rowLimit,
  });
  const previousRows = await searchAnalytics({
    accessToken,
    siteUrl,
    startDate: previousStart,
    endDate: previousEnd,
    rowLimit,
  });

  const rows = currentRows
    .map(normalizeRow)
    .filter((row) => row.query && row.page && row.impressions >= minImpressions);
  const previousMap = new Map(previousRows.map(normalizeRow).map((row) => [rowKey(row), row]));

  return {
    siteName: site.name || siteUrl,
    siteUrl,
    window: {
      currentStart,
      currentEnd,
      previousStart,
      previousEnd,
    },
    rowCount: rows.length,
    opportunities: {
      ctrTitle: ctrTitleOpportunities(rows, maxPerSection),
      strikingDistance: strikingDistanceOpportunities(rows, maxPerSection),
      decay: decayOpportunities(rows, previousMap, maxPerSection),
      newPage: newPageOpportunities(rows, brandTerms, maxPerSection),
      cannibalization: cannibalizationOpportunities(rows, maxPerSection),
    },
  };
}

async function searchAnalytics({ accessToken, siteUrl, startDate, endDate, rowLimit }) {
  const url = `https://www.googleapis.com/webmasters/v3/sites/${encodeURIComponent(siteUrl)}/searchAnalytics/query`;
  const json = await googleJson(url, {
    method: "POST",
    headers: { ...authHeaders(accessToken), "Content-Type": "application/json" },
    body: JSON.stringify({
      startDate,
      endDate,
      dimensions: ["query", "page"],
      type: "web",
      rowLimit,
    }),
  });
  return json.rows || [];
}

function ctrTitleOpportunities(rows, limit) {
  return rows
    .filter((row) => row.position <= 10 && row.ctr < expectedCtr(row.position) * 0.65)
    .map((row) => ({
      type: "ctr-title",
      action: "Rewrite title/meta and align heading copy with the query intent.",
      reason: `Position ${round(row.position)} but CTR ${pct(row.ctr)} is weak for this rank band.`,
      impactScore: score(row.impressions, expectedCtr(row.position) - row.ctr),
      ...pickEvidence(row),
    }))
    .sort((a, b) => b.impactScore - a.impactScore)
    .slice(0, limit);
}

function strikingDistanceOpportunities(rows, limit) {
  return rows
    .filter((row) => row.position > 7 && row.position <= 20)
    .map((row) => ({
      type: "striking-distance",
      action: "Add a focused section, examples, internal links, or FAQ coverage for this query.",
      reason: `Average position ${round(row.position)} is close enough to improve with targeted page work.`,
      impactScore: score(row.impressions, 21 - row.position),
      ...pickEvidence(row),
    }))
    .sort((a, b) => b.impactScore - a.impactScore)
    .slice(0, limit);
}

function decayOpportunities(rows, previousMap, limit) {
  return rows
    .map((row) => ({ row, previous: previousMap.get(rowKey(row)) }))
    .filter(({ previous }) => previous && previous.impressions >= 20)
    .map(({ row, previous }) => {
      const clickDrop = dropRate(previous.clicks, row.clicks);
      const impressionDrop = dropRate(previous.impressions, row.impressions);
      const positionDelta = row.position - previous.position;
      return { row, previous, clickDrop, impressionDrop, positionDelta };
    })
    .filter((item) => item.clickDrop >= 0.25 || item.impressionDrop >= 0.25 || item.positionDelta >= 2)
    .map((item) => ({
      type: "decay",
      action: "Review whether search intent, freshness, competing pages, or indexing status changed.",
      reason: `Compared with the previous window: clicks ${delta(item.previous.clicks, item.row.clicks)}, impressions ${delta(item.previous.impressions, item.row.impressions)}, position ${round(item.previous.position)} -> ${round(item.row.position)}.`,
      impactScore: score(item.previous.impressions, item.clickDrop + item.impressionDrop + Math.max(0, item.positionDelta)),
      previous: pickEvidence(item.previous),
      ...pickEvidence(item.row),
    }))
    .sort((a, b) => b.impactScore - a.impactScore)
    .slice(0, limit);
}

function newPageOpportunities(rows, brandTerms, limit) {
  return rows
    .filter((row) => row.position > 14 && row.query.split(/\s+/).length >= 3)
    .filter((row) => !brandTerms.some((term) => row.query.toLowerCase().includes(term)))
    .map((row) => ({
      type: "new-page",
      action: "Consider a dedicated page, tool surface, template, table, or comparison page for this query cluster.",
      reason: `The current page is only weakly relevant for a specific long-tail query at position ${round(row.position)}.`,
      impactScore: score(row.impressions, row.query.split(/\s+/).length),
      ...pickEvidence(row),
    }))
    .sort((a, b) => b.impactScore - a.impactScore)
    .slice(0, limit);
}

function cannibalizationOpportunities(rows, limit) {
  const grouped = new Map();
  for (const row of rows) {
    const current = grouped.get(row.query) || [];
    current.push(row);
    grouped.set(row.query, current);
  }
  return [...grouped.entries()]
    .filter(([, group]) => new Set(group.map((row) => row.page)).size > 1)
    .map(([query, group]) => {
      const sorted = group.sort((a, b) => b.impressions - a.impressions).slice(0, 4);
      return {
        type: "cannibalization",
        query,
        action: "Choose the canonical target page and align internal links/content boundaries.",
        reason: `${sorted.length} pages receive impressions for the same query.`,
        impactScore: sorted.reduce((sum, row) => sum + row.impressions, 0),
        pages: sorted.map(pickEvidence),
      };
    })
    .sort((a, b) => b.impactScore - a.impactScore)
    .slice(0, limit);
}

function renderMarkdown(payload) {
  const lines = [];
  lines.push("# GSC SEO Opportunities");
  lines.push("");
  lines.push(`Generated: ${payload.generatedAt}`);
  lines.push("");
  for (const result of payload.results) {
    lines.push(`## ${result.siteName}`);
    lines.push("");
    lines.push(`- Site: ${result.siteUrl}`);
    lines.push(`- Current window: ${result.window.currentStart} to ${result.window.currentEnd}`);
    lines.push(`- Previous window: ${result.window.previousStart} to ${result.window.previousEnd}`);
    lines.push(`- Rows analyzed: ${result.rowCount}`);
    lines.push("");

    renderSection(lines, "CTR / Title", result.opportunities.ctrTitle);
    renderSection(lines, "Striking Distance", result.opportunities.strikingDistance);
    renderSection(lines, "Decay / Refresh", result.opportunities.decay);
    renderSection(lines, "New Page / Long Tail", result.opportunities.newPage);
    renderCannibalization(lines, result.opportunities.cannibalization);

    lines.push("### 7-Day Plan");
    lines.push("");
    lines.push("1. Rewrite titles/meta for the top CTR opportunities with the clearest query intent.");
    lines.push("2. Add focused sections or examples for the top striking-distance queries.");
    lines.push("3. Review decay candidates manually before changing content; GSC shows symptoms, not full cause.");
    lines.push("4. Group long-tail candidates before creating new pages; avoid one thin page per tiny query.");
    lines.push("");
  }
  return `${lines.join("\n")}\n`;
}

function renderSection(lines, title, items) {
  lines.push(`### ${title}`);
  lines.push("");
  if (!items.length) {
    lines.push("- No high-confidence items in this section.");
    lines.push("");
    return;
  }
  for (const item of items.slice(0, 8)) {
    lines.push(`- Query: \`${item.query}\``);
    lines.push(`  Page: ${item.page}`);
    lines.push(`  Evidence: clicks ${item.clicks}, impressions ${item.impressions}, CTR ${pct(item.ctr)}, position ${round(item.position)}.`);
    lines.push(`  Action: ${item.action}`);
    lines.push(`  Why: ${item.reason}`);
  }
  lines.push("");
}

function renderCannibalization(lines, items) {
  lines.push("### Cannibalization");
  lines.push("");
  if (!items.length) {
    lines.push("- No high-confidence cannibalization candidates.");
    lines.push("");
    return;
  }
  for (const item of items.slice(0, 8)) {
    lines.push(`- Query: \`${item.query}\``);
    lines.push(`  Why: ${item.reason}`);
    lines.push(`  Action: ${item.action}`);
    for (const page of item.pages) {
      lines.push(`  - ${page.page} — impressions ${page.impressions}, position ${round(page.position)}`);
    }
  }
  lines.push("");
}

function normalizeRow(row) {
  return {
    query: row.keys?.[0] || "",
    page: row.keys?.[1] || "",
    clicks: Number(row.clicks || 0),
    impressions: Number(row.impressions || 0),
    ctr: Number(row.ctr || 0),
    position: Number(row.position || 0),
  };
}

function rowKey(row) {
  return `${row.query}\n${row.page}`;
}

function pickEvidence(row) {
  return {
    query: row.query,
    page: row.page,
    clicks: row.clicks,
    impressions: row.impressions,
    ctr: row.ctr,
    position: row.position,
  };
}

function expectedCtr(position) {
  if (position <= 1.5) return 0.28;
  if (position <= 3) return 0.15;
  if (position <= 5) return 0.08;
  if (position <= 10) return 0.035;
  return 0.015;
}

function score(volume, lift) {
  return Math.round(Number(volume || 0) * Math.max(0, Number(lift || 0)));
}

function dropRate(before, after) {
  if (!before) return 0;
  return Math.max(0, (before - after) / before);
}

function delta(before, after) {
  const diff = after - before;
  return `${before} -> ${after} (${diff >= 0 ? "+" : ""}${diff})`;
}

function pct(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

function round(value) {
  return Number(value || 0).toFixed(1);
}

function daysAgo(days) {
  const date = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
  return formatDate(date);
}

function formatDate(date) {
  return new Intl.DateTimeFormat("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

async function getAccessToken() {
  const token = await readJson(tokenPath, null);
  if (!token) throw new Error(`Missing token. Run: node "${path.relative(skillRoot, __filename)}" auth`);
  if (token.access_token && token.expires_at && Number(token.expires_at) > Date.now() + 60_000) {
    return token.access_token;
  }
  if (!token.refresh_token) throw new Error("Token has no refresh_token. Re-run auth.");

  const credentials = await readCredentials();
  const client = getClient(credentials);
  const params = new URLSearchParams({
    client_id: client.client_id,
    refresh_token: token.refresh_token,
    grant_type: "refresh_token",
  });
  if (client.client_secret) params.set("client_secret", client.client_secret);

  const refreshed = await googleJson("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: params.toString(),
  });
  const nextToken = withExpiry({ ...token, ...refreshed });
  await writeJson(tokenPath, nextToken);
  return nextToken.access_token;
}

function waitForOAuthCode(port) {
  return new Promise((resolve, reject) => {
    const server = createServer((req, res) => {
      const url = new URL(req.url || "/", `http://127.0.0.1:${port}`);
      if (url.pathname !== "/oauth2callback") {
        res.writeHead(404);
        res.end("Not found");
        return;
      }
      const code = url.searchParams.get("code");
      const error = url.searchParams.get("error");
      res.writeHead(code ? 200 : 400, { "Content-Type": "text/plain; charset=utf-8" });
      res.end(code ? "GSC authorization complete. You can close this tab." : `Authorization failed: ${error}`);
      server.close();
      if (code) resolve(code);
      else reject(new Error(error || "OAuth failed"));
    });
    server.listen(port, "127.0.0.1", () => {});
    server.on("error", reject);
  });
}

async function exchangeCode({ client, code, redirectUri }) {
  const params = new URLSearchParams({
    client_id: client.client_id,
    code,
    redirect_uri: redirectUri,
    grant_type: "authorization_code",
  });
  if (client.client_secret) params.set("client_secret", client.client_secret);
  return googleJson("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: params.toString(),
  });
}

async function googleJson(url, options = {}) {
  const response = await fetch(url, options);
  const text = await response.text();
  const json = text ? JSON.parse(text) : {};
  if (!response.ok) {
    const message = json.error?.message || json.error_description || JSON.stringify(json);
    throw new Error(`Google API error ${response.status}: ${message}`);
  }
  return json;
}

async function readCredentials() {
  const credentials = await readJson(credentialsPath, null);
  if (!credentials) throw new Error(`Missing OAuth credentials: ${credentialsPath}`);
  return credentials;
}

function getClient(credentials) {
  const client = credentials.installed || credentials.web || credentials;
  if (!client.client_id) throw new Error("credentials.json missing client_id");
  return client;
}

function withExpiry(token) {
  return { ...token, expires_at: Date.now() + Number(token.expires_in || 3600) * 1000 };
}

async function readJson(target, fallback) {
  if (!existsSync(target)) return fallback;
  try {
    return JSON.parse(await readFile(target, "utf8"));
  } catch {
    return fallback;
  }
}

async function writeJson(target, value) {
  await mkdir(path.dirname(target), { recursive: true });
  await writeFile(target, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function authHeaders(accessToken) {
  return { Authorization: `Bearer ${accessToken}` };
}

function parseArgs(argv) {
  const parsed = { _: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!arg.startsWith("--")) {
      parsed._.push(arg);
      continue;
    }
    const body = arg.slice(2);
    const equals = body.indexOf("=");
    if (equals !== -1) {
      parsed[body.slice(0, equals)] = body.slice(equals + 1);
      continue;
    }
    const next = argv[index + 1];
    if (next && !next.startsWith("--")) {
      parsed[body] = next;
      index += 1;
    } else {
      parsed[body] = "true";
    }
  }
  return parsed;
}

function printHelp() {
  console.log(`Usage:
  node scripts/gsc-seo-audit.mjs auth [--open=false]
  node scripts/gsc-seo-audit.mjs sites
  node scripts/gsc-seo-audit.mjs audit --config "$GSC_SEO_RUNTIME_ROOT/config/sites.json" [--out "$GSC_SEO_RUNTIME_ROOT/reports"]

Runtime:
  GSC_SEO_RUNTIME_ROOT=${runtimeRoot}
  GSC_CREDENTIALS_PATH=${credentialsPath}
  GSC_TOKEN_PATH=${tokenPath}`);
}
