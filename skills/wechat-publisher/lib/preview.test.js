import { describe, expect, it } from 'bun:test';
import { tmpdir } from 'os';
import { savePreviewHTML } from './preview.js';

describe('Preview HTML Saving', () => {
  it('saves HTML to temp file and returns path', async () => {
    const html = '<p>Test content</p>';
    const filePath = await savePreviewHTML(html, 'test-article');

    expect(filePath).toBeTruthy();
    expect(filePath).toContain('test-article');
    expect(filePath.endsWith('.html')).toBe(true);
  });

  it('uses system temp directory', async () => {
    const html = '<p>Test</p>';
    const filePath = await savePreviewHTML(html, 'test');

    expect(filePath.startsWith(tmpdir())).toBe(true);
  });
});
