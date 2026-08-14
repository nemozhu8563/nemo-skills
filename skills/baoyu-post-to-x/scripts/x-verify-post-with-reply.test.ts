import { describe, expect, test } from 'bun:test';

import {
  classifyThread,
  findMainPostUrl,
  githubUrlMatchesRepo,
  normalizeTweetUrl,
  replyVerificationPending,
} from './x-verify-post-with-reply.js';
import { TIMELINE_EXTRACTION_EXPRESSION } from './x-timeline-dom.js';

describe('read-only X post verification', () => {
  test('keeps the timeline extraction expression syntactically valid', () => {
    expect(() => new Function('document', `return ${TIMELINE_EXTRACTION_EXPRESSION}`)).not.toThrow();
    expect(TIMELINE_EXTRACTION_EXPRESSION).toContain('项目地址');
  });

  test('normalizes x.com and twitter.com status URLs', () => {
    expect(normalizeTweetUrl('https://twitter.com/nemoisme/status/123?ref=home')).toBe('https://x.com/nemoisme/status/123');
    expect(normalizeTweetUrl('not-a-post')).toBeNull();
  });

  test('finds an account-owned post from live search results', () => {
    const articles = [{
      text: 'A useful repository for resilient agents',
      links: [],
      statusUrls: ['https://x.com/nemoisme/status/123'],
    }, {
      text: 'A useful repository for resilient agents',
      links: [],
      statusUrls: ['https://x.com/someone_else/status/456'],
    }];
    expect(findMainPostUrl(articles, 'nemoisme', 'useful repository')).toBe('https://x.com/nemoisme/status/123');
  });

  test('requires the repository reply to be a distinct rendered article', () => {
    const expectedReply = '项目地址：https://github.com/acme/project';
    expect(classifyThread([{
      text: 'Main post',
      links: ['https://x.com/nemoisme/status/123'],
      statusUrls: ['https://x.com/nemoisme/status/123'],
    }, {
      text: '项目地址：github.com/acme/project',
      links: ['https://github.com/acme/project'],
      statusUrls: ['https://x.com/nemoisme/status/124'],
    }], 'https://x.com/nemoisme/status/123', expectedReply)).toEqual({
      mainPostFound: true,
      replyFound: true,
    });

    expect(classifyThread([{
      text: `Main post ${expectedReply}`,
      links: ['https://x.com/nemoisme/status/123', 'https://github.com/acme/project'],
      statusUrls: ['https://x.com/nemoisme/status/123'],
    }], 'https://x.com/nemoisme/status/123', expectedReply)).toEqual({
      mainPostFound: true,
      replyFound: false,
    });
  });

  test('keeps polling after the main post renders before its reply', () => {
    const expectedReply = '项目地址：https://github.com/acme/project';
    expect(replyVerificationPending({ mainPostFound: false, replyFound: false }, expectedReply)).toBe(true);
    const mainOnly = classifyThread([{
      text: 'Main post',
      links: ['https://x.com/nemoisme/status/123'],
      statusUrls: ['https://x.com/nemoisme/status/123'],
    }], 'https://x.com/nemoisme/status/123', expectedReply);
    expect(replyVerificationPending(mainOnly, expectedReply)).toBe(true);

    const verified = classifyThread([{
      text: 'Main post',
      links: ['https://x.com/nemoisme/status/123'],
      statusUrls: ['https://x.com/nemoisme/status/123'],
    }, {
      text: '项目地址：acme/project',
      links: ['https://github.com/acme/project'],
      statusUrls: ['https://x.com/nemoisme/status/124'],
    }], 'https://x.com/nemoisme/status/123', expectedReply);
    expect(replyVerificationPending(verified, expectedReply)).toBe(false);
  });

  test('requires a short-link destination to match the exact GitHub repository path', () => {
    expect(githubUrlMatchesRepo('https://github.com/acme/project', 'acme/project')).toBe(true);
    expect(githubUrlMatchesRepo('https://github.com/acme/project/issues', 'acme/project')).toBe(true);
    expect(githubUrlMatchesRepo('https://github.com/acme/project-extra', 'acme/project')).toBe(false);
  });
});
