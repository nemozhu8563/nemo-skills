import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';

import {
  CHROME_CANDIDATES_FULL,
  CdpConnection,
  clearChromeDebugPort,
  findChromeExecutable,
  getDefaultProfileDir,
  getFreePort,
  getReusableChromeDebugSession,
  rememberChromeDebugPort,
  sleep,
  waitForChromeDebugPort,
} from './x-utils.js';

type ChromeProcess = ReturnType<typeof spawn>;

export interface ReadonlyPageOptions {
  url: string;
  profileDir?: string;
  chromePath?: string;
  keepOpen?: boolean;
  startupTimeoutMs?: number;
}

export interface ReadonlyXPage {
  cdp: CdpConnection;
  sessionId: string;
  profileDir: string;
  port: number;
  reusedSession: boolean;
  launchedChrome: boolean;
  navigate: (url: string) => Promise<void>;
  evaluate: <T>(expression: string) => Promise<T>;
  close: () => Promise<void>;
}

export type XRenderedState = 'ready' | 'login_required' | 'rate_limited' | 'timeout';

export interface XRenderedResult {
  state: XRenderedState;
  articleCount: number;
  url: string;
  title: string;
  reloaded: boolean;
}

const PAGE_STATE_EXPRESSION = `(() => {
  const text = (document.body?.innerText || '').slice(0, 12000);
  const loginRequired = Boolean(
    document.querySelector('input[name="text"][autocomplete="username"]')
    || document.querySelector('a[href="/login"]')
    || /(?:sign in to x|登录 x|登录到 x)/i.test(text)
  );
  const rateLimited = /(?:rate limit exceeded|something went wrong\. try reloading|超过使用频率限制|出错了，请尝试重新加载)/i.test(text);
  return {
    loginRequired,
    rateLimited,
    articleCount: document.querySelectorAll('article[data-testid="tweet"], article').length,
    url: location.href,
    title: document.title,
  };
})()`;

async function createPageTarget(cdp: CdpConnection, url: string): Promise<string> {
  const result = await cdp.send<{ targetId: string }>('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await cdp.send<{ sessionId: string }>(
    'Target.attachToTarget',
    { targetId: result.targetId, flatten: true },
  );
  await cdp.send('Page.enable', {}, { sessionId });
  await cdp.send('Runtime.enable', {}, { sessionId });
  await cdp.send('Page.navigate', { url }, { sessionId });
  return sessionId;
}

export async function openReadonlyXPage(options: ReadonlyPageOptions): Promise<ReadonlyXPage> {
  const profileDir = options.profileDir ?? getDefaultProfileDir();
  const keepOpen = options.keepOpen ?? false;
  const startupTimeoutMs = options.startupTimeoutMs ?? 30_000;
  const chromePath = options.chromePath ?? findChromeExecutable(CHROME_CANDIDATES_FULL);
  if (!chromePath) throw new Error('Chrome not found. Set X_BROWSER_CHROME_PATH env var.');
  await mkdir(profileDir, { recursive: true });

  const reusable = await getReusableChromeDebugSession(profileDir);
  const port = reusable?.port ?? await getFreePort();
  let chrome: ChromeProcess | null = null;
  let launchedChrome = false;
  let cdp: CdpConnection | null = null;

  try {
    if (!reusable) {
      chrome = spawn(chromePath, [
        `--remote-debugging-port=${port}`,
        '--remote-debugging-address=127.0.0.1',
        `--user-data-dir=${profileDir}`,
        '--no-first-run',
        '--no-default-browser-check',
        '--start-maximized',
        'about:blank',
      ], { stdio: 'ignore' });
      launchedChrome = true;
    }

    const wsUrl = reusable?.wsUrl
      ?? await waitForChromeDebugPort(port, startupTimeoutMs, { includeLastError: true });
    rememberChromeDebugPort(profileDir, port);
    cdp = await CdpConnection.connect(wsUrl, startupTimeoutMs, { defaultTimeoutMs: 15_000 });
    const sessionId = await createPageTarget(cdp, options.url);
    let closed = false;

    return {
      cdp,
      sessionId,
      profileDir,
      port,
      reusedSession: Boolean(reusable),
      launchedChrome,
      navigate: async (url: string) => {
        await cdp!.send('Page.navigate', { url }, { sessionId });
      },
      evaluate: async <T>(expression: string): Promise<T> => {
        const result = await cdp!.send<{
          result: { value: T; description?: string };
          exceptionDetails?: { text?: string; exception?: { description?: string } };
        }>('Runtime.evaluate', {
          expression,
          returnByValue: true,
        }, { sessionId });
        if (result.exceptionDetails) {
          throw new Error(
            result.exceptionDetails.exception?.description
            || result.exceptionDetails.text
            || result.result.description
            || 'DOM evaluation failed.',
          );
        }
        return result.result.value;
      },
      close: async () => {
        if (closed) return;
        closed = true;
        if (launchedChrome && !keepOpen) {
          try { await cdp!.send('Browser.close', {}, { timeoutMs: 5_000 }); } catch {}
          clearChromeDebugPort(profileDir, port);
          try { chrome?.kill('SIGTERM'); } catch {}
        }
        cdp!.close();
      },
    };
  } catch (error) {
    cdp?.close();
    if (launchedChrome) {
      clearChromeDebugPort(profileDir, port);
      try { chrome?.kill('SIGTERM'); } catch {}
    }
    throw error;
  }
}

export async function waitForXRenderedContent(
  page: ReadonlyXPage,
  options: { timeoutMs?: number; requireArticle?: boolean; reloadOnce?: boolean } = {},
): Promise<XRenderedResult> {
  const timeoutMs = options.timeoutMs ?? 45_000;
  const requireArticle = options.requireArticle ?? true;
  const reloadOnce = options.reloadOnce ?? true;
  const startedAt = Date.now();
  let reloaded = false;
  let last = { articleCount: 0, url: '', title: '' };

  while (Date.now() - startedAt < timeoutMs) {
    const state = await page.evaluate<{
      loginRequired: boolean;
      rateLimited: boolean;
      articleCount: number;
      url: string;
      title: string;
    }>(PAGE_STATE_EXPRESSION);
    last = state;
    if (state.loginRequired) return { state: 'login_required', ...last, reloaded };
    if (state.rateLimited) return { state: 'rate_limited', ...last, reloaded };
    if (!requireArticle || state.articleCount > 0) return { state: 'ready', ...last, reloaded };

    if (reloadOnce && !reloaded && Date.now() - startedAt >= timeoutMs / 2) {
      reloaded = true;
      await page.cdp.send('Page.reload', { ignoreCache: true }, { sessionId: page.sessionId });
    }
    await sleep(500);
  }

  return { state: 'timeout', ...last, reloaded };
}
