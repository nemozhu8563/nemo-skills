#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

/**
 * Convert article-clip output to Obsidian format
 * Usage: node convert.js <source-md-path> <output-dir> <assets-dir>
 */

function extractRealTitle(frontmatter, body) {
  // Extract real title using multiple strategies

  const rawTitle = frontmatter.title || 'Untitled';

  // Strategy 1: Try to extract from body first line
  if (body) {
    const lines = body.split('\n').filter(line =>
      line.trim() &&
      !line.startsWith('![[') &&
      !line.startsWith('![')
    );

    if (lines.length > 0) {
      let firstLine = lines[0].trim();

      // Remove common Twitter artifacts patterns
      firstLine = firstLine
        .replace(/^#+\s*/g, '')             // Remove markdown heading markers
        .replace(/\d+,\d+万/g, '')           // Remove "413731,20932万"
        .replace(/\d+\.\d+万/g, '')          // Remove "21592313.4万"
        .replace(/\d{6,}/g, '')              // Remove long numbers
        .replace(/这是一篇.*/g, '')          // Remove "这是一篇..." and everything after
        .replace(/（.*?）/g, '')             // Remove parentheses content
        .replace(/\(.*?\)/g, '')             // Remove parentheses content
        .replace(/\s+/g, ' ')                // Normalize spaces
        .trim();

      // If we got a reasonable title (10-100 chars), use it
      if (firstLine.length >= 10 && firstLine.length <= 100) {
        return firstLine;
      }
    }
  }

  // Strategy 2: Clean the frontmatter title
  let cleanedTitle = rawTitle
    .replace(/^#+\s*/g, '')
    .replace(/\d+,\d+万/g, '')
    .replace(/\d+\.\d+万/g, '')
    .replace(/\d{6,}/g, '')
    .replace(/这是一篇.*/g, '')
    .replace(/（.*?）/g, '')
    .replace(/\(.*?\)/g, '')
    .replace(/\s+/g, ' ')
    .trim();

  // If cleaned title is reasonable, use it
  if (cleanedTitle.length >= 10) {
    return cleanedTitle;
  }

  // Fallback: return raw title
  return rawTitle;
}

function sanitizeFilename(str) {
  // OneDrive filename restrictions:
  // - Cannot start/end with space or period
  // - Cannot start with two periods
  // - Cannot contain: / : * ? " < > |
  // - Keep short for path length limits

  return str
    .replace(/[<>:"/\\|?*]/g, '')  // Remove invalid filename chars
    .replace(/\d+,\d+万/g, '')      // Remove "413731,20932万" patterns (view counts)
    .replace(/\d+\.\d+万/g, '')     // Remove "21592313.4万" patterns
    .replace(/\d{6,}/g, '')         // Remove long number sequences (6+ digits)
    .replace(/\s+/g, ' ')           // Normalize whitespace
    .replace(/^\.+/g, '')           // Remove leading periods
    .replace(/\.+$/g, '')           // Remove trailing periods
    .replace(/^\s+|\s+$/g, '')      // Remove leading/trailing spaces
    .trim()
    .substring(0, 40);              // Limit to 40 chars for OneDrive
}

function sanitizeSourceTitle(str) {
  return str
    .replace(/\d+,\d+万/g, '')
    .replace(/\d+\.\d+万/g, '')
    .replace(/\d{6,}/g, '')
    .replace(/\s+/g, ' ')
    .replace(/^\.+/g, '')
    .replace(/\.+$/g, '')
    .trim();
}

function escapeYamlString(value) {
  return String(value ?? '')
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\r?\n/g, ' ')
    .trim();
}

function parseRequiredDate(dateStr, fieldName) {
  if (!dateStr) {
    throw new Error(`Missing required date field: ${fieldName}`);
  }

  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) {
    throw new Error(`Invalid required date field ${fieldName}: ${dateStr}`);
  }

  return date;
}

function formatTimestamp(dateStr) {
  const date = parseRequiredDate(dateStr, 'fetched_at');
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hour = String(date.getHours()).padStart(2, '0');
  const minute = String(date.getMinutes()).padStart(2, '0');
  return `${year}${month}${day}${hour}${minute}`;
}

function formatDate(dateStr) {
  const date = parseRequiredDate(dateStr, 'published_at');
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function extractFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) return { frontmatter: {}, body: content };

  const frontmatterText = match[1];
  const body = match[2];
  const frontmatter = {};

  frontmatterText.split('\n').forEach(line => {
    const colonIndex = line.indexOf(':');
    if (colonIndex > 0) {
      const key = line.substring(0, colonIndex).trim();
      let value = line.substring(colonIndex + 1).trim();
      if (value.startsWith('"') && value.endsWith('"')) {
        value = value.slice(1, -1);
      }
      frontmatter[key] = value;
    }
  });

  return { frontmatter, body };
}

function stripZhihuPlaceholderImageNotice(body, frontmatter) {
  // article-clip currently collects Zhihu lazy-load SVG placeholders from
  // <img src="data:image/svg+xml..."> as assets. Those placeholders are not
  // article images, and after every placeholder download fails the generated
  // Markdown contains only a generic "图片下载提示" section with no usable image
  // links. Remove that noisy notice while preserving real image references and
  // non-Zhihu asset failures.
  if (frontmatter.platform !== 'zhihu') {
    return body;
  }

  const hasImageReference = /!\[[^\]]*\]\([^)]+\)/.test(body) || /!\[\[[^\]]+\]\]/.test(body);
  if (hasImageReference) {
    return body;
  }

  const noticePattern = /\n*---\n\n## 图片下载提示\n\n部分图片使用在线链接：\n\n((?:• \d{3}\.(?:jpg|jpeg|png|webp|gif) \(下载失败\)\n?)+)\s*$/;
  const match = body.match(noticePattern);
  if (!match) {
    return body;
  }

  return body.slice(0, match.index).trimEnd();
}

