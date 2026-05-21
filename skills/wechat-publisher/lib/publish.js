import { access } from 'fs/promises';
import { constants } from 'fs';
import { dirname, join } from 'path';
import { resolveLocalImagePath } from './path.js';

export async function resolveThumbnailSource({ filePath, localImages = [], remoteImages = [], config = {} }) {
  const baseDir = dirname(filePath);
  const coverSearchDirs = [baseDir];

  if (localImages.length > 0) {
    coverSearchDirs.unshift(dirname(resolveLocalImagePath(baseDir, localImages[0].path, config)));
  }

  for (const searchDir of coverSearchDirs) {
    const coverCandidates = [
      join(searchDir, 'cover.png'),
      join(searchDir, 'cover.jpg'),
      join(searchDir, 'cover.jpeg'),
      join(searchDir, 'cover.webp')
    ];

    for (const candidate of coverCandidates) {
      try {
        await access(candidate, constants.F_OK);
        return candidate;
      } catch {
        // Try next candidate.
      }
    }
  }

  if (localImages.length > 0) {
    return resolveLocalImagePath(baseDir, localImages[0].path, config);
  }

  if (remoteImages.length > 0) {
    return remoteImages[0].url;
  }

  return null;
}
