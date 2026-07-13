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
}

export interface ReplyResult {
  submitted: boolean;
}

function normalizeTweetUrl(value: string): string | null {
  const match = value.match(/(?:https?:\/\/)?(?:x\.com|twitter\.com)\/((?:i\/web)|[^/?#]+)\/status\/(\d+)/i);
  if (!match) return null;
  return `https://x.com/${match[1]}/status/${match[2]}`;
}

type TargetInfo = { targetId: string; url: string; type: string };

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

export async function replyToX(options: ReplyOptions): Promise<ReplyResult> {
  const tweetUrl = normalizeTweetUrl(options.tweetUrl);
  if (!tweetUrl) throw new Error(`Invalid tweet URL: ${options.tweetUrl}`);

  const { text, submit = false, timeoutMs = 120_000, profileDir = getDefaultProfileDir() } = options;
  const chromePath = options.chromePath ?? findChromeExecutable(CHROME_CANDIDATES_FULL);
  if (!chromePath) throw new Error('Chrome not found. Set X_BROWSER_CHROME_PATH env var.');
  await mkdir(profileDir, { recursive: true });

  const reusable = await getReusableChromeDebugSession(profileDir);
  let port = reusable?.port;
  let wsUrl = reusable?.wsUrl;
  let launchedChrome = false;
  let chrome: ReturnType<typeof spawn> | null = null;
  if (!reusable) {
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
      rememberChromeDebugPort(profileDir, port!);
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

    await insertTextIntoComposer(cdp, sessionId, text);
    if (!submit) return { submitted: false };
    if (!await clickReplySubmitButton(cdp, sessionId)) throw new Error('Could not find a visible reply submit button.');
    await sleep(2_000);
    return { submitted: true };
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
  const [tweetUrl, ...textParts] = process.argv.slice(2).filter((arg) => arg !== '--submit');
  const submit = process.argv.includes('--submit');
  if (!tweetUrl || textParts.length === 0) {
    console.error('Usage: npx -y bun x-reply.ts <tweet-url> [--submit] <reply text>');
    process.exit(1);
  }
  await replyToX({ tweetUrl, text: textParts.join(' '), submit }).catch((error) => {
    console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  });
}
