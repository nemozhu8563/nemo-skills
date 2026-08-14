import process from 'node:process';

import { openReadonlyXPage, waitForXRenderedContent } from './x-readonly.js';
import { repoSlugFromReplyText, replyAppearsOnPostPage, type RenderedReply } from './x-reply.js';
import { sleep } from './x-utils.js';

interface VerifyOptions {
  healthCheck: boolean;
  tweetUrl?: string;
  handle?: string;
  mainQuery?: string;
  repoSlug?: string;
  replyText?: string;
  profileDir?: string;
  timeoutMs: number;
  keepOpen: boolean;
}

interface RenderedArticle extends RenderedReply {
  statusUrls: string[];
}

export interface ThreadClassification {
  mainPostFound: boolean;
  replyFound: boolean;
}

export interface VerifyResult {
  ok: boolean;
  state: 'ready' | 'verified' | 'main_only' | 'not_found' | 'login_required' | 'rate_limited' | 'dom_timeout' | 'error';
  mainPostUrl?: string;
  mainPostFound?: boolean;
  replyFound?: boolean;
  repoSlug?: string;
  reusedSession?: boolean;
  launchedChrome?: boolean;
  error?: string;
}

function normalizeText(value: string): string {
  return value.replace(/\s+/g, ' ').trim().toLowerCase();
}

