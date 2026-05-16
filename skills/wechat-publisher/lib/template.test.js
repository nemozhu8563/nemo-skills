import { describe, expect, it } from 'bun:test';
import { generateHTML } from './template.js';

describe('HTML Generator', () => {
  it('converts markdown to HTML', async () => {
    const markdown = '# Hello\n\nThis is **bold** text.';
    const html = await generateHTML(markdown, 'template-tech');

    expect(html).toContain('<h1');
    expect(html).toContain('Hello');
    expect(html).toContain('<strong');
    expect(html).toContain('bold');
  });

  it('applies inline styles', async () => {
    const markdown = '# Test';
    const html = await generateHTML(markdown, 'template-tech');

    expect(html).toContain('style=');
    expect(html).toContain('color:');
  });

  it('handles code blocks', async () => {
    const markdown = '```javascript\nconst x = 1;\n```';
    const html = await generateHTML(markdown, 'template-tech');

    expect(html).toContain('<pre');
    expect(html).toContain('const x = 1');
  });

  it('uses default template for invalid template name', async () => {
    const markdown = '# Test';
    const html = await generateHTML(markdown, 'non-existent-template');

    expect(html).toContain('<h1');
    expect(html).toContain('Test');
  });
});

describe('Template Generator - Image Preservation', () => {
  it('preserves image URLs in generated HTML', async () => {
    const markdown = '![test](https://example.com/image.jpg)';
    const html = await generateHTML(markdown, 'template-tech');

    expect(html).toContain('https://example.com/image.jpg');
    expect(html).toContain('<img');
  });

  it('preserves multiple image URLs', async () => {
    const markdown = `
![img1](https://oss.example.com/img1.png)
![img2](https://oss.example.com/img2.png)
    `;
    const html = await generateHTML(markdown, 'template-tech');

    expect(html).toContain('https://oss.example.com/img1.png');
    expect(html).toContain('https://oss.example.com/img2.png');
  });

  it('preserves img src attribute exactly', async () => {
    const markdown = '![alt](https://cdn.example.com/test.jpg)';
    const html = await generateHTML(markdown, 'template-tech');
    const srcMatch = html.match(/<img[^>]+src="([^"]+)"/);

    expect(srcMatch).toBeTruthy();
    expect(srcMatch[1]).toBe('https://cdn.example.com/test.jpg');
  });
});

describe('Template Generator - Inline Styles on Elements', () => {
  it('applies inline styles to h1 element', async () => {
    const html = await generateHTML('# Hello', 'template-tech');

    expect(html).toContain('<h1');
    expect(html).toMatch(/<h1[^>]*style=/);
  });

  it('applies inline styles to h2 element', async () => {
    const html = await generateHTML('## World', 'template-tech');

    expect(html).toContain('<h2');
    expect(html).toMatch(/<h2[^>]*style=/);
  });

  it('applies inline styles to p element', async () => {
    const html = await generateHTML('This is a paragraph', 'template-tech');

    expect(html).toContain('<p');
    expect(html).toMatch(/<p[^>]*style=/);
  });

  it('applies inline styles to strong element', async () => {
    const html = await generateHTML('This is **bold** text', 'template-tech');

    expect(html).toContain('<strong');
    expect(html).toMatch(/<strong[^>]*style=/);
  });
});
