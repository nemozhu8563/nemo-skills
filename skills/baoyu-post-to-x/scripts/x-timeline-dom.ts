import process from 'node:process';

import { openReadonlyXPage, waitForXRenderedContent } from './x-readonly.js';
import { sleep } from './x-utils.js';

interface TimelineOptions {
  handle: string;
  maxScrollScreens: number;
  scrollY: number;
  scrollWaitMs: number;
  timeoutMs: number;
  profileDir?: string;
  keepOpen: boolean;
}

export interface TimelineDomResult {
  ok: boolean;
  state: 'ready' | 'login_required' | 'rate_limited' | 'dom_timeout' | 'error';
  handle: string;
  htmlSnapshots: string[];
  articleCounts: number[];
  reusedSession?: boolean;
  launchedChrome?: boolean;
  error?: string;
}

export const TIMELINE_EXTRACTION_EXPRESSION = `(() => {
  const esc = (value) => String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
  const textOf = (node) => (node && node.innerText ? node.innerText.trim() : '');
  const attr = (node, name) => node ? node.getAttribute(name) || '' : '';
  const firstStatusLink = (article) => Array.from(article.querySelectorAll('a[href*="/status/"]'))
    .map((link) => attr(link, 'href'))
    .find((href) => href.includes('/status/') && /[0-9]+/.test(href.split('/status/')[1] || '')) || '';
  const statusId = (href) => ((href.split('/status/')[1] || '').match(/[0-9]+/) || [])[0] || '';
  const ownerFromHref = (href) => {
    try {
      const parts = new URL(href, 'https://x.com').pathname.split('/').filter(Boolean);
      return parts[1] === 'status' ? parts[0] || '' : '';
    } catch {
      return '';
    }
  };
  const parseMetric = (label, names) => {
    if (!label) return '';
    for (const name of names) {
      const re = new RegExp('([0-9][0-9,.]*\\\\s*(?:[KkMm]|万|亿)?)\\\\s*' + name, 'i');
      const match = label.match(re);
      if (match) return match[1].replace(/\\s+/g, '');
    }
    return '';
  };
  const kindOf = (article) => {
    const text = textOf(article);
    if (/reposted/i.test(text)) return 'repost';
    if (/Replying to|正在回复|回复\s*@|回复给/i.test(text)) return 'reply';
    if (/^项目地址\s*[:：]/.test(textOf(article.querySelector('[data-testid="tweetText"]')))) return 'reply';
    return article.querySelectorAll('article[data-testid="tweet"], article').length > 1 ? 'quote' : 'original';
  };
  const articles = Array.from(document.querySelectorAll('article[data-testid="tweet"], article'));
  return articles.map((article) => {
    const href = firstStatusLink(article);
    const time = article.querySelector('time');
    const textNode = article.querySelector('[data-testid="tweetText"]');
    const label = Array.from(article.querySelectorAll('[role="group"], [aria-label]')).map((node) => attr(node, 'aria-label')).filter(Boolean).join(' ');
    return '<article data-tweet-id="' + esc(statusId(href)) + '" data-x-ops-owner="' + esc(ownerFromHref(href)) + '" data-x-ops-kind="' + esc(kindOf(article)) + '" data-views="' + esc(parseMetric(label, ['views?', '次查看', '次观看'])) + '" data-likes="' + esc(parseMetric(label, ['likes?', '喜欢次数', '喜欢'])) + '" data-reposts="' + esc(parseMetric(label, ['reposts?', 'retweets?', '次转帖', '转帖'])) + '" data-replies="' + esc(parseMetric(label, ['replies?', '回复'])) + '" data-bookmarks="' + esc(parseMetric(label, ['bookmarks?', '书签'])) + '"><a href="' + esc(href) + '"></a><time datetime="' + esc(attr(time, 'datetime')) + '"></time><div data-testid="tweetText">' + esc(textOf(textNode)) + '</div></article>';
  }).join('\\n');
})()`;

function normalizeHandle(value: string): string {
  const normalized = value.trim().replace(/^@/, '');
  if (!/^[A-Za-z0-9_]{1,15}$/.test(normalized)) throw new Error(`Invalid X handle: ${value}`);
  return normalized;
}

