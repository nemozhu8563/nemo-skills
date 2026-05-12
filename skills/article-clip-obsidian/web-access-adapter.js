#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { setTimeout: sleep } = require('timers/promises');

/**
 * Normalize a web-access capture into the article package contract consumed by
 * convert.js: content.md plus an optional sibling assets/ directory.
 *
 * Usage: node web-access-adapter.js <capture-json-path> <package-output-dir>
 */

function firstPresent(...values) {
  return values.find(value => value !== undefined && value !== null && String(value).trim() !== '');
}

function escapeYamlString(value) {
  return String(value ?? '')
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\r?\n/g, ' ')
    .trim();
}

function titleFromMarkdown(markdown) {
  const heading = String(markdown || '').match(/^#\s+(.+)$/m);
  if (heading && heading[1].trim()) {
    return heading[1].trim();
  }

  const firstTextLine = String(markdown || '')
    .split(/\r?\n/)
    .map(line => line.trim())
    .find(line =>
      line &&
      !line.startsWith('![') &&
      !line.startsWith('![[') &&
      !line.startsWith('---')
    );

  return firstTextLine;
}

function titleFromUrl(url) {
  try {
    const parsed = new URL(url);
    const segments = parsed.pathname.split('/').filter(Boolean);
    const lastSegment = segments[segments.length - 1] || parsed.hostname;
    return decodeURIComponent(lastSegment)
      .replace(/[-_]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim() || parsed.hostname;
  } catch {
    return 'Untitled';
  }
}

function platformFromUrl(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return 'web';
  }
}

function normalizeCapture(input) {
  if (!input || typeof input !== 'object') {
    throw new Error('Capture must be a JSON object');
  }

  const metadata = input.metadata || {};
  const markdown = firstPresent(input.markdown, input.body, input.content, input.document);
  const url = firstPresent(
    input.url,
    input.source_url,
    input.canonical_url,
    metadata.url,
    metadata.source_url,
    metadata.canonical_url
  );

  if (!url) {
    throw new Error('Capture is missing url');
  }

  try {
    new URL(url);
  } catch {
    throw new Error(`Capture url is invalid: ${url}`);
  }

  if (!markdown || !String(markdown).trim()) {
    throw new Error('Capture is missing article markdown');
  }

  const fetchedAt = firstPresent(
    input.fetched_at,
    input.captured_at,
    input.capturedAt,
    metadata.fetched_at,
    metadata.captured_at,
    metadata.capturedAt,
    new Date().toISOString()
  );
  const publishedAt = firstPresent(
    input.published_at,
    input.publishedAt,
    input.published,
    metadata.published_at,
    metadata.publishedAt,
    metadata.published,
    fetchedAt
  );
  const title = firstPresent(
    input.title,
    metadata.title,
    titleFromMarkdown(markdown),
    titleFromUrl(url)
  );

  return {
    title,
    source_url: url,
    canonical_url: firstPresent(input.canonical_url, metadata.canonical_url, url),
    fetched_at: fetchedAt,
    published_at: publishedAt,
    author: firstPresent(input.author, metadata.author, 'unknown'),
    platform: firstPresent(input.platform, metadata.platform, platformFromUrl(url)),
    markdown: String(markdown).trim(),
    assets: Array.isArray(input.assets) ? input.assets : []
  };
}

function normalizeAsset(asset) {
  if (typeof asset === 'string') {
    return { sourcePath: asset, filename: path.basename(asset) };
  }

  if (!asset || typeof asset !== 'object') {
    throw new Error('Asset entries must be file paths or objects');
  }

  const sourcePath = asset.path || asset.sourcePath || asset.file;
  const originalUrl = asset.url || asset.originalUrl || asset.sourceUrl;
  const rawFilename = asset.filename || asset.name || (sourcePath ? path.basename(sourcePath) : undefined);
  const filename = rawFilename ? path.basename(String(rawFilename)) : undefined;

  if (!sourcePath || !filename) {
    throw new Error('Asset object must include path and filename/name');
  }

  return { sourcePath, filename, originalUrl };
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function copyAssets(assets, outputDir) {
  if (!assets.length) {
    return [];
  }

  const assetsDir = path.join(outputDir, 'assets');
  fs.mkdirSync(assetsDir, { recursive: true });

  return assets.map(asset => {
    const normalized = normalizeAsset(asset);
    const targetPath = path.join(assetsDir, normalized.filename);
    fs.copyFileSync(normalized.sourcePath, targetPath);
    return {
      sourcePath: normalized.sourcePath,
      originalUrl: normalized.originalUrl,
      filename: normalized.filename,
      relativePath: `./assets/${normalized.filename}`
    };
  });
}

function rewriteAssetReferences(markdown, copiedAssets) {
  let rewritten = markdown;

  for (const asset of copiedAssets) {
    const normalizedSource = asset.sourcePath.replace(/\\/g, '/');
    const candidates = new Set([
      asset.sourcePath,
      normalizedSource,
      `file://${normalizedSource}`,
      path.basename(asset.sourcePath),
      asset.originalUrl
    ]);

    for (const candidate of candidates) {
      if (!candidate) {
        continue;
      }
      rewritten = rewritten.replace(
        new RegExp(`\\]\\(${escapeRegExp(candidate)}\\)`, 'g'),
        `](${asset.relativePath})`
      );
    }
  }

  return rewritten;
}

function extractRemoteImageReferences(markdown) {
  const matches = [];
  const seen = new Set();
  const imagePattern = /!\[[^\]]*\]\((https?:\/\/[^)\s]+)\)/g;

  for (const match of markdown.matchAll(imagePattern)) {
    const url = match[1];
    if (!seen.has(url)) {
      seen.add(url);
      matches.push(url);
    }
  }

  return matches;
}

