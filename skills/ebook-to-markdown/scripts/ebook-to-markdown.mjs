#!/usr/bin/env bun
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const SUPPORTED_EXTENSIONS = new Set([
  ".epub",
  ".azw3",
  ".mobi",
  ".prc",
  ".html",
  ".xhtml",
  ".htm",
  ".txt",
  ".md",
  ".pdf",
]);
const IMAGE_EXTENSIONS = new Set([".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]);

function usage() {
  console.log(`Usage: bun ebook-to-markdown.mjs <source> --out <output-dir>

Converts EPUB, AZW3/MOBI via Calibre or mobiunpack, HTML, TXT/MD, and text-layer PDF into a Markdown study package.
Fails fast when the source appears to be scanned/image-only.`);
}

function parseArgs(argv) {
  const args = { out: "converted" };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else if (arg === "--out") {
      i += 1;
      if (!argv[i]) throw new Error("Missing value for --out");
      args.out = argv[i];
    } else if (!args.source) {
      args.source = arg;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  return args;
}

function commandExists(name) {
  return spawnSync("sh", ["-lc", `command -v ${shellQuote(name)} >/dev/null 2>&1`]).status === 0;
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, { stdio: "pipe", encoding: "utf8", ...options });
  if (result.status !== 0) {
    const detail = [result.stderr, result.stdout].filter(Boolean).join("\n").trim();
    throw new Error(`${command} failed${detail ? `: ${detail}` : ""}`);
  }
  return result;
}

function shellQuote(value) {
  return `'${String(value).replaceAll("'", "'\\''")}'`;
}

function tmpDir(prefix) {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function slug(value) {
  return (
    String(value || "ebook")
      .replace(/[\\/:*?"<>|()[\]]+/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 80) || "ebook"
  );
}

function decodeEntities(value) {
  return String(value)
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&#x([0-9a-f]+);/gi, (_, hex) => String.fromCodePoint(Number.parseInt(hex, 16)))
    .replace(/&#([0-9]+);/g, (_, dec) => String.fromCodePoint(Number.parseInt(dec, 10)));
}

function cleanMarkdown(value) {
  return decodeEntities(value)
    .replace(/\u00a0/g, " ")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function readableCharCount(value) {
  return [...String(value).matchAll(/[\p{L}\p{N}]/gu)].length;
}

function getAttr(tag, name) {
  const pattern = new RegExp(`${name}\\s*=\\s*["']([^"']*)["']`, "i");
  return tag.match(pattern)?.[1] || "";
}

function stripTags(value) {
  return decodeEntities(String(value).replace(/<[^>]+>/g, "")).replace(/\s+/g, " ").trim();
}

function extractTagText(xml, tagName) {
  const pattern = new RegExp(`<[^:>]*:?${tagName}\\b[^>]*>([\\s\\S]*?)<\\/[^:>]*:?${tagName}>`, "i");
  return stripTags(xml.match(pattern)?.[1] || "");
}

function extractRootfile(containerXml) {
  const match = containerXml.match(/<rootfile\b[^>]*full-path=["']([^"']+)["'][^>]*>/i);
  if (!match) throw new Error("EPUB container does not declare a rootfile.");
  return match[1];
}

function parseManifestItems(opfXml) {
  const items = new Map();
  for (const match of opfXml.matchAll(/<item\b[^>]*>/gi)) {
    const tag = match[0];
    const id = getAttr(tag, "id");
    if (!id) continue;
    items.set(id, {
      id,
      href: getAttr(tag, "href"),
      mediaType: getAttr(tag, "media-type"),
    });
  }
  return items;
}

function parseSpine(opfXml, manifest) {
  const spine = [];
  for (const match of opfXml.matchAll(/<itemref\b[^>]*>/gi)) {
    const idref = getAttr(match[0], "idref");
    if (idref && manifest.has(idref)) spine.push(manifest.get(idref));
  }
  if (spine.length > 0) return spine;
  return [...manifest.values()].filter((item) => /\.(xhtml|html|htm)$/i.test(item.href || ""));
}

function unzipArchive(source, destination) {
  if (!commandExists("unzip")) throw new Error("EPUB conversion requires unzip.");
  fs.mkdirSync(destination, { recursive: true });
  run("unzip", ["-q", source, "-d", destination]);
}

function copyImage(src, baseDir, assetsDir, assetRefDir, stats) {
  if (!src || /^(https?:|data:)/i.test(src)) return "";
  const sourcePath = path.resolve(baseDir, decodeURIComponent(src.split("#")[0]));
  if (!fs.existsSync(sourcePath) || !IMAGE_EXTENSIONS.has(path.extname(sourcePath).toLowerCase())) return "";
  fs.mkdirSync(assetsDir, { recursive: true });
  const targetPath = path.join(assetsDir, path.basename(sourcePath));
  if (!fs.existsSync(targetPath)) fs.copyFileSync(sourcePath, targetPath);
  stats.imageRefs.add(targetPath);
  return `![](${assetRefDir}/${path.basename(targetPath)})`;
}

function convertInline(htmlText, baseDir, assetsDir, assetRefDir, stats) {
  let out = htmlText;
  out = out.replace(/<br\b[^>]*\/?>/gi, "\n");
  out = out.replace(/<img\b[^>]*>/gi, (tag) => copyImage(getAttr(tag, "src"), baseDir, assetsDir, assetRefDir, stats));
  out = out.replace(/<a\b([^>]*)>([\s\S]*?)<\/a>/gi, (full, attrs, body) => {
    const label = stripTags(body);
    const href = getAttr(`<a ${attrs}>`, "href");
    if (/^https?:\/\//i.test(href) && label) return `[${label}](${href})`;
    return label;
  });
  return stripTags(out);
}

function paragraphMarkdown(tag, body, baseDir, assetsDir, assetRefDir, stats) {
  const text = convertInline(body, baseDir, assetsDir, assetRefDir, stats);
  if (!text) return "";
  const classes = new Set(getAttr(tag, "class").split(/\s+/).filter(Boolean));
  if (classes.has("calibre_6")) return `# ${text}\n\n`;
  if (/^第[0-9一二三四五六七八九十百]+章[ \u3000]/.test(text)) return `## ${text}\n\n`;
  if (classes.has("calibre_9")) return `### ${text}\n\n`;
  if (classes.has("calibre_8")) return `> ${text}\n\n`;
  return `${text}\n\n`;
}

function convertHtmlFile(filePath, assetsDir, assetRefDir, stats) {
  const baseDir = path.dirname(filePath);
  let htmlText = fs.readFileSync(filePath, "utf8");
  htmlText = htmlText.replace(/<!DOCTYPE[\s\S]*?>/gi, "");
  htmlText = htmlText.replace(/<script\b[\s\S]*?<\/script>/gi, "");
  htmlText = htmlText.replace(/<style\b[\s\S]*?<\/style>/gi, "");
  htmlText = htmlText.replace(/<head\b[\s\S]*?<\/head>/gi, "");
  const bodyMatch = htmlText.match(/<body\b[^>]*>([\s\S]*?)<\/body>/i);
  htmlText = bodyMatch ? bodyMatch[1] : htmlText;
  htmlText = htmlText.replace(/<div\b[^>]*class=["'][^"']*mbp_pagebreak[^"']*["'][^>]*><\/div>/gi, "");

  stats.htmlDocuments += 1;
  stats.sourceTextChars += readableCharCount(stripTags(htmlText));
  stats.localImageTags += [...htmlText.matchAll(/<img\b[^>]*src=["']([^"']+)["'][^>]*>/gi)].filter((match) => {
    const src = match[1] || "";
    return src && !/^(https?:|data:)/i.test(src);
  }).length;

  const blocks = [];
  htmlText = htmlText.replace(/<h([1-6])\b[^>]*>([\s\S]*?)<\/h\1>/gi, (_, level, body) => {
    blocks.push(`${"#".repeat(Number(level))} ${convertInline(body, baseDir, assetsDir, assetRefDir, stats)}\n\n`);
    return "\n";
  });
  htmlText = htmlText.replace(/<p\b([^>]*)>([\s\S]*?)<\/p>/gi, (full, attrs, body) => {
    blocks.push(paragraphMarkdown(`<p ${attrs}>`, body, baseDir, assetsDir, assetRefDir, stats));
    return "\n";
  });
  htmlText = htmlText.replace(/<li\b[^>]*>([\s\S]*?)<\/li>/gi, (_, body) => {
    blocks.push(`- ${convertInline(body, baseDir, assetsDir, assetRefDir, stats)}\n`);
    return "\n";
  });
  htmlText = htmlText.replace(/<img\b[^>]*>/gi, (tag) => {
    const image = copyImage(getAttr(tag, "src"), baseDir, assetsDir, assetRefDir, stats);
    if (image) blocks.push(`${image}\n\n`);
    return "\n";
  });
  const remainder = convertInline(htmlText, baseDir, assetsDir, assetRefDir, stats);
  if (readableCharCount(remainder) > 0) blocks.push(`${remainder}\n\n`);
  return cleanMarkdown(blocks.join(""));
}

function assessScanned(stats, label) {
  const textChars = stats.markdownTextChars || stats.sourceTextChars || 0;
  const images = stats.imageRefs?.size || stats.localImageTags || stats.manifestImageCount || 0;
  const docs = stats.htmlDocuments || 1;
  const imageDominant = images >= Math.max(3, docs * 0.6);
  const tooLittleText = textChars < 800 || textChars / Math.max(docs, 1) < 120;
  if (imageDominant && tooLittleText) {
    throw new Error(
      `${label} appears to be scanned/image-only: text_chars=${textChars}, images=${images}, documents=${docs}. OCR is required before Markdown conversion.`,
    );
  }
  if (textChars < 120) {
    throw new Error(`${label} has too little extractable text: text_chars=${textChars}. It may be scanned, encrypted, or unsupported.`);
  }
}

function convertEpub(epubPath, outDir, sourceForHeader = epubPath) {
  const tempRoot = tmpDir("ebook-md-");
  try {
    const extractDir = path.join(tempRoot, "epub");
    unzipArchive(epubPath, extractDir);
    const containerPath = path.join(extractDir, "META-INF", "container.xml");
    const opfPath = path.join(extractDir, extractRootfile(fs.readFileSync(containerPath, "utf8")));
    const opfXml = fs.readFileSync(opfPath, "utf8");
    const opfDir = path.dirname(opfPath);
    const title = extractTagText(opfXml, "title") || path.basename(epubPath, path.extname(epubPath));
    const author = extractTagText(opfXml, "creator");
    const publisher = extractTagText(opfXml, "publisher");
    const publicationDate = extractTagText(opfXml, "date");
    const outputName = slug(title);
    const assetsDir = path.join(outDir, `${outputName}.assets`);
    const stats = {
      htmlDocuments: 0,
      imageRefs: new Set(),
      localImageTags: 0,
      manifestImageCount: 0,
      sourceTextChars: 0,
      markdownTextChars: 0,
    };
    const manifest = parseManifestItems(opfXml);
    stats.manifestImageCount = [...manifest.values()].filter((item) => /^image\//i.test(item.mediaType)).length;
    const spine = parseSpine(opfXml, manifest);
    const chunks = [];
    for (const item of spine) {
      if (!item.href || !/\.(xhtml|html|htm)$/i.test(item.href)) continue;
      const htmlPath = path.resolve(opfDir, item.href);
      if (!htmlPath.startsWith(path.resolve(extractDir)) || !fs.existsSync(htmlPath)) continue;
      const chunk = convertHtmlFile(htmlPath, assetsDir, path.basename(assetsDir), stats);
      if (chunk) chunks.push(chunk);
    }
    const body = chunks.join("\n\n---\n\n");
    stats.markdownTextChars = readableCharCount(body);
    assessScanned(stats, path.basename(sourceForHeader));

    fs.mkdirSync(outDir, { recursive: true });
    const outputPath = path.join(outDir, `${outputName}.md`);
    const header = [
      "---",
      `title: ${title}`,
      `author: ${author}`,
      `publisher: ${publisher}`,
      `publication_date: ${publicationDate}`,
      `source: ${sourceForHeader}`,
      `converted_at: ${new Date().toISOString()}`,
      "---",
      "",
    ].join("\n");
    fs.writeFileSync(outputPath, `${header}${body}\n`, "utf8");
    return { outputPath, stats };
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

function findFirst(root, predicate) {
  const entries = fs.readdirSync(root, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(root, entry.name);
    if (entry.isDirectory()) {
      const found = findFirst(full, predicate);
      if (found) return found;
    } else if (predicate(full)) {
      return full;
    }
  }
  return "";
}

function kindleToEpub(sourcePath) {
  const tempRoot = tmpDir("ebook-kindle-");
  const epubPath = path.join(tempRoot, `${path.basename(sourcePath, path.extname(sourcePath))}.epub`);
  if (commandExists("ebook-convert")) {
    run("ebook-convert", [sourcePath, epubPath]);
    return { epubPath, cleanup: () => fs.rmSync(tempRoot, { recursive: true, force: true }) };
  }
  if (commandExists("mobiunpack")) {
    const unpackDir = path.join(tempRoot, "unpacked");
    fs.mkdirSync(unpackDir, { recursive: true });
    run("mobiunpack", [sourcePath, unpackDir]);
    const found = findFirst(unpackDir, (file) => path.extname(file).toLowerCase() === ".epub");
    if (!found) throw new Error("mobiunpack completed but no EPUB was found.");
    return { epubPath: found, cleanup: () => fs.rmSync(tempRoot, { recursive: true, force: true }) };
  }
  fs.rmSync(tempRoot, { recursive: true, force: true });
  throw new Error("AZW3/MOBI conversion requires Calibre ebook-convert or mobiunpack on PATH.");
}

function convertHtmlSource(sourcePath, outDir) {
  const title = path.basename(sourcePath, path.extname(sourcePath));
  const outputName = slug(title);
  const assetsDir = path.join(outDir, `${outputName}.assets`);
  const stats = { htmlDocuments: 0, imageRefs: new Set(), localImageTags: 0, manifestImageCount: 0, sourceTextChars: 0 };
  const body = convertHtmlFile(sourcePath, assetsDir, path.basename(assetsDir), stats);
  stats.markdownTextChars = readableCharCount(body);
  assessScanned(stats, path.basename(sourcePath));
  fs.mkdirSync(outDir, { recursive: true });
  const outputPath = path.join(outDir, `${outputName}.md`);
  fs.writeFileSync(
    outputPath,
    `---\ntitle: ${title}\nsource: ${sourcePath}\nconverted_at: ${new Date().toISOString()}\n---\n\n${body}\n`,
    "utf8",
  );
  return { outputPath, stats };
}

function convertTextSource(sourcePath, outDir) {
  const title = path.basename(sourcePath, path.extname(sourcePath));
  const text = fs.readFileSync(sourcePath, "utf8");
  const stats = { markdownTextChars: readableCharCount(text), imageRefs: new Set(), htmlDocuments: 1 };
  assessScanned(stats, path.basename(sourcePath));
  fs.mkdirSync(outDir, { recursive: true });
  const outputPath = path.join(outDir, `${slug(title)}.md`);
  fs.writeFileSync(
    outputPath,
    `---\ntitle: ${title}\nsource: ${sourcePath}\nconverted_at: ${new Date().toISOString()}\n---\n\n${text}`,
    "utf8",
  );
  return { outputPath, stats };
}

function convertPdfSource(sourcePath, outDir) {
  if (!commandExists("pdftotext")) {
    throw new Error("PDF conversion requires pdftotext. Scanned PDFs require OCR before Markdown conversion.");
  }
  const tempRoot = tmpDir("ebook-pdf-");
  try {
    const txtPath = path.join(tempRoot, `${path.basename(sourcePath, path.extname(sourcePath))}.txt`);
    run("pdftotext", ["-layout", sourcePath, txtPath]);
    const text = fs.readFileSync(txtPath, "utf8");
    const stats = { markdownTextChars: readableCharCount(text), imageRefs: new Set(), htmlDocuments: 1 };
    assessScanned(stats, path.basename(sourcePath));
    fs.mkdirSync(outDir, { recursive: true });
    const title = path.basename(sourcePath, path.extname(sourcePath));
    const outputPath = path.join(outDir, `${slug(title)}.md`);
    fs.writeFileSync(
      outputPath,
      `---\ntitle: ${title}\nsource: ${sourcePath}\nconverted_at: ${new Date().toISOString()}\n---\n\n${text}`,
      "utf8",
    );
    return { outputPath, stats };
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

function convert(source, outDir) {
  const sourcePath = path.resolve(source);
  if (!fs.existsSync(sourcePath)) throw new Error(`Source not found: ${sourcePath}`);
  const extension = path.extname(sourcePath).toLowerCase();
  if (!SUPPORTED_EXTENSIONS.has(extension)) throw new Error(`Unsupported extension: ${extension}`);
  if (extension === ".epub") return convertEpub(sourcePath, path.resolve(outDir));
  if ([".azw3", ".mobi", ".prc"].includes(extension)) {
    const converted = kindleToEpub(sourcePath);
    try {
      return convertEpub(converted.epubPath, path.resolve(outDir), sourcePath);
    } finally {
      converted.cleanup();
    }
  }
  if ([".html", ".xhtml", ".htm"].includes(extension)) return convertHtmlSource(sourcePath, path.resolve(outDir));
  if ([".txt", ".md"].includes(extension)) return convertTextSource(sourcePath, path.resolve(outDir));
  if (extension === ".pdf") return convertPdfSource(sourcePath, path.resolve(outDir));
  throw new Error(`Unsupported extension: ${extension}`);
}

try {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.source) {
    usage();
    process.exit(args.help ? 0 : 1);
  }
  const result = convert(args.source, args.out);
  console.log(result.outputPath);
  console.log(
    JSON.stringify({
      text_chars: result.stats.markdownTextChars || result.stats.sourceTextChars || 0,
      image_refs: result.stats.imageRefs?.size || 0,
      html_documents: result.stats.htmlDocuments || 0,
    }),
  );
} catch (error) {
  console.error(`error: ${error.message}`);
  process.exit(1);
}
