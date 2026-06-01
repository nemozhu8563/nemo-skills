import { mkdir, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { parseMarkdown } from './md-to-html.js';

interface PackageOptions {
  markdownPath: string;
  outputDir?: string;
  title?: string;
  coverImage?: string;
}

interface ContentImage {
  placeholder: string;
  localPath: string;
  originalPath: string;
  alt: string;
  blockIndex: number;
}

interface PackageManifest {
  title: string;
  markdownPath: string;
  outputDir: string;
  coverImage: string | null;
  manifestPath: string;
  htmlPath: string;
  textPath: string;
  checklistPath: string;
  contentImages: ContentImage[];
  placeholders: string[];
  totalBlocks: number;
  generatedAt: string;
  safety: {
    finalPublish: string;
    imagePlacement: string;
  };
}

function usage(): never {
  console.log(`Prepare an X Article publishing package from Markdown.

Usage:
  npx -y bun x-article-package.ts <markdown_file> [options]

Options:
  --output-dir <dir>  Output package directory
  --title <title>     Override title
  --cover <path>      Override cover image
  --help              Show help
`);
  process.exit(0);
}

function parseArgs(): PackageOptions {
  const args = process.argv.slice(2);
  if (args.length === 0 || args.includes('--help') || args.includes('-h')) usage();

  let markdownPath = '';
  let outputDir: string | undefined;
  let title: string | undefined;
  let coverImage: string | undefined;

  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i]!;
    if (arg === '--output-dir' && args[i + 1]) {
      outputDir = args[++i];
    } else if (arg === '--title' && args[i + 1]) {
      title = args[++i];
    } else if (arg === '--cover' && args[i + 1]) {
      coverImage = args[++i];
    } else if (!arg.startsWith('-') && !markdownPath) {
      markdownPath = arg;
    } else {
      throw new Error(`Unknown or duplicate argument: ${arg}`);
    }
  }

  if (!markdownPath) throw new Error('Markdown file is required');
  return { markdownPath, outputDir, title, coverImage };
}

function defaultOutputDir(markdownPath: string): string {
  const safeName = path.basename(markdownPath, path.extname(markdownPath));
  return path.join(os.tmpdir(), 'baoyu-post-to-x', safeName);
}

function htmlToTextWithPlaceholders(html: string): string {
  return html
    .replace(/<\/h2>\n?/g, '\n\n')
    .replace(/<h2>/g, '')
    .replace(/<\/p>\n?/g, '\n\n')
    .replace(/<p>/g, '')
    .replace(/<li>/g, '- ')
    .replace(/<\/li>/g, '\n')
    .replace(/<\/?ol>|<\/?ul>/g, '\n')
    .replace(/<br\s*\/?>/g, '\n')
    .replace(/<\/?[^>]+>/g, '')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, '&')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function renderChecklist(manifest: PackageManifest): string {
  const images = manifest.contentImages
    .map((image, index) => `${index + 1}. Replace \`${image.placeholder}\` with \`${image.localPath}\`.`)
    .join('\n');

  return `# X Article Publishing Checklist

Title: ${manifest.title}

## Files

- Manifest: ${manifest.manifestPath}
- HTML: ${manifest.htmlPath}
- Text: ${manifest.textPath}
- Cover: ${manifest.coverImage ?? '(none)'}

## Steps

1. Open X Articles in Chrome.
2. Create a new article.
3. Set the cover image to \`${manifest.coverImage ?? '(none)'}\`.
4. Paste \`${manifest.htmlPath}\` into the editor.
5. Replace inline image placeholders in order.

${images || '(No inline images.)'}

## Verify Before Publishing

- No \`[[IMAGE_PLACEHOLDER_#]]\` placeholders remain.
- Every screenshot appears at its intended paragraph location.
- Preview renders title, cover, headings, body, and screenshots correctly.

Do not publish until the preview is visually verified.
`;
}

function normalizeRuntimePath(filePath: string): string {
  const resolved = path.resolve(filePath);
  return process.platform === 'win32' ? resolved.toLowerCase() : resolved;
}

function isDirectCliExecution(): boolean {
  return normalizeRuntimePath(process.argv[1] ?? '') === normalizeRuntimePath(fileURLToPath(import.meta.url));
}

export async function prepareArticlePackage(options: PackageOptions): Promise<PackageManifest> {
  const markdownPath = path.resolve(options.markdownPath);
  const outputDir = path.resolve(options.outputDir ?? defaultOutputDir(markdownPath));

  await mkdir(outputDir, { recursive: true });

  const parsed = await parseMarkdown(markdownPath, {
    title: options.title,
    coverImage: options.coverImage,
    tempDir: path.join(os.tmpdir(), 'baoyu-post-to-x-images'),
  });

  const htmlPath = path.join(outputDir, 'article.html');
  const textPath = path.join(outputDir, 'article.txt');
  const manifestPath = path.join(outputDir, 'manifest.json');
  const checklistPath = path.join(outputDir, 'operator-checklist.md');

  const contentImages = parsed.contentImages.map((image) => ({
    placeholder: image.placeholder,
    localPath: image.localPath,
    originalPath: image.originalPath,
    alt: image.alt,
    blockIndex: image.blockIndex,
  }));

  const manifest: PackageManifest = {
    title: parsed.title,
    markdownPath,
    outputDir,
    coverImage: parsed.coverImage,
    manifestPath,
    htmlPath,
    textPath,
    checklistPath,
    contentImages,
    placeholders: contentImages.map((image) => image.placeholder),
    totalBlocks: parsed.totalBlocks,
    generatedAt: new Date().toISOString(),
    safety: {
      finalPublish: 'Manual only. The account owner clicks the final X Publish button after preview.',
      imagePlacement: 'Do not publish while any placeholder remains or before visual preview verification.',
    },
  };

  await writeFile(htmlPath, parsed.html, 'utf8');
  await writeFile(textPath, htmlToTextWithPlaceholders(parsed.html), 'utf8');
  await writeFile(manifestPath, JSON.stringify(manifest, null, 2) + '\n', 'utf8');
  await writeFile(checklistPath, renderChecklist(manifest), 'utf8');

  return manifest;
}

async function main(): Promise<void> {
  const manifest = await prepareArticlePackage(parseArgs());
  console.log(JSON.stringify(manifest, null, 2));
}

if (isDirectCliExecution()) {
  await main().catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  });
}