function extensionFromUrl(url) {
  try {
    const parsed = new URL(url);
    const format = parsed.searchParams.get('format');
    if (format) {
      return format.toLowerCase() === 'jpeg' ? 'jpg' : format.toLowerCase();
    }

    const ext = path.extname(parsed.pathname).replace(/^\./, '').toLowerCase();
    if (ext) {
      return ext === 'jpeg' ? 'jpg' : ext;
    }
  } catch {}

  return 'jpg';
}

async function downloadRemoteImage(url, targetPath, options = {}) {
  const fetchImpl = options.fetchImpl || globalThis.fetch;
  if (typeof fetchImpl !== 'function') {
    throw new Error('Remote image download requires global fetch support');
  }

  const attempts = options.attempts || 3;
  let lastError;

  for (let attempt = 1; attempt <= attempts; attempt++) {
    try {
      const response = await fetchImpl(url, {
        headers: {
          'user-agent': 'Mozilla/5.0 article-clip-obsidian'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const bytes = Buffer.from(await response.arrayBuffer());
      if (bytes.length === 0) {
        throw new Error('empty response');
      }

      fs.writeFileSync(targetPath, bytes);
      return;
    } catch (error) {
      lastError = error;
      if (attempt < attempts) {
        await sleep(options.retryDelayMs || 300);
      }
    }
  }

  throw new Error(`Failed to download image ${url}: ${lastError.message}`);
}

async function localizeRemoteImages(markdown, outputDir, copiedAssets, options = {}) {
  const remoteUrls = extractRemoteImageReferences(markdown);
  if (remoteUrls.length === 0) {
    return { markdown, copiedAssets };
  }

  const assetsDir = path.join(outputDir, 'assets');
  fs.mkdirSync(assetsDir, { recursive: true });

  let rewritten = markdown;
  const localizedAssets = [...copiedAssets];
  let nextIndex = localizedAssets.length + 1;
  const failures = [];

  for (const url of remoteUrls) {
    const extension = extensionFromUrl(url);
    const filename = `${String(nextIndex).padStart(3, '0')}.${extension}`;
    const targetPath = path.join(assetsDir, filename);

    try {
      await downloadRemoteImage(url, targetPath, options);
      const asset = {
        sourcePath: targetPath,
        originalUrl: url,
        filename,
        relativePath: `./assets/${filename}`
      };
      localizedAssets.push(asset);
      rewritten = rewriteAssetReferences(rewritten, [asset]);
      nextIndex++;
    } catch (error) {
      failures.push(error.message);
    }
  }

  if (failures.length > 0) {
    throw new Error(`Remote image localization failed: ${failures.join('; ')}`);
  }

  return { markdown: rewritten, copiedAssets: localizedAssets };
}

function renderContentMarkdown(capture) {
  return `---
title: "${escapeYamlString(capture.title)}"
source_url: "${escapeYamlString(capture.source_url)}"
canonical_url: "${escapeYamlString(capture.canonical_url)}"
fetched_at: "${escapeYamlString(capture.fetched_at)}"
published_at: "${escapeYamlString(capture.published_at)}"
author: "${escapeYamlString(capture.author)}"
platform: "${escapeYamlString(capture.platform)}"
---
${capture.markdown}
`;
}

async function createArticlePackage(input, outputDir, options = {}) {
  const capture = normalizeCapture(input);
  fs.mkdirSync(outputDir, { recursive: true });

  const copiedAssets = copyAssets(capture.assets, outputDir);
  let markdown = rewriteAssetReferences(capture.markdown, copiedAssets);
  const localized = await localizeRemoteImages(markdown, outputDir, copiedAssets, options);
  markdown = localized.markdown;
  const contentPath = path.join(outputDir, 'content.md');

  fs.writeFileSync(contentPath, renderContentMarkdown({ ...capture, markdown }), 'utf-8');

  return {
    contentPath,
    outputDir,
    assetCount: localized.copiedAssets.length
  };
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

if (require.main === module) {
  const [capturePath, outputDir] = process.argv.slice(2);

  if (!capturePath || !outputDir) {
    console.error('Usage: node web-access-adapter.js <capture-json-path> <package-output-dir>');
    process.exit(1);
  }

  try {
    createArticlePackage(readJson(capturePath), outputDir).then(result => {
    console.log(JSON.stringify(result, null, 2));
    }).catch(error => {
      console.error('Error:', error.message);
      process.exit(1);
    });
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

module.exports = {
  createArticlePackage,
  downloadRemoteImage,
  extractRemoteImageReferences,
  localizeRemoteImages,
  normalizeCapture,
  renderContentMarkdown,
  rewriteAssetReferences
};
