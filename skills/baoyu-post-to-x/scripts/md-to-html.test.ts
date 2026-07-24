import { afterEach, describe, expect, test } from 'bun:test';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

import { parseMarkdown } from './md-to-html.js';

const tempDirs: string[] = [];

async function parseFixture(markdown: string) {
  const dir = await mkdtemp(path.join(os.tmpdir(), 'baoyu-post-to-x-test-'));
  tempDirs.push(dir);
  const markdownPath = path.join(dir, 'article.md');
  await writeFile(markdownPath, markdown, 'utf8');
  return parseMarkdown(markdownPath, { tempDir: path.join(dir, 'images') });
}

afterEach(async () => {
  await Promise.all(tempDirs.splice(0).map((dir) => rm(dir, { recursive: true, force: true })));
});

describe('x-plain fenced blocks', () => {
  test('preserves exact configuration text without blockquote or inline Markdown', async () => {
    const result = await parseFixture([
      '# Test',
      '',
      '```x-plain',
      '[features.multi_agent_v2]',
      'max_concurrent_threads_per_session = 7',
      'model = "<verified_model>"',
      '**keep these characters literal**',
      '```',
    ].join('\n'));

    expect(result.html).toBe(
      '<p>[features.multi_agent_v2]<br>max_concurrent_threads_per_session = 7<br>model = &quot;&lt;verified_model&gt;&quot;<br>**keep these characters literal**</p>',
    );
    expect(result.html).not.toContain('<blockquote>');
    expect(result.html).not.toContain('<em>');
    expect(result.html).not.toContain('<strong>');
  });

  test('does not let a shorter nested fence close a longer outer fence', async () => {
    const result = await parseFixture([
      '# Test',
      '',
      '````text',
      'before',
      '```toml',
      'value_with_underscores = true',
      '```',
      'after',
      '````',
    ].join('\n'));

    expect(result.html).toBe(
      '<blockquote>before<br>```toml<br>value_with_underscores = true<br>```<br>after</blockquote>',
    );
  });
});
