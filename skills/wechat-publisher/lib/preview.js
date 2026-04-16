// lib/preview.js
import { writeFile } from 'fs/promises';
import { join } from 'path';
import { tmpdir } from 'os';
import { getTemplate } from '../templates/styles.js';

export async function savePreviewHTML(html, filename, templateName = 'template-tech') {
  const timestamp = Date.now();
  const sanitizedName = filename.replace(/[^a-zA-Z0-9_-]/g, '_');
  const tempFileName = `${sanitizedName}_${timestamp}.html`;
  const tempPath = join(tmpdir(), tempFileName);

  // Get template for CSS
  const template = getTemplate(templateName);

  // Create a complete HTML document for preview with CSS
  const fullHTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${sanitizedName}</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      line-height: 1.8;
      color: #333;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
      font-size: 16px;
    }
    ${template.css}
  </style>
</head>
<body>
${html}
</body>
</html>`;

  await writeFile(tempPath, fullHTML, 'utf-8');
  return tempPath;
}