export function normalizeTweetUrl(value: string): string | null {
  const match = value.match(/(?:https?:\/\/)?(?:x\.com|twitter\.com)\/((?:i\/web)|[^/?#]+)\/status\/(\d+)/i);
  if (!match) return null;
  return `https://x.com/${match[1]}/status/${match[2]}`;
}

function expectedReply(options: VerifyOptions): string | undefined {
  if (options.replyText) return options.replyText;
  if (options.repoSlug) return `项目地址：https://github.com/${options.repoSlug}`;
  return undefined;
}

export function findMainPostUrl(
  articles: RenderedArticle[],
  handle: string,
  mainQuery: string,
): string | undefined {
  const query = normalizeText(mainQuery);
  const ownerPrefix = `https://x.com/${handle.toLowerCase()}/status/`;
  return articles
    .filter((article) => normalizeText(article.text).includes(query))
    .flatMap((article) => article.statusUrls)
    .find((url) => url.toLowerCase().startsWith(ownerPrefix));
}

export function classifyThread(
  articles: RenderedArticle[],
  tweetUrl: string,
  expectedReplyText?: string,
): ThreadClassification {
  const normalizedTweetUrl = normalizeTweetUrl(tweetUrl);
  if (!normalizedTweetUrl) return { mainPostFound: false, replyFound: false };
  const statusId = normalizedTweetUrl.match(/\/status\/(\d+)/)?.[1];
  const mainIndex = articles.findIndex((article) => article.statusUrls.some((url) => url.includes(`/status/${statusId}`)));
  if (mainIndex < 0) return { mainPostFound: false, replyFound: false };
  if (!expectedReplyText) return { mainPostFound: true, replyFound: false };
  return {
    mainPostFound: true,
    replyFound: articles.some((article, index) => index !== mainIndex && replyAppearsOnPostPage(article, expectedReplyText)),
  };
}

export function replyVerificationPending(
  result: ThreadClassification,
  expectedReplyText?: string,
): boolean {
  if (!result.mainPostFound) return true;
  return Boolean(expectedReplyText) && !result.replyFound;
}

function parseArgs(args: string[]): VerifyOptions {
  const options: VerifyOptions = {
    healthCheck: false,
    timeoutMs: 45_000,
    keepOpen: false,
  };
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index]!;
    const value = args[index + 1];
    if (arg === '--health-check') options.healthCheck = true;
    else if (arg === '--tweet-url' && value) options.tweetUrl = args[++index]!;
    else if (arg === '--handle' && value) options.handle = args[++index]!.replace(/^@/, '');
    else if (arg === '--main-query' && value) options.mainQuery = args[++index]!;
    else if (arg === '--repo-slug' && value) options.repoSlug = args[++index]!;
    else if (arg === '--reply-text' && value) options.replyText = args[++index]!;
    else if (arg === '--profile' && value) options.profileDir = args[++index]!;
    else if (arg === '--timeout-ms' && value) options.timeoutMs = Number(args[++index]);
    else if (arg === '--keep-open') options.keepOpen = true;
    else throw new Error(`Unknown or incomplete argument: ${arg}`);
  }

  if (!Number.isFinite(options.timeoutMs) || options.timeoutMs <= 0) throw new Error('--timeout-ms must be positive.');
  if (options.healthCheck) return options;
  if (!options.tweetUrl && !(options.handle && options.mainQuery)) {
    throw new Error('Provide --tweet-url, or both --handle and --main-query.');
  }
  if (options.tweetUrl && !normalizeTweetUrl(options.tweetUrl)) throw new Error(`Invalid tweet URL: ${options.tweetUrl}`);
  if (options.handle && !/^[A-Za-z0-9_]{1,15}$/.test(options.handle)) throw new Error(`Invalid X handle: ${options.handle}`);
  if (options.repoSlug && !/^[^/\s]+\/[^/\s]+$/.test(options.repoSlug)) throw new Error(`Invalid repository slug: ${options.repoSlug}`);
  return options;
}

async function readArticles(page: Awaited<ReturnType<typeof openReadonlyXPage>>): Promise<RenderedArticle[]> {
  return page.evaluate<RenderedArticle[]>(`(() => Array.from(document.querySelectorAll('article[data-testid="tweet"], article')).map((article) => ({
    text: article.innerText || article.textContent || '',
    links: Array.from(article.querySelectorAll('a[href]')).map((link) => link.href || link.getAttribute('href') || ''),
    linkMetadata: Array.from(article.querySelectorAll('a[href]')).flatMap((link) => [
      link.getAttribute('title') || '',
      link.getAttribute('aria-label') || '',
      link.getAttribute('data-expanded-url') || '',
    ]).filter(Boolean),
    statusUrls: Array.from(article.querySelectorAll('a[href*="/status/"]'))
      .map((link) => link.href || link.getAttribute('href') || '')
      .map((href) => {
        const clean = href.split('?')[0];
        const analyticsIndex = clean.lastIndexOf('/analytics');
        if (analyticsIndex >= 0) return clean.slice(0, analyticsIndex);
        const photoIndex = clean.lastIndexOf('/photo/');
        return photoIndex >= 0 ? clean.slice(0, photoIndex) : clean;
      }),
  })))()`);
}

async function waitForReplyVerification(
  page: Awaited<ReturnType<typeof openReadonlyXPage>>,
  tweetUrl: string,
  expectedReplyText: string | undefined,
  timeoutMs: number,
): Promise<ThreadClassification> {
  const startedAt = Date.now();
  let reloaded = false;
  const resolvedShortUrls = new Map<string, string | undefined>();

  while (true) {
    const articles = await readArticles(page);
    const result = classifyThread(articles, tweetUrl, expectedReplyText);
    if (replyVerificationPending(result, expectedReplyText)
      && result.mainPostFound
      && await replyCardMatchesExpectedRepo(page, articles, expectedReplyText, resolvedShortUrls)) {
      return { mainPostFound: true, replyFound: true };
    }
    if (!replyVerificationPending(result, expectedReplyText)) return result;

    const elapsedMs = Date.now() - startedAt;
    if (elapsedMs >= timeoutMs) return result;

    if (!reloaded && elapsedMs >= timeoutMs / 2) {
      reloaded = true;
      await page.cdp.send('Page.reload', { ignoreCache: true }, { sessionId: page.sessionId });
      await sleep(2_000);
      continue;
    }

    const scrollExpression = result.mainPostFound
      ? 'window.scrollBy({ top: 900, behavior: "instant" })'
      : 'window.scrollTo({ top: 0, behavior: "instant" })';
    await page.evaluate(scrollExpression);
    await sleep(Math.min(750, Math.max(1, timeoutMs - elapsedMs)));
  }
}

function stateResult(
  state: 'login_required' | 'rate_limited' | 'timeout',
  page: Awaited<ReturnType<typeof openReadonlyXPage>>,
): VerifyResult {
  return {
    ok: false,
    state: state === 'timeout' ? 'dom_timeout' : state,
    reusedSession: page.reusedSession,
    launchedChrome: page.launchedChrome,
  };
}

export function githubUrlMatchesRepo(value: string, repoSlug: string): boolean {
  try {
    const url = new URL(value);
    const expectedPath = `/${repoSlug.toLowerCase()}`;
    return /^(?:www\.)?github\.com$/i.test(url.hostname)
      && (url.pathname.toLowerCase() === expectedPath || url.pathname.toLowerCase().startsWith(`${expectedPath}/`));
  } catch {
    return false;
  }
}

async function resolveShortUrl(
  page: Awaited<ReturnType<typeof openReadonlyXPage>>,
  shortUrl: string,
): Promise<string | undefined> {
  const { targetId } = await page.cdp.send<{ targetId: string }>('Target.createTarget', { url: 'about:blank' });
  let sessionId: string | undefined;
  try {
    ({ sessionId } = await page.cdp.send<{ sessionId: string }>(
      'Target.attachToTarget',
      { targetId, flatten: true },
    ));
    await page.cdp.send('Page.enable', {}, { sessionId });
    await page.cdp.send('Page.navigate', { url: shortUrl }, { sessionId });
    for (let attempt = 0; attempt < 8; attempt += 1) {
      await sleep(250);
      const location = await page.cdp.send<{ result: { value?: string } }>('Runtime.evaluate', {
        expression: 'location.href',
        returnByValue: true,
      }, { sessionId });
      const value = location.result.value;
      if (value && !/^https?:\/\/t\.co\//i.test(value)) return value;
    }
  } finally {
    if (sessionId) {
      try { await page.cdp.send('Target.detachFromTarget', { sessionId }); } catch {}
    }
    try { await page.cdp.send('Target.closeTarget', { targetId }); } catch {}
  }
  return undefined;
}

async function replyCardMatchesExpectedRepo(
  page: Awaited<ReturnType<typeof openReadonlyXPage>>,
  articles: RenderedArticle[],
  expectedReplyText: string | undefined,
  resolvedShortUrls: Map<string, string | undefined>,
): Promise<boolean> {
  if (!expectedReplyText) return false;
  const repoSlug = repoSlugFromReplyText(expectedReplyText);
  const urlStart = expectedReplyText.search(/https?:\/\//i);
  const label = normalizeText(urlStart >= 0 ? expectedReplyText.slice(0, urlStart) : expectedReplyText);
  if (!repoSlug || !label) return false;

  for (const article of articles) {
    if (!normalizeText(article.text).includes(label)) continue;
    for (const link of article.links) {
      if (githubUrlMatchesRepo(link, repoSlug)) return true;
      if (!/^https:\/\/t\.co\//i.test(link)) continue;
      if (!resolvedShortUrls.has(link)) resolvedShortUrls.set(link, await resolveShortUrl(page, link));
      if (githubUrlMatchesRepo(resolvedShortUrls.get(link) ?? '', repoSlug)) return true;
    }
  }
  return false;
}

export async function verifyPostWithReply(options: VerifyOptions): Promise<VerifyResult> {
  const initialUrl = options.healthCheck
    ? 'https://x.com/home'
    : options.tweetUrl
      ? normalizeTweetUrl(options.tweetUrl)!
      : `https://x.com/search?q=${encodeURIComponent(`from:${options.handle} "${options.mainQuery}"`)}&src=typed_query&f=live`;
  const page = await openReadonlyXPage({
    url: initialUrl,
    profileDir: options.profileDir,
    keepOpen: options.keepOpen,
  });
  try {
    let rendered = await waitForXRenderedContent(page, {
      timeoutMs: options.timeoutMs,
      requireArticle: true,
      reloadOnce: true,
    });
    if (rendered.state !== 'ready') return stateResult(rendered.state, page);
    if (options.healthCheck) {
      return {
        ok: true,
        state: 'ready',
        reusedSession: page.reusedSession,
        launchedChrome: page.launchedChrome,
      };
    }

    let mainPostUrl = options.tweetUrl ? normalizeTweetUrl(options.tweetUrl)! : undefined;
    if (!mainPostUrl) {
      const searchArticles = await readArticles(page);
      mainPostUrl = findMainPostUrl(searchArticles, options.handle!, options.mainQuery!);
      if (!mainPostUrl) {
        return {
          ok: false,
          state: 'not_found',
          mainPostFound: false,
          replyFound: false,
          repoSlug: options.repoSlug,
          reusedSession: page.reusedSession,
          launchedChrome: page.launchedChrome,
        };
      }
      await page.navigate(mainPostUrl);
      rendered = await waitForXRenderedContent(page, {
        timeoutMs: options.timeoutMs,
        requireArticle: true,
        reloadOnce: true,
      });
      if (rendered.state !== 'ready') return stateResult(rendered.state, page);
    }

    const expectedReplyText = expectedReply(options);
    const result = await waitForReplyVerification(page, mainPostUrl, expectedReplyText, options.timeoutMs);
    const replyRequired = Boolean(expectedReplyText);
    const ok = result.mainPostFound && (!replyRequired || result.replyFound);
    return {
      ok,
      state: ok ? 'verified' : result.mainPostFound ? 'main_only' : 'not_found',
      mainPostUrl,
      mainPostFound: result.mainPostFound,
      replyFound: replyRequired ? result.replyFound : undefined,
      repoSlug: options.repoSlug,
      reusedSession: page.reusedSession,
      launchedChrome: page.launchedChrome,
    };
  } finally {
    await page.close();
  }
}

if (import.meta.main) {
  try {
    const options = parseArgs(process.argv.slice(2));
    const result = await verifyPostWithReply(options);
    console.log(JSON.stringify(result));
    if (!result.ok) process.exitCode = 2;
  } catch (error) {
    const result: VerifyResult = {
      ok: false,
      state: 'error',
      error: error instanceof Error ? error.message : String(error),
    };
    console.log(JSON.stringify(result));
    process.exitCode = 1;
  }
}