function parseArgs(args: string[]): TimelineOptions {
  const options: TimelineOptions = {
    handle: '',
    maxScrollScreens: 3,
    scrollY: 1400,
    scrollWaitMs: 800,
    timeoutMs: 45_000,
    keepOpen: false,
  };
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index]!;
    const value = args[index + 1];
    if (arg === '--handle' && value) options.handle = normalizeHandle(args[++index]!);
    else if (arg === '--profile' && value) options.profileDir = args[++index]!;
    else if (arg === '--max-scroll-screens' && value) options.maxScrollScreens = Number(args[++index]);
    else if (arg === '--scroll-y' && value) options.scrollY = Number(args[++index]);
    else if (arg === '--scroll-wait-ms' && value) options.scrollWaitMs = Number(args[++index]);
    else if (arg === '--timeout-ms' && value) options.timeoutMs = Number(args[++index]);
    else if (arg === '--keep-open') options.keepOpen = true;
    else throw new Error(`Unknown or incomplete argument: ${arg}`);
  }
  if (!options.handle) throw new Error('--handle is required.');
  if (!Number.isInteger(options.maxScrollScreens) || options.maxScrollScreens < 0 || options.maxScrollScreens > 8) {
    throw new Error('--max-scroll-screens must be an integer between 0 and 8.');
  }
  for (const [name, value] of [
    ['--scroll-y', options.scrollY],
    ['--scroll-wait-ms', options.scrollWaitMs],
    ['--timeout-ms', options.timeoutMs],
  ] as const) {
    if (!Number.isFinite(value) || value <= 0) throw new Error(`${name} must be positive.`);
  }
  return options;
}

async function articleCount(page: Awaited<ReturnType<typeof openReadonlyXPage>>): Promise<number> {
  return page.evaluate<number>('document.querySelectorAll(\'article[data-testid="tweet"], article\').length');
}

async function waitForMoreArticles(
  page: Awaited<ReturnType<typeof openReadonlyXPage>>,
  before: number,
  timeoutMs: number,
): Promise<number> {
  const startedAt = Date.now();
  let current = before;
  while (Date.now() - startedAt < timeoutMs) {
    current = await articleCount(page);
    if (current > before) return current;
    await sleep(200);
  }
  return current;
}

export async function collectTimelineDom(options: TimelineOptions): Promise<TimelineDomResult> {
  const page = await openReadonlyXPage({
    url: `https://x.com/${options.handle}`,
    profileDir: options.profileDir,
    keepOpen: options.keepOpen,
  });
  try {
    const rendered = await waitForXRenderedContent(page, {
      timeoutMs: options.timeoutMs,
      requireArticle: true,
      reloadOnce: true,
    });
    if (rendered.state !== 'ready') {
      return {
        ok: false,
        state: rendered.state === 'timeout' ? 'dom_timeout' : rendered.state,
        handle: options.handle,
        htmlSnapshots: [],
        articleCounts: [rendered.articleCount],
        reusedSession: page.reusedSession,
        launchedChrome: page.launchedChrome,
      };
    }

    const htmlSnapshots: string[] = [];
    const articleCounts: number[] = [];
    for (let screen = 0; screen <= options.maxScrollScreens; screen += 1) {
      const count = await articleCount(page);
      articleCounts.push(count);
      htmlSnapshots.push(await page.evaluate<string>(TIMELINE_EXTRACTION_EXPRESSION));
      if (screen === options.maxScrollScreens) break;
      await page.evaluate<void>(`window.scrollBy({ top: ${Math.round(options.scrollY)}, left: 0, behavior: 'instant' })`);
      await waitForMoreArticles(page, count, options.scrollWaitMs);
    }
    return {
      ok: true,
      state: 'ready',
      handle: options.handle,
      htmlSnapshots,
      articleCounts,
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
    const result = await collectTimelineDom(options);
    console.log(JSON.stringify(result));
    if (!result.ok) process.exitCode = 2;
  } catch (error) {
    const result: TimelineDomResult = {
      ok: false,
      state: 'error',
      handle: '',
      htmlSnapshots: [],
      articleCounts: [],
      error: error instanceof Error ? error.message : String(error),
    };
    console.log(JSON.stringify(result));
    process.exitCode = 1;
  }
}
