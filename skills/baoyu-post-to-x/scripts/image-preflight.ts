import { readFile } from 'node:fs/promises';
import path from 'node:path';

export const DEFAULT_MAX_INLINE_IMAGE_ASPECT_RATIO = 1.8;

export interface RasterDimensions {
  width: number;
  height: number;
  format: 'png' | 'jpeg' | 'gif' | 'webp';
}

export interface InlineImagePath {
  localPath: string;
}

export interface TallImageIssue extends RasterDimensions {
  localPath: string;
  aspectRatio: number;
}

function validDimensions(width: number, height: number): boolean {
  return Number.isInteger(width) && Number.isInteger(height) && width > 0 && height > 0;
}

function readPngDimensions(buffer: Buffer): RasterDimensions | null {
  const signature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  if (buffer.length < 24 || !buffer.subarray(0, 8).equals(signature)) return null;

  const width = buffer.readUInt32BE(16);
  const height = buffer.readUInt32BE(20);
  return validDimensions(width, height) ? { width, height, format: 'png' } : null;
}

function readGifDimensions(buffer: Buffer): RasterDimensions | null {
  if (buffer.length < 10 || !/^GIF8[79]a$/.test(buffer.toString('ascii', 0, 6))) return null;

  const width = buffer.readUInt16LE(6);
  const height = buffer.readUInt16LE(8);
  return validDimensions(width, height) ? { width, height, format: 'gif' } : null;
}

function readWebpDimensions(buffer: Buffer): RasterDimensions | null {
  if (
    buffer.length < 30
    || buffer.toString('ascii', 0, 4) !== 'RIFF'
    || buffer.toString('ascii', 8, 12) !== 'WEBP'
  ) return null;

  const chunk = buffer.toString('ascii', 12, 16);
  let width = 0;
  let height = 0;

  if (chunk === 'VP8X') {
    width = 1 + buffer.readUIntLE(24, 3);
    height = 1 + buffer.readUIntLE(27, 3);
  } else if (chunk === 'VP8 ' && buffer.length >= 30) {
    if (buffer[23] !== 0x9d || buffer[24] !== 0x01 || buffer[25] !== 0x2a) return null;
    width = buffer.readUInt16LE(26) & 0x3fff;
    height = buffer.readUInt16LE(28) & 0x3fff;
  } else if (chunk === 'VP8L' && buffer.length >= 25 && buffer[20] === 0x2f) {
    const bits = buffer.readUInt32LE(21);
    width = (bits & 0x3fff) + 1;
    height = ((bits >>> 14) & 0x3fff) + 1;
  }

  return validDimensions(width, height) ? { width, height, format: 'webp' } : null;
}

function isJpegStartOfFrame(marker: number): boolean {
  return [
    0xc0, 0xc1, 0xc2, 0xc3,
    0xc5, 0xc6, 0xc7,
    0xc9, 0xca, 0xcb,
    0xcd, 0xce, 0xcf,
  ].includes(marker);
}

function readJpegDimensions(buffer: Buffer): RasterDimensions | null {
  if (buffer.length < 4 || buffer[0] !== 0xff || buffer[1] !== 0xd8) return null;

  let offset = 2;
  while (offset + 3 < buffer.length) {
    if (buffer[offset] !== 0xff) {
      offset += 1;
      continue;
    }

    while (offset < buffer.length && buffer[offset] === 0xff) offset += 1;
    if (offset >= buffer.length) break;

    const marker = buffer[offset++]!;
    if (marker === 0xd8 || marker === 0x01 || (marker >= 0xd0 && marker <= 0xd7)) continue;
    if (marker === 0xd9 || marker === 0xda || offset + 1 >= buffer.length) break;

    const segmentLength = buffer.readUInt16BE(offset);
    if (segmentLength < 2 || offset + segmentLength > buffer.length) break;

    if (isJpegStartOfFrame(marker) && segmentLength >= 7) {
      const height = buffer.readUInt16BE(offset + 3);
      const width = buffer.readUInt16BE(offset + 5);
      return validDimensions(width, height) ? { width, height, format: 'jpeg' } : null;
    }

    offset += segmentLength;
  }

  return null;
}

export function detectRasterDimensions(buffer: Buffer): RasterDimensions | null {
  return readPngDimensions(buffer)
    ?? readJpegDimensions(buffer)
    ?? readGifDimensions(buffer)
    ?? readWebpDimensions(buffer);
}

export async function readRasterDimensions(filePath: string): Promise<RasterDimensions | null> {
  return detectRasterDimensions(await readFile(filePath));
}

export async function auditTallArticleImages(
  images: readonly InlineImagePath[],
  maxAspectRatio = DEFAULT_MAX_INLINE_IMAGE_ASPECT_RATIO,
): Promise<TallImageIssue[]> {
  const issues: TallImageIssue[] = [];

  for (const image of images) {
    const dimensions = await readRasterDimensions(image.localPath);
    if (!dimensions) continue;

    const aspectRatio = dimensions.height / dimensions.width;
    if (aspectRatio > maxAspectRatio) {
      issues.push({
        ...dimensions,
        localPath: image.localPath,
        aspectRatio,
      });
    }
  }

  return issues;
}

export function formatTallImageError(
  issues: readonly TallImageIssue[],
  maxAspectRatio = DEFAULT_MAX_INLINE_IMAGE_ASPECT_RATIO,
): string {
  const details = issues
    .map((issue) => `- ${path.basename(issue.localPath)}: ${issue.width}x${issue.height} (1:${issue.aspectRatio.toFixed(2)})`)
    .join('\n');

  return [
    `Found ${issues.length} inline image(s) taller than the mobile-safe 1:${maxAspectRatio} ratio:`,
    details,
    'Split each logical screenshot into its own image before composing the X Article.',
    'If an intentionally tall illustration should remain unchanged, rerun with --allow-tall-images.',
    'Chrome was not opened.',
  ].join('\n');
}
