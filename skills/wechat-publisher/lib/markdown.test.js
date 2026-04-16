import { afterEach, describe, expect, it } from 'bun:test';
import { parseMarkdown } from './markdown.js';
import { writeFile, rm } from 'fs/promises';
import { join } from 'path';
import { tmpdir } from 'os';

const tempFiles = [];

async function writeTempFile(name, content) {
  const filePath = join(tmpdir(), `${Date.now()}-${Math.random().toString(16).slice(2)}-${name}`);
  await writeFile(filePath, content, 'utf-8');
  tempFiles.push(filePath);
  return filePath;
}

afterEach(async () => {
  while (tempFiles.length > 0) {
    await rm(tempFiles.pop(), { force: true });
  }
});

describe('Markdown Parser', () => {
  it('removes frontmatter', async () => {
    const content = `---
title: Test Title
tags: [test, markdown]
---

# Main Content

This is the main content.`;

    const filePath = await writeTempFile('test-frontmatter.md', content);
    const result = await parseMarkdown(filePath);

    expect(result.content).not.toContain('title: Test Title');
    expect(result.content).toContain('# Main Content');
    expect(result.frontmatter.title).toBe('Test Title');
    expect(result.frontmatter.tags).toEqual(['test', 'markdown']);
  });

  it('converts wikilinks to plain text', async () => {
    const content = `Check out [[My Page]] and [[Another Page|display text]] for more info.`;

    const filePath = await writeTempFile('test-wikilinks.md', content);
    const result = await parseMarkdown(filePath);

    expect(result.content).not.toContain('[[');
    expect(result.content).toContain('My Page');
    expect(result.content).toContain('display text');
  });

  it('removes standalone tags while keeping inline tags', async () => {
    const content = `# Article Title

This is content with #inline tags.

#tag1 #tag2`;

    const filePath = await writeTempFile('test-tags.md', content);
    const result = await parseMarkdown(filePath);

    expect(result.content).toContain('#inline');
    expect(result.content).not.toMatch(/\n#tag1/);
  });

  it('extracts local and remote images', async () => {
    const content = `# Article

![remote](https://example.com/image.png)
![local](./images/local.png)`;

    const filePath = await writeTempFile('test-images.md', content);
    const result = await parseMarkdown(filePath);

    expect(result.images.remote).toHaveLength(1);
    expect(result.images.local).toHaveLength(1);
    expect(result.images.remote[0].url).toBe('https://example.com/image.png');
    expect(result.images.local[0].path).toBe('./images/local.png');
  });

  it('converts obsidian embeds into local images', async () => {
    const content = `# Article

![[./assets/cover.png]]
![[../images/figure-1.png]]`;

    const filePath = await writeTempFile('test-obsidian-embeds.md', content);
    const result = await parseMarkdown(filePath);

    expect(result.images.local).toHaveLength(2);
    expect(result.content).toContain('![](./assets/cover.png)');
    expect(result.content).toContain('![](../images/figure-1.png)');
  });

  it('strips trailing Links section', async () => {
    const content = `# Article

正文内容

## Links

- [[Page One]]
- [[Page Two]]`;

    const filePath = await writeTempFile('test-links-section.md', content);
    const result = await parseMarkdown(filePath);

    expect(result.content).toContain('正文内容');
    expect(result.content).not.toContain('## Links');
    expect(result.content).not.toContain('Page One');
  });
});
