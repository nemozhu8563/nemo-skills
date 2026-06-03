const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const {
  convertToObsidianFormat,
  stripZhihuPlaceholderImageNotice
} = require('./convert');

function makeTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'article-clip-obsidian-'));
}

function writeArticlePackage(root, content, assets = {}) {
  fs.mkdirSync(root, { recursive: true });
  fs.writeFileSync(path.join(root, 'content.md'), content, 'utf-8');

  const assetNames = Object.keys(assets);
  if (assetNames.length > 0) {
    const assetsDir = path.join(root, 'assets');
    fs.mkdirSync(assetsDir, { recursive: true });
    for (const name of assetNames) {
      fs.writeFileSync(path.join(assetsDir, name), assets[name]);
    }
  }

  return path.join(root, 'content.md');
}

test('converts article package to Obsidian note and wiki-linked assets', () => {
  const root = makeTempDir();
  const packageDir = path.join(root, 'package');
  const outputDir = path.join(root, 'clippings');
  const assetsDir = path.join(root, 'vault-assets');
  fs.mkdirSync(outputDir, { recursive: true });

  const sourcePath = writeArticlePackage(
    packageDir,
    `---
title: "A Useful Article About Agents"
source_url: "https://example.com/articles/agents"
fetched_at: "2026-05-03T10:20:00+08:00"
published_at: "2026-05-01T09:00:00+08:00"
author: "Nemo"
platform: "web"
---
# A Useful Article About Agents

Intro paragraph.

![diagram](./assets/001.jpg)
`,
    { '001.jpg': 'image bytes' }
  );

  const result = convertToObsidianFormat(sourcePath, outputDir, assetsDir);

  assert.equal(result.filename, '202605031020 A Useful Article About Agents.md');
  assert.equal(result.imageCount, 1);
  assert.equal(fs.existsSync(result.outputPath), true);
  assert.equal(fs.existsSync(path.join(result.assetsDir, '001.jpg')), true);

  const converted = fs.readFileSync(result.outputPath, 'utf-8');
  assert.match(converted, /type: source/);
  assert.match(converted, /created: 2026-05-01/);
  assert.match(converted, /source: "A Useful Article About Agents"/);
  assert.match(converted, /author: "Nemo"/);
  assert.match(converted, /- "https:\/\/example.com\/articles\/agents"/);
  assert.match(converted, /!\[\[assets\/202605031020 A Useful Article About Agents\/001\.jpg\]\]/);
});

