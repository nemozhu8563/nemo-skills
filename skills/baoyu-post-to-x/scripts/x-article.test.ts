import { afterEach, describe, expect, test } from 'bun:test';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

import {
  auditTallArticleImages,
  detectRasterDimensions,
  formatTallImageError,
} from './image-preflight.js';
import {
  selectionCoversArticleBody,
  sortImagesForStableInsertion,
} from './x-article.js';

const tempDirs: string[] = [];

function pngHeader(width: number, height: number): Buffer {
  const buffer = Buffer.alloc(24);
  Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]).copy(buffer, 0);
  buffer.write('IHDR', 12, 'ascii');
  buffer.writeUInt32BE(width, 16);
  buffer.writeUInt32BE(height, 20);
  return buffer;
}

afterEach(async () => {
  await Promise.all(tempDirs.splice(0).map((dir) => rm(dir, { recursive: true, force: true })));
});

describe('X Article inline image order', () => {
  test('processes placeholders from the end of the article without mutating parser output', () => {
    const images = [
      { placeholder: '[[IMAGE_PLACEHOLDER_2]]', blockIndex: 10 },
      { placeholder: '[[IMAGE_PLACEHOLDER_3]]', blockIndex: 20 },
      { placeholder: '[[IMAGE_PLACEHOLDER_4]]', blockIndex: 20 },
    ];

    expect(sortImagesForStableInsertion(images).map((image) => image.placeholder)).toEqual([
      '[[IMAGE_PLACEHOLDER_4]]',
      '[[IMAGE_PLACEHOLDER_3]]',
      '[[IMAGE_PLACEHOLDER_2]]',
    ]);
    expect(images.map((image) => image.placeholder)).toEqual([
      '[[IMAGE_PLACEHOLDER_2]]',
      '[[IMAGE_PLACEHOLDER_3]]',
      '[[IMAGE_PLACEHOLDER_4]]',
    ]);
  });
});

describe('X Article edit-mode selection safety', () => {
  test('accepts complete structural coverage when Draft.js text lengths differ', () => {
    expect(selectionCoversArticleBody({
      editorLength: 3146,
      selectedLength: 3114,
      startsInside: true,
      endsInside: true,
      collapsed: false,
      blockCount: 99,
      selectedBlockCount: 99,
      imageCount: 11,
      selectedImageCount: 11,
      textBlockCount: 88,
      startsWithFirstTextBlock: true,
      endsWithLastTextBlock: true,
    })).toBe(true);
  });

  test('rejects a selection that misses any body image or final text boundary', () => {
    const complete = {
      editorLength: 3146,
      selectedLength: 3114,
      startsInside: true,
      endsInside: true,
      collapsed: false,
      blockCount: 99,
      selectedBlockCount: 99,
      imageCount: 11,
      selectedImageCount: 11,
      textBlockCount: 88,
      startsWithFirstTextBlock: true,
      endsWithLastTextBlock: true,
    };

    expect(selectionCoversArticleBody({ ...complete, selectedImageCount: 10 })).toBe(false);
    expect(selectionCoversArticleBody({ ...complete, endsWithLastTextBlock: false })).toBe(false);
  });
});

describe('X Article tall image preflight', () => {
  test('reads PNG dimensions without decoding the full image', () => {
    expect(detectRasterDimensions(pngHeader(1080, 1960))).toEqual({
      width: 1080,
      height: 1960,
      format: 'png',
    });
  });

  test('flags tall inline images while keeping mobile-friendly images', async () => {
    const dir = await mkdtemp(path.join(os.tmpdir(), 'baoyu-post-to-x-image-test-'));
    tempDirs.push(dir);
    const tallPath = path.join(dir, 'three-screens.png');
    const safePath = path.join(dir, 'one-screen.png');
    await writeFile(tallPath, pngHeader(1080, 2598));
    await writeFile(safePath, pngHeader(1080, 988));

    const issues = await auditTallArticleImages([
      { localPath: tallPath },
      { localPath: safePath },
    ]);

    expect(issues).toHaveLength(1);
    expect(issues[0]).toMatchObject({
      localPath: tallPath,
      width: 1080,
      height: 2598,
      format: 'png',
    });
    expect(formatTallImageError(issues)).toContain('--allow-tall-images');
    expect(formatTallImageError(issues)).toContain('Chrome was not opened.');
  });
});
