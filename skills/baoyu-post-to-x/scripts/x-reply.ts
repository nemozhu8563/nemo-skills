import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import process from 'node:process';

import {
  CHROME_CANDIDATES_FULL,
  CdpConnection,
  findChromeExecutable,
  getDefaultProfileDir,
  getFreePort,
  getReusableChromeDebugSession,
  insertTextIntoComposer,
  rememberChromeDebugPort,
  sleep,
  waitForChromeDebugPort,
} from './x-utils.js';

interface ReplyOptions {
  tweetUrl: string;
  text: string;
  submit?: boolean;
  timeoutMs?: number;
  profileDir?: string;
  chromePath?: string;
  connectPort?: number;
  onSubmitClicked?: () => void | Promise<void>;
}

export interface ReplyResult {
  submitted: boolean;
  submissionClicked: boolean;
  verifiedOnPostPage: boolean;
}

export class ReplyVerificationError extends Error {
  constructor() {
    super('Reply submit button was clicked, but the reply could not be verified on the direct post page.');
    this.name = 'ReplyVerificationError';
  }
}

function normalizeTweetUrl(value: string): string | null {
  const match = value.match(/(?:https?:\/\/)?(?:x\.com|twitter\.com)\/((?:i\/web)|[^/?#]+)\/status\/(\d+)/i);
  if (!match) return null;
  return `https://x.com/${match[1]}/status/${match[2]}`;
}

type TargetInfo = { targetId: string; url: string; type: string };

export interface RenderedReply {
  text: string;
  links: string[];
  linkMetadata?: string[];
}

function normalized(value: string): string {
  return value.replace(/\s+/g, ' ').trim().toLowerCase();
}

export function repoSlugFromReplyText(text: string): string | undefined {
  const match = text.match(/https?:\/\/(?:www\.)?github\.com\/([^/?#]+\/[^/?#]+)/i);
  return match?.[1]?.toLowerCase();
}

export function replyAppearsOnPostPage(reply: RenderedReply, expectedText: string): boolean {
  const expected = normalized(expectedText);
  const candidateText = normalized(reply.text);
  if (candidateText.includes(expected)) return true;

  const urlStart = expectedText.search(/https?:\/\//i);
  const label = normalized(urlStart >= 0 ? expectedText.slice(0, urlStart) : expectedText);
  const repoSlug = repoSlugFromReplyText(expectedText);
  if (!label || !repoSlug || !candidateText.includes(label)) return false;

  return candidateText.includes(repoSlug)
    || [...reply.links, ...(reply.linkMetadata ?? [])]
      .some((link) => normalized(link).includes(`github.com/${repoSlug}`));
}

async function getPageTargets(cdp: CdpConnection): Promise<TargetInfo[]> {
  const targets = await cdp.send<{ targetInfos: TargetInfo[] }>('Target.getTargets');
  return targets.targetInfos.filter((target) => target.type === 'page');
}

async function waitForPageTarget(cdp: CdpConnection, timeoutMs: number): Promise<TargetInfo | undefined> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const page = (await getPageTargets(cdp))[0];
    if (page) return page;
    await sleep(500);
  }
  return undefined;
}

async function waitForReplyEditor(cdp: CdpConnection, sessionId: string, timeoutMs: number): Promise<boolean> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const result = await cdp.send<{ result: { value: boolean } }>('Runtime.evaluate', {
      expression: `!!document.querySelector('[data-testid="tweetTextarea_0"]')`,
      returnByValue: true,
    }, { sessionId });
    if (result.result.value) return true;
    await sleep(500);
  }
  return false;
}

async function clickReplyButton(cdp: CdpConnection, sessionId: string): Promise<boolean> {
  const result = await cdp.send<{ result: { value: boolean } }>('Runtime.evaluate', {
    expression: `(() => {
      const candidates = Array.from(document.querySelectorAll('[data-testid="reply"], button[aria-label*="Reply" i], button[aria-label*="回复" i]'))
        .map((element) => element.closest('button, [role="button"]') ?? element)
        .filter((element, index, all) => all.indexOf(element) === index)
        .filter((element) => {
          const rect = element.getBoundingClientRect();
          const style = window.getComputedStyle(element);
          return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
        });
      const button = candidates.find((element) => element.closest('article')) ?? candidates[0];
      if (!button) return false;
      button.scrollIntoView({ block: 'center' });
      button.click();
      return true;
    })()`,
    returnByValue: true,
  }, { sessionId });
  return result.result.value;
}

async function clickReplySubmitButton(cdp: CdpConnection, sessionId: string): Promise<boolean> {
  const result = await cdp.send<{ result: { value: boolean } }>('Runtime.evaluate', {
    expression: `(() => {
      const candidates = Array.from(document.querySelectorAll('[data-testid="tweetButton"], [data-testid="tweetButtonInline"]'))
        .filter((element) => {
          const rect = element.getBoundingClientRect();
          const style = window.getComputedStyle(element);
          return element.getAttribute('aria-disabled') !== 'true' && !element.hasAttribute('disabled')
            && rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
        });
      const button = candidates.find((element) => element.closest('[role="dialog"]')?.querySelector('[data-testid="tweetTextarea_0"]')) ?? candidates[candidates.length - 1];
      if (!button) return false;
      button.click();
      return true;
    })()`,
    returnByValue: true,
  }, { sessionId });
  return result.result.value;
}

interface ThreadSnapshot {
  replyCount?: number;
  replies: RenderedReply[];
}

function statusIdFromTweetUrl(tweetUrl: string): string {
  const match = tweetUrl.match(/\/status\/(\d+)/);
  if (!match) throw new Error(`Could not extract status ID from ${tweetUrl}`);
  return match[1]!;
}

async function readThreadSnapshot(
  cdp: CdpConnection,
  sessionId: string,
  statusId: string,
): Promise<ThreadSnapshot> {
  const result = await cdp.send<{ result: { value: ThreadSnapshot } }>('Runtime.evaluate', {
    expression: `(() => {
      const statusId = ${JSON.stringify(statusId)};
      const articles = Array.from(document.querySelectorAll('article'));
      const parent = articles.find((article) => Array.from(article.querySelectorAll('a[href*="/status/"]'))
        .some((link) => link.getAttribute('href')?.includes('/status/' + statusId)));
      const labels = Array.from(parent?.querySelectorAll('[aria-label]') ?? [])
        .map((element) => element.getAttribute('aria-label') || '');
      const replyLabel = labels.find((label) => /\\d[\\d,.]*\\s*(?:回复|repl(?:y|ies))/i.test(label));
      const countMatch = replyLabel?.match(/(\\d[\\d,.]*)\\s*(?:回复|repl(?:y|ies))/i);
      const replyCount = countMatch ? Number.parseFloat(countMatch[1].replace(/,/g, '')) : undefined;
      return {
        replyCount: Number.isFinite(replyCount) ? replyCount : undefined,
        replies: articles.map((article) => ({
          text: article.innerText || '',
          links: Array.from(article.querySelectorAll('a[href]')).map((link) => link.href || ''),
          linkMetadata: Array.from(article.querySelectorAll('a[href]')).flatMap((link) => [
            link.getAttribute('title') || '',
            link.getAttribute('aria-label') || '',
            link.getAttribute('data-expanded-url') || '',
          ]).filter(Boolean),
        })),
      };
    })()`,
    returnByValue: true,
  }, { sessionId });
  return result.result.value;
}

async function waitForPublishedReply(
  cdp: CdpConnection,
  sessionId: string,
  statusId: string,
  text: string,
  timeoutMs: number,
  before: ThreadSnapshot,
): Promise<boolean> {
  const start = Date.now();
  let reloaded = false;
  while (Date.now() - start < timeoutMs) {
    const current = await readThreadSnapshot(cdp, sessionId, statusId);
    if (current.replies.some((reply) => replyAppearsOnPostPage(reply, text))) {
      const replyCountChanged = before.replyCount != null && current.replyCount != null
        ? ` (${before.replyCount} → ${current.replyCount} replies)`
        : '';
      console.log(`[x-reply] Reply visible on the direct post page${replyCountChanged}.`);
      return true;
    }

    if (!reloaded && Date.now() - start >= timeoutMs / 2) {
      reloaded = true;
      console.log('[x-reply] Reply is not rendered yet; reloading the direct post page once.');
      await cdp.send('Page.reload', { ignoreCache: true }, { sessionId });
      await sleep(2_000);
    } else {
      await cdp.send('Runtime.evaluate', {
        expression: 'window.scrollTo({ top: document.body.scrollHeight, behavior: "instant" })',
      }, { sessionId });
    }
    await sleep(1_000);
  }
  return false;
}

export async function replyToX(options: ReplyOptions): Promise<ReplyResult> {
  const tweetUrl = normalizeTweetUrl(options.tweetUrl);
  if (!tweetUrl) throw new Error(`Invalid tweet URL: ${options.tweetUrl}`);

  const { text, submit = false, timeoutMs = 120_000, profileDir = getDefaultProfileDir(), connectPort } = options;
  const chromePath = options.chromePath ?? findChromeExecutable(CHROME_CANDIDATES_FULL);
  if (!chromePath) throw new Error('Chrome not found. Set X_BROWSER_CHROME_PATH env var.');
  await mkdir(profileDir, { recursive: true });

  const reusable = connectPort == null ? await getReusableChromeDebugSession(profileDir) : null;
  let port = connectPort ?? reusable?.port;
  let wsUrl = connectPort == null ? reusable?.wsUrl : undefined;
  let launchedChrome = false;
  let chrome: ReturnType<typeof spawn> | null = null;
  if (!reusable && connectPort == null) {
    port = await getFreePort();
    chrome = spawn(chromePath, [
      `--remote-debugging-port=${port}`,
      '--remote-debugging-address=127.0.0.1',
      `--user-data-dir=${profileDir}`,
      '--no-first-run',
      '--no-default-browser-check',
      '--start-maximized',
      tweetUrl,
    ], { stdio: 'ignore' });
    launchedChrome = true;
  }

  let cdp: CdpConnection | null = null;
  try {
    if (!wsUrl) {
      wsUrl = await waitForChromeDebugPort(port!, 30_000, { includeLastError: true });
      if (connectPort == null) rememberChromeDebugPort(profileDir, port!);
    }
    cdp = await CdpConnection.connect(wsUrl, 30_000, { defaultTimeoutMs: 15_000 });
    let page = launchedChrome ? await waitForPageTarget(cdp, 5_000) : undefined;
    if (!page) {
      try {
        const { targetId } = await cdp.send<{ targetId: string }>('Target.createTarget', { url: tweetUrl });
        page = { targetId, url: tweetUrl, type: 'page' };
      } catch {
        // Some Chrome debug sessions reject new tabs; reuse an existing page instead.
        page = await waitForPageTarget(cdp, 3_000);
        if (!page) throw new Error('Failed to open a new tab and no existing Chrome page is available.');
      }
    }
    const { sessionId } = await cdp.send<{ sessionId: string }>('Target.attachToTarget', { targetId: page.targetId, flatten: true });
    await cdp.send('Page.enable', {}, { sessionId });
    await cdp.send('Runtime.enable', {}, { sessionId });
    await cdp.send('Input.setIgnoreInputEvents', { ignore: false }, { sessionId });
    await cdp.send('Page.navigate', { url: tweetUrl }, { sessionId });
    await sleep(3_000);

    if (!await waitForReplyEditor(cdp, sessionId, 3_000)) {
      if (!await clickReplyButton(cdp, sessionId)) {
        throw new Error('Could not find a visible reply button. Confirm the post is accessible and X is logged in.');
      }
      if (!await waitForReplyEditor(cdp, sessionId, timeoutMs)) throw new Error('Timed out waiting for the reply editor.');
    }

    console.log('[x-reply] Typing reply...');
    // A native paste targets the frontmost Chrome tab, which can differ from
    // this CDP-attached reply page. Keep reply text scoped to the target page.
    await insertTextIntoComposer(cdp, sessionId, text, undefined, { preferClipboard: false });
    if (!submit) return { submitted: false, submissionClicked: false, verifiedOnPostPage: false };
    console.log('[x-reply] Submitting reply...');
    const statusId = statusIdFromTweetUrl(tweetUrl);
    const beforeReply = await readThreadSnapshot(cdp, sessionId, statusId);
    if (!await clickReplySubmitButton(cdp, sessionId)) throw new Error('Could not find a visible reply submit button.');
    await options.onSubmitClicked?.();
    if (!await waitForPublishedReply(cdp, sessionId, statusId, text, 20_000, beforeReply)) {
      throw new ReplyVerificationError();
    }
    console.log('[x-reply] Reply submitted and confirmed on the post page.');
    return { submitted: true, submissionClicked: true, verifiedOnPostPage: true };
  } finally {
    if (cdp) {
      if (launchedChrome) {
        try { await cdp.send('Browser.close', {}, { timeoutMs: 5_000 }); } catch {}
      }
      cdp.close();
    }
    if (launchedChrome && chrome) {
      try { chrome.kill('SIGTERM'); } catch {}
    }
  }
}

if (import.meta.main) {
  const args = process.argv.slice(2);
  let tweetUrl: string | undefined;
  let submit = false;
  let connectPort: number | undefined;
  const textParts: string[] = [];
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index]!;
    if (arg === '--submit') submit = true;
    else if (arg === '--connect-port' && args[index + 1]) {
      const parsedPort = Number.parseInt(args[++index]!, 10);
      if (!Number.isInteger(parsedPort) || parsedPort <= 0 || parsedPort > 65_535) {
        console.error('Error: --connect-port must be a valid TCP port.');
        process.exit(1);
      }
      connectPort = parsedPort;
    } else if (!arg.startsWith('-') && !tweetUrl) tweetUrl = arg;
    else if (!arg.startsWith('-')) textParts.push(arg);
  }
  if (!tweetUrl || textParts.length === 0) {
    console.error('Usage: npx -y bun x-reply.ts <tweet-url> [--connect-port <port>] [--submit] <reply text>');
    process.exit(1);
  }
  await replyToX({ tweetUrl, text: textParts.join(' '), submit, connectPort }).catch((error) => {
    console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  });
}
