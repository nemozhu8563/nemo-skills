const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const { convertToObsidianFormat } = require('./convert');
const {
  createArticlePackage,
  extractRemoteImageReferences,
  localizeRemoteImages,
  normalizeCapture,
  rewriteAssetReferences
} = require('./web-access-adapter');

function makeTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'web-access-adapter-'));
}

test('normalizes web-access capture metadata into converter frontmatter fields', () => {
  const normalized = normalizeCapture({
    metadata: {
      url: 'https://example.com/articles/deep-work',
      title: 'Deep Work for Agents',
      author: 'Nemo',
      published: '2026-05-01T09:00:00+08:00',
      captured_at: '2026-05-03T10:20:00+08:00'
    },
    markdown: '# Deep Work for Agents\n\nArticle body.'
  });

  assert.equal(normalized.title, 'Deep Work for Agents');
  assert.equal(normalized.source_url, 'https://example.com/articles/deep-work');
  assert.equal(normalized.author, 'Nemo');
  assert.equal(normalized.published_at, '2026-05-01T09:00:00+08:00');
  assert.equal(normalized.fetched_at, '2026-05-03T10:20:00+08:00');
  assert.equal(normalized.platform, 'example.com');
});

test('falls back to capture time and URL-derived title when metadata is sparse', () => {
  const normalized = normalizeCapture({
    url: 'https://example.com/posts/url-derived-title',
    captured_at: '2026-05-03T11:00:00+08:00',
    markdown: '![cover](https://example.com/cover.jpg)'
  });

  assert.equal(normalized.title, 'url derived title');
  assert.equal(normalized.published_at, '2026-05-03T11:00:00+08:00');
  assert.equal(normalized.author, 'unknown');
});

function fakeFetch(body = 'remote image bytes', ok = true) {
  return async () => ({
    ok,
    status: ok ? 200 : 503,
    arrayBuffer: async () => Buffer.from(body)
  });
}

test('creates content.md and copies local assets for converter consumption', async () => {
  const root = makeTempDir();
  const sourceAsset = path.join(root, 'source-image.jpg');
  const packageDir = path.join(root, 'package');
  fs.writeFileSync(sourceAsset, 'image bytes');

  const result = await createArticlePackage({
    url: 'https://example.com/articles/assets',
    title: 'Asset Capture Example',
    author: 'Nemo',
    published_at: '2026-05-01T09:00:00+08:00',
    captured_at: '2026-05-03T10:20:00+08:00',
    markdown: `# Asset Capture Example\n\n![cover](${sourceAsset})`,
    assets: [{ path: sourceAsset, filename: '001.jpg' }]
  }, packageDir);

  assert.equal(result.assetCount, 1);
  assert.equal(fs.existsSync(path.join(packageDir, 'assets', '001.jpg')), true);

  const content = fs.readFileSync(result.contentPath, 'utf-8');
  assert.match(content, /title: "Asset Capture Example"/);
  assert.match(content, /source_url: "https:\/\/example.com\/articles\/assets"/);
  assert.match(content, /!\[cover\]\(\.\/assets\/001\.jpg\)/);
});

test('keeps provided asset filenames inside the package assets directory', async () => {
  const root = makeTempDir();
  const sourceAsset = path.join(root, 'source-image.jpg');
  const packageDir = path.join(root, 'package');
  fs.writeFileSync(sourceAsset, 'image bytes');

  await createArticlePackage({
    url: 'https://example.com/articles/assets',
    title: 'Asset Capture Example',
    captured_at: '2026-05-03T10:20:00+08:00',
    markdown: '# Asset Capture Example\n\n![cover](source-image.jpg)',
    assets: [{ path: sourceAsset, filename: '../001.jpg' }]
  }, packageDir);

  assert.equal(fs.existsSync(path.join(packageDir, 'assets', '001.jpg')), true);
  assert.equal(fs.existsSync(path.join(packageDir, '001.jpg')), false);
});

