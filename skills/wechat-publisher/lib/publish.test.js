import { afterEach, describe, expect, it } from 'bun:test';
import { mkdtemp, writeFile, rm, mkdir } from 'fs/promises';
import { join } from 'path';
import { tmpdir } from 'os';
import { resolveThumbnailSource } from './publish.js';

const tempDirs = [];

async function makeTempDir() {
  const dir = await mkdtemp(join(tmpdir(), 'wechat-publisher-'));
  tempDirs.push(dir);
  return dir;
}

afterEach(async () => {
  while (tempDirs.length > 0) {
    await rm(tempDirs.pop(), { recursive: true, force: true });
  }
});

describe('Publish Helpers', () => {
  it('prefers cover.png as thumbnail', async () => {
    const dir = await makeTempDir();
    const filePath = join(dir, 'article.md');
    const coverPath = join(dir, 'cover.png');

    await writeFile(filePath, '# Article', 'utf-8');
    await writeFile(coverPath, 'fake-image', 'utf-8');

    const thumbSource = await resolveThumbnailSource({
      filePath,
      localImages: [{ path: './inline.png' }],
      remoteImages: [{ url: 'https://example.com/remote.png' }]
    });

    expect(thumbSource).toBe(coverPath);
  });

  it('prefers cover.png next to embedded images', async () => {
    const dir = await makeTempDir();
    const filePath = join(dir, 'article.md');
    const assetsDir = join(dir, 'assets', 'article');
    const coverPath = join(assetsDir, 'cover.png');

    await writeFile(filePath, '# Article', 'utf-8');
    await mkdir(assetsDir, { recursive: true });
    await writeFile(coverPath, 'fake-image', 'utf-8');

    const thumbSource = await resolveThumbnailSource({
      filePath,
      localImages: [{ path: './assets/article/file-1.png' }],
      remoteImages: []
    });

    expect(thumbSource).toBe(coverPath);
  });
});
