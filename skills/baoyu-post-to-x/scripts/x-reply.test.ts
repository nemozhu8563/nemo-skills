import { describe, expect, test } from 'bun:test';

import { replyAppearsOnPostPage, repoSlugFromReplyText } from './x-reply.js';

const expected = '项目地址：https://github.com/shareAI-lab/learn-claude-code';

describe('reply confirmation', () => {
  test('accepts the original reply text when it remains visible', () => {
    expect(replyAppearsOnPostPage({ text: expected, links: [] }, expected)).toBe(true);
  });

  test('accepts X GitHub cards that replace the raw URL', () => {
    expect(replyAppearsOnPostPage({
      text: '项目地址：\nshareAI-lab/learn-claude-code\nBash is all you need',
      links: ['https://t.co/example'],
    }, expected)).toBe(true);
  });

  test('accepts a card link even when the card title has not rendered', () => {
    expect(replyAppearsOnPostPage({
      text: '项目地址：',
      links: ['https://github.com/shareAI-lab/learn-claude-code'],
    }, expected)).toBe(true);
  });

  test('does not accept a different GitHub card or an unrelated label', () => {
    expect(replyAppearsOnPostPage({
      text: '项目地址：\nshareAI-lab/another-repo',
      links: [],
    }, expected)).toBe(false);
    expect(replyAppearsOnPostPage({
      text: '推荐项目：\nshareAI-lab/learn-claude-code',
      links: [],
    }, expected)).toBe(false);
  });

  test('extracts a normalized repository slug', () => {
    expect(repoSlugFromReplyText('项目地址：https://github.com/ShareAI-Lab/learn-claude-code?tab=readme')).toBe('shareai-lab/learn-claude-code');
  });
});
