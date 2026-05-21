import { existsSync } from 'fs';
import { dirname, isAbsolute, resolve } from 'path';

function findVaultRoot(startPath) {
  let current = resolve(startPath);

  while (current !== dirname(current)) {
    if (existsSync(resolve(current, '.obsidian'))) {
      return current;
    }
    current = dirname(current);
  }

  return null;
}

export function resolveLocalImagePath(basePath, imagePath, config = {}) {
  if (isAbsolute(imagePath)) {
    return imagePath;
  }

  const candidates = [resolve(basePath, imagePath)];
  const configuredVaultRoot = config.defaults?.vaultRoot || config.vaultRoot;
  const vaultRoot = configuredVaultRoot || findVaultRoot(basePath);

  if (vaultRoot) {
    candidates.push(resolve(vaultRoot, imagePath));
  }

  const existing = candidates.find(candidate => existsSync(candidate));
  return existing || candidates[0];
}