test('unwraps linked image embeds into plain Obsidian image embeds', () => {
  const root = makeTempDir();
  const packageDir = path.join(root, 'package');
  const outputDir = path.join(root, 'clippings');
  const assetsDir = path.join(root, 'vault-assets');
  fs.mkdirSync(outputDir, { recursive: true });

  const sourcePath = writeArticlePackage(
    packageDir,
    `---
title: "Linked Image Article"
source_url: "https://x.com/example/status/1"
fetched_at: "2026-05-03T10:20:00+08:00"
published_at: "2026-05-03T10:20:00+08:00"
---
# Linked Image Article

[![Image 1: Image](./assets/001.jpg)](https://x.com/example/status/1/photo/1)
`,
    { '001.jpg': 'image bytes' }
  );

  const result = convertToObsidianFormat(sourcePath, outputDir, assetsDir);
  const converted = fs.readFileSync(result.outputPath, 'utf-8');

  assert.match(converted, /!\[\[assets\/202605031020 Linked Image Article\/001\.jpg\]\]/);
  assert.doesNotMatch(converted, /\[!\[\[assets\//);
  assert.doesNotMatch(converted, /\]\(https:\/\/x\.com\/example\/status\/1\/photo\/1\)/);
});

test('sanitizes noisy titles consistently for filenames and source field', () => {
  const root = makeTempDir();
  const packageDir = path.join(root, 'package');
  const outputDir = path.join(root, 'clippings');
  const assetsDir = path.join(root, 'vault-assets');
  fs.mkdirSync(outputDir, { recursive: true });

  const sourcePath = writeArticlePackage(
    packageDir,
    `---
title: "..A <Very> Long / Invalid: Article? Title* With Extra Words That Should Be Truncated 123456"
source_url: "https://example.com/long"
fetched_at: "2026-05-03T11:00:00+08:00"
published_at: "2026-05-03T11:00:00+08:00"
---
Tiny.
`
  );

  const result = convertToObsidianFormat(sourcePath, outputDir, assetsDir);

  assert.equal(result.filename, '202605031100 A Very Long Invalid Article Title With E.md');

  const converted = fs.readFileSync(result.outputPath, 'utf-8');
  assert.match(converted, /source: "A <Very> Long \/ Invalid: Article\? Title\* With Extra Words That Should Be Truncated"/);
});

test('keeps full source title while truncating only the filename', () => {
  const root = makeTempDir();
  const packageDir = path.join(root, 'package');
  const outputDir = path.join(root, 'clippings');
  const assetsDir = path.join(root, 'vault-assets');
  fs.mkdirSync(outputDir, { recursive: true });

  const longTitle = '似乎佛教有一个观点叫“不着相”，“不着相”指的是什么？ - 浮梦子的回答 - 知乎';
  const sourcePath = writeArticlePackage(
    packageDir,
    `---
title: "${longTitle}"
source_url: "https://www.zhihu.com/question/1/answer/2"
fetched_at: "2026-06-03T15:47:00+08:00"
published_at: "2025-11-25T12:49:20+08:00"
author: "浮梦子"
platform: "zhihu"
---
# ${longTitle}

正文。
`
  );

  const result = convertToObsidianFormat(sourcePath, outputDir, assetsDir);
  const converted = fs.readFileSync(result.outputPath, 'utf-8');

  assert.equal(result.filename, '202606031547 似乎佛教有一个观点叫“不着相”，“不着相”指的是什么？ - 浮梦子的回答 - 知.md');
  assert.match(converted, new RegExp(`source: "${longTitle}"`));
});

test('escapes quoted source urls and authors in YAML frontmatter', () => {
  const root = makeTempDir();
  const packageDir = path.join(root, 'package');
  const outputDir = path.join(root, 'clippings');
  const assetsDir = path.join(root, 'vault-assets');
  fs.mkdirSync(outputDir, { recursive: true });

  const sourcePath = writeArticlePackage(
    packageDir,
    `---
title: "Quoted Article"
source_url: https://example.com/articles?query="agents"
fetched_at: "2026-05-03T11:00:00+08:00"
published_at: "2026-05-03T11:00:00+08:00"
author: A "Quoted" Author
---
# Quoted Article

Body.
`
  );

  const result = convertToObsidianFormat(sourcePath, outputDir, assetsDir);
  const converted = fs.readFileSync(result.outputPath, 'utf-8');

  assert.match(converted, /- "https:\/\/example\.com\/articles\?query=\\"agents\\""/);
  assert.match(converted, /author: "A \\"Quoted\\" Author"/);
});

test('removes Zhihu placeholder-only image notices', () => {
  const body = `Main answer text.

---

## 图片下载提示

部分图片使用在线链接：

• 001.jpg (下载失败)
• 002.png (下载失败)
`;

  const cleaned = stripZhihuPlaceholderImageNotice(body, { platform: 'zhihu' });

  assert.equal(cleaned, 'Main answer text.');
});

test('keeps Zhihu image notice when real image references exist', () => {
  const body = `Main answer text.

![real](https://example.com/real.jpg)

---

## 图片下载提示

部分图片使用在线链接：

• 001.jpg (下载失败)
`;

  const cleaned = stripZhihuPlaceholderImageNotice(body, { platform: 'zhihu' });

  assert.equal(cleaned, body);
});

test('fails clearly when frontmatter dates are missing', () => {
  const root = makeTempDir();
  const packageDir = path.join(root, 'package');
  const outputDir = path.join(root, 'clippings');
  const assetsDir = path.join(root, 'vault-assets');
  fs.mkdirSync(outputDir, { recursive: true });

  const sourcePath = writeArticlePackage(
    packageDir,
    'This package has no frontmatter but still has enough body text for a title.'
  );

  assert.throws(
    () => convertToObsidianFormat(sourcePath, outputDir, assetsDir),
    /Missing required date field: fetched_at/
  );
});

test('does not overwrite an existing clipping file', () => {
  const root = makeTempDir();
  const packageDir = path.join(root, 'package');
  const outputDir = path.join(root, 'clippings');
  const assetsDir = path.join(root, 'vault-assets');
  fs.mkdirSync(outputDir, { recursive: true });

  const sourcePath = writeArticlePackage(
    packageDir,
    `---
title: "Duplicate Article"
source_url: "https://example.com/duplicate"
fetched_at: "2026-05-03T11:00:00+08:00"
published_at: "2026-05-03T11:00:00+08:00"
---
# Duplicate Article

Body.
`
  );

  const existingPath = path.join(outputDir, '202605031100 Duplicate Article.md');
  fs.writeFileSync(existingPath, 'existing clipping', 'utf-8');

  assert.throws(
    () => convertToObsidianFormat(sourcePath, outputDir, assetsDir),
    /Output file already exists/
  );
  assert.equal(fs.readFileSync(existingPath, 'utf-8'), 'existing clipping');
});
