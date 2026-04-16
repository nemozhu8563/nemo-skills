import { access } from 'fs/promises';
import { constants } from 'fs';
import { dirname, join, resolve } from 'path';

export async function resolveThumbnailSource({ filePath, localImages = [], remoteImages = [] }) {
  const baseDir = dirname(filePath);
  const coverSearchDirs = [baseDir];

  if (localImages.length > 0) {
    coverSearchDirs.unshift(dirname(resolve(baseDir, localImages[0].path)));
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
    return resolve(baseDir, localImages[0].path);
  }

  if (remoteImages.length > 0) {
    return remoteImages[0].url;
  }

  return null;
}
