import { describe, expect, it } from 'bun:test';
import { uploadImages, replaceImageLinks } from './image.js';

describe('Image Handler', () => {
  it('keeps remote images as-is', async () => {
    const images = {
      remote: [
        { alt: 'remote', url: 'https://example.com/image.png' }
      ],
      local: []
    };

    const result = await uploadImages(images, '/base/path');

    expect(result).toHaveLength(1);
    expect(result[0].url).toBe('https://example.com/image.png');
  });

  it('replaces image links in content', () => {
    const content = `![alt1](url1.png)\n\n![alt2](url2.png)`;
    const images = [
      { alt: 'alt1', url: 'https://cdn.example.com/img1.png' },
      { alt: 'alt2', url: 'https://cdn.example.com/img2.png' }
    ];

    const result = replaceImageLinks(content, images);

    expect(result).toContain('https://cdn.example.com/img1.png');
    expect(result).toContain('https://cdn.example.com/img2.png');
    expect(result).not.toContain('url1.png');
  });

  it('uploads local images with provided uploader', async () => {
    const images = {
      remote: [],
      local: [{ alt: 'local', path: './images/local.png' }]
    };

    const result = await uploadImages(
      images,
      '/base/path',
      {},
      async (config, imagePath) => `https://wechat.example/${imagePath.split(/[\\/]/).pop()}`
    );

    expect(result).toHaveLength(1);
    expect(result[0].url).toBe('https://wechat.example/local.png');
  });
});