function convertToObsidianFormat(sourcePath, outputDir, assetsDir) {
  // Read source file
  const content = fs.readFileSync(sourcePath, 'utf-8');
  const { frontmatter, body } = extractFrontmatter(content);

  // Extract real title from body content
  const realTitle = extractRealTitle(frontmatter, body);
  const cleanTitle = sanitizeFilename(realTitle);
  const sourceTitle = sanitizeSourceTitle(realTitle);
  const author = frontmatter.author || 'unknown';
  const sourceUrl = frontmatter.source_url || frontmatter.canonical_url || '';
  const fetchedAt = frontmatter.fetched_at; // Use download time for filename
  const publishedAt = frontmatter.published_at || frontmatter.fetched_at; // Use for created date
  const timestamp = formatTimestamp(fetchedAt);
  const createdDate = formatDate(publishedAt);

  // Generate filename
  const filename = `${timestamp} ${cleanTitle}.md`;
  const assetsDirName = `${timestamp} ${cleanTitle}`;

  // Create new frontmatter
  const newFrontmatter = `---
type: source
status: 待读
tags: [待处理]
created: ${createdDate}
source: "${escapeYamlString(sourceTitle)}"
refs:
  - "${escapeYamlString(sourceUrl)}"
ddc: "000"
author: "${escapeYamlString(author)}"
---`;

  // Update image references
  const cleanedBody = stripZhihuPlaceholderImageNotice(body, frontmatter);

  let newBody = cleanedBody
    .replace(/^#\s*$/gm, '') // Remove empty markdown headings emitted by some clippers
    .replace(/!\[[^\]]*\]\(\.\/assets\/([^)]+)\)/g, (match, imgFile) => {
      return `![[assets/${assetsDirName}/${imgFile}]]`;
    })
    .replace(/\[(!\[\[assets\/[^\]]+\]\])\]\([^)]+\)/g, '$1')
    .replace(/\n{3,}/g, '\n\n')
    .trim();

  // Combine
  const newContent = `${newFrontmatter}\n\n${newBody}`;

  // Write output file
  const outputPath = path.join(outputDir, filename);
  if (fs.existsSync(outputPath)) {
    throw new Error(`Output file already exists: ${outputPath}`);
  }
  fs.mkdirSync(outputDir, { recursive: true });
  fs.writeFileSync(outputPath, newContent, 'utf-8');

  // Move assets
  const sourceAssetsDir = path.join(path.dirname(sourcePath), 'assets');
  const targetAssetsDir = path.join(assetsDir, assetsDirName);

  if (fs.existsSync(sourceAssetsDir)) {
    fs.mkdirSync(targetAssetsDir, { recursive: true });
    const files = fs.readdirSync(sourceAssetsDir);
    files.forEach(file => {
      fs.copyFileSync(
        path.join(sourceAssetsDir, file),
        path.join(targetAssetsDir, file)
      );
    });
  }

  return {
    filename,
    outputPath,
    assetsDir: targetAssetsDir,
    imageCount: fs.existsSync(sourceAssetsDir) ? fs.readdirSync(sourceAssetsDir).length : 0
  };
}

// Main
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length < 3) {
    console.error('Usage: node convert.js <source-md-path> <output-dir> <assets-dir>');
    process.exit(1);
  }

  const [sourcePath, outputDir, assetsDir] = args;

  try {
    const result = convertToObsidianFormat(sourcePath, outputDir, assetsDir);
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

module.exports = { convertToObsidianFormat, stripZhihuPlaceholderImageNotice };
