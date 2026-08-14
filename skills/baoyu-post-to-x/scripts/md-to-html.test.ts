import { afterEach, describe, expect, test } from 'bun:test';
import { mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

import { parseMarkdown } from './md-to-html.js';

const tempDirs: string[] = [];

async function parseFixture(
  markdown: string,
  options?: { coverImage?: string; files?: Record<string, string> },
) {
  const dir = await mkdtemp(path.join(os.tmpdir(), 'baoyu-post-to-x-test-'));
  tempDirs.push(dir);
  const markdownPath = path.join(dir, 'article.md');
  await writeFile(markdownPath, markdown, 'utf8');
  for (const [relativePath, content] of Object.entries(options?.files ?? {})) {
    const filePath = path.join(dir, relativePath);
    await mkdir(path.dirname(filePath), { recursive: true });
    await writeFile(filePath, content, 'utf8');
  }
  return parseMarkdown(markdownPath, {
    coverImage: options?.coverImage,
    tempDir: path.join(dir, 'images'),
  });
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

describe('cover image handling', () => {
  test('uses the first inline image as cover when no cover is otherwise selected', async () => {
    const result = await parseFixture([
      '# Test',
      '',
      '![](./cover.png)',
      '',
      '![](./step.png)',
    ].join('\n'), {
      files: {
        'cover.png': 'cover-image',
        'step.png': 'step-image',
      },
    });

    expect(path.basename(result.coverImage!)).toBe('cover.png');
    expect(result.contentImages.map((image) => path.basename(image.localPath))).toEqual(['step.png']);
    expect(result.html).not.toContain('[[IMAGE_PLACEHOLDER_1]]');
    expect(result.html).toContain('[[IMAGE_PLACEHOLDER_2]]');
  });

  test('deduplicates an explicit cover that is also the first inline image', async () => {
    const result = await parseFixture([
      '# Test',
      '',
      '![](./cover.png)',
      '',
      'Step one',
      '',
      '![](./step.png)',
    ].join('\n'), {
      coverImage: './cover.png',
      files: {
        'cover.png': 'cover-image',
        'step.png': 'step-image',
      },
    });

    expect(path.basename(result.coverImage!)).toBe('cover.png');
    expect(result.contentImages.map((image) => path.basename(image.localPath))).toEqual(['step.png']);
    expect(result.html).not.toContain('[[IMAGE_PLACEHOLDER_1]]');
    expect(result.html).toContain('[[IMAGE_PLACEHOLDER_2]]');
  });

  test('deduplicates a frontmatter cover that is also the first inline image', async () => {
    const result = await parseFixture([
      '---',
      'cover_image: ./cover.png',
      '---',
      '# Test',
      '',
      '![](./cover.png)',
      '',
      '![](./step.png)',
    ].join('\n'), {
      files: {
        'cover.png': 'cover-image',
        'step.png': 'step-image',
      },
    });

    expect(path.basename(result.coverImage!)).toBe('cover.png');
    expect(result.contentImages.map((image) => path.basename(image.localPath))).toEqual(['step.png']);
    expect(result.html).not.toContain('[[IMAGE_PLACEHOLDER_1]]');
    expect(result.html).toContain('[[IMAGE_PLACEHOLDER_2]]');
  });

  test('keeps the first inline image when the selected cover is a different file', async () => {
    const result = await parseFixture([
      '# Test',
      '',
      '![](./step-one.png)',
      '',
      '![](./step-two.png)',
    ].join('\n'), {
      coverImage: './cover.png',
      files: {
        'cover.png': 'cover-image',
        'step-one.png': 'step-one-image',
        'step-two.png': 'step-two-image',
      },
    });

    expect(result.contentImages.map((image) => path.basename(image.localPath))).toEqual([
      'step-one.png',
      'step-two.png',
    ]);
    expect(result.html).toContain('[[IMAGE_PLACEHOLDER_1]]');
    expect(result.html).toContain('[[IMAGE_PLACEHOLDER_2]]');
  });
});
