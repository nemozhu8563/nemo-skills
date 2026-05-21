// lib/image.js
import { uploadArticleImageToWeChat } from './wechat.js';
import { resolveLocalImagePath } from './path.js';

export async function uploadImages(images, basePath, config = {}, uploader = uploadArticleImageToWeChat) {
  const results = [];

  // Keep remote images as-is
  for (const img of images.remote) {
    results.push({ alt: img.alt, url: img.url });
  }

  // Upload local images directly to WeChat article image API.
  for (const img of images.local) {
    try {
      const fullPath = resolveLocalImagePath(basePath, img.path, config);
      const uploadedUrl = await uploader(config, fullPath);

      results.push({ alt: img.alt, url: uploadedUrl });
    } catch (error) {
      throw new Error(`Failed to upload ${img.path}: ${error.message}`);
    }
  }

  return results;
}

export function replaceImageLinks(content, images) {
  let result = content;
  let imageIndex = 0;

  return result.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (match, alt, url) => {
    if (images[imageIndex]) {
      const replacement = `![${alt}](${images[imageIndex].url})`;
      imageIndex++;
      return replacement;
    }
    return match;
  });
}

export { resolveLocalImagePath };