test('downloads and localizes remote Markdown image references', async () => {
  const root = makeTempDir();
  const packageDir = path.join(root, 'package');

  const result = await createArticlePackage({
    url: 'https://example.com/articles/remote-assets',
    title: 'Remote Asset Capture Example',
    captured_at: '2026-05-03T10:20:00+08:00',
    markdown: '# Remote Asset Capture Example\n\n![remote](https://pbs.twimg.com/media/example?format=jpg&name=small)'
  }, packageDir, { fetchImpl: fakeFetch('downloaded remote image') });

  assert.equal(result.assetCount, 1);
  assert.equal(fs.existsSync(path.join(packageDir, 'assets', '001.jpg')), true);

  const content = fs.readFileSync(result.contentPath, 'utf-8');
  assert.match(content, /!\[remote\]\(\.\/assets\/001\.jpg\)/);
  assert.doesNotMatch(content, /pbs\.twimg\.com/);
});

test('fails instead of silently leaving remote image references when download fails', async () => {
  await assert.rejects(
    () => createArticlePackage({
      url: 'https://example.com/articles/remote-assets',
      title: 'Remote Asset Capture Example',
      captured_at: '2026-05-03T10:20:00+08:00',
      markdown: '# Remote Asset Capture Example\n\n![remote](https://pbs.twimg.com/media/example?format=jpg&name=small)'
    }, makeTempDir(), { fetchImpl: fakeFetch('', false), attempts: 1 }),
    /Remote image localization failed/
  );
});

test('extracts unique remote image references from Markdown', () => {
  const refs = extractRemoteImageReferences(
    '![one](https://example.com/one.jpg)\n![one again](https://example.com/one.jpg)\n[![two](https://example.com/two.png)](https://example.com/page)'
  );

  assert.deepEqual(refs, [
    'https://example.com/one.jpg',
    'https://example.com/two.png'
  ]);
});

test('localizes remote images after copied local asset numbering', async () => {
  const root = makeTempDir();
  const outputDir = path.join(root, 'package');
  const localAsset = path.join(root, 'local.jpg');
  fs.writeFileSync(localAsset, 'local image');
  const copiedAssets = [{
    sourcePath: localAsset,
    filename: '001.jpg',
    relativePath: './assets/001.jpg'
  }];

  const result = await localizeRemoteImages(
    '![remote](https://example.com/remote.png)',
    outputDir,
    copiedAssets,
    { fetchImpl: fakeFetch('remote image') }
  );

  assert.match(result.markdown, /!\[remote\]\(\.\/assets\/002\.png\)/);
  assert.equal(fs.existsSync(path.join(outputDir, 'assets', '002.png')), true);
});

test('adapter output converts through convert.js', async () => {
  const root = makeTempDir();
  const packageDir = path.join(root, 'package');
  const outputDir = path.join(root, 'clippings');
  const assetsDir = path.join(root, 'vault-assets');
  fs.mkdirSync(outputDir, { recursive: true });

  const packageResult = await createArticlePackage({
    url: 'https://example.com/articles/adapter-integration',
    title: 'Adapter Integration Example',
    author: 'Nemo',
    published_at: '2026-05-01T09:00:00+08:00',
    captured_at: '2026-05-03T10:20:00+08:00',
    markdown: '# Adapter Integration Example\n\nBody.'
  }, packageDir);

  const converted = convertToObsidianFormat(packageResult.contentPath, outputDir, assetsDir);
  const note = fs.readFileSync(converted.outputPath, 'utf-8');

  assert.equal(converted.filename, '202605031020 Adapter Integration Example.md');
  assert.match(note, /created: 2026-05-01/);
  assert.match(note, /- "https:\/\/example.com\/articles\/adapter-integration"/);
});

test('fails clearly when required capture fields are missing', () => {
  assert.throws(
    () => normalizeCapture({ markdown: 'Body only.' }),
    /missing url/
  );

  assert.throws(
    () => normalizeCapture({ url: 'https://example.com/empty', markdown: '   ' }),
    /missing article markdown/
  );
});

test('rewrites copied asset references without touching unrelated links', () => {
  const markdown = '![local](C:/tmp/source.jpg)\n\n![remote](https://example.com/source.jpg)';
  const rewritten = rewriteAssetReferences(markdown, [{
    sourcePath: 'C:/tmp/source.jpg',
    filename: '001.jpg',
    relativePath: './assets/001.jpg'
  }]);

  assert.match(rewritten, /!\[local\]\(\.\/assets\/001\.jpg\)/);
  assert.match(rewritten, /!\[remote\]\(https:\/\/example.com\/source\.jpg\)/);
});
