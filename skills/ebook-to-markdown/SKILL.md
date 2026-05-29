---
name: ebook-to-markdown
description: Convert learning ebooks and reading files such as AZW3, MOBI, EPUB, HTML, TXT, and text-layer PDFs into Markdown packages, after rejecting scanned/image-only sources that need OCR. Use when the user asks to convert an ebook, Kindle book, EPUB, AZW3, MOBI, PDF, HTML, or downloaded book into Markdown for study, annotation, Obsidian, or LLM-assisted reading.
---

# Ebook To Markdown

Convert ebook files into Markdown packages that are easy to study, quote, annotate, and import into Obsidian.

## Source Of Truth

This skill is managed from the sibling `nemo-skills` repository. Edit the source skill there, then publish into the vault. Do not hand-edit the generated vault copy.

## Output Contract

Create a package with:

- one primary Markdown file, named from the book title or source filename
- an adjacent asset folder named `<title>.assets/` when images exist
- YAML frontmatter with at least `title`, `source`, and `converted_at`
- local image references only; no broken asset links
- chapter order preserved from the ebook spine, manifest, table of contents, or filename order

Do not overwrite an existing useful Markdown output without checking. Prefer a new output directory or a timestamped package when there is any doubt.

## Scanned/Image-Only Boundary

Always identify whether the source has a usable text layer before treating conversion as successful. This is not just a PDF issue:

- scanned PDFs often have no extractable text
- EPUB/AZW3/MOBI can be image-only page scans
- HTML exports can contain page images with little or no OCR text

If the source is image-dominant and has too little extractable text, stop and report that OCR is required. Do not create a fake Markdown file made of image links or page noise and call it converted.

## Format Strategy

Use this decision tree:

| Source format | Preferred path | Notes |
| --- | --- | --- |
| `.epub` | parse EPUB directly or use helper script | Best structured source; preserve spine order and images. |
| `.azw3`, `.mobi`, `.prc` | convert/unpack to EPUB first, then Markdown | Prefer Calibre `ebook-convert`; fallback to `mobiunpack` when Calibre is not installed. |
| `.html`, `.xhtml`, `.htm` | HTML to Markdown | Preserve external web links; localize only existing local images. |
| `.txt`, `.md` | normalize/copy into package | Add frontmatter and keep text intact. |
| `.pdf` | extract text only when it has a text layer | For scanned PDFs, state that OCR is required before Markdown conversion. |

## Workflow

### 1. Locate The Source

When the user says the file is in Downloads, check common ebook extensions:

```bash
find ~/Downloads -maxdepth 2 -type f \( \
  -iname '*.azw3' -o -iname '*.mobi' -o -iname '*.prc' -o \
  -iname '*.epub' -o -iname '*.pdf' -o -iname '*.html' -o \
  -iname '*.xhtml' -o -iname '*.txt' -o -iname '*.md' \
\) -print
```

If multiple candidates exist, choose the most recent obvious match only when the user's wording makes it clear. Otherwise ask which book to convert.

### 2. Check Tools

Check local tools before installing anything:

```bash
command -v ebook-convert || true
command -v mobiunpack || true
command -v bun || true
command -v node || true
command -v pdftotext || true
```

Tool preference:

1. Calibre `ebook-convert` for broad proprietary ebook conversion.
2. `mobiunpack` for AZW3/MOBI when Calibre is unavailable.
3. This skill's Bun/Node helper for EPUB/HTML/TXT/PDF text extraction, scanned-source detection, and Markdown packaging.
4. `pdftotext` for PDFs with a real text layer.

Do not install large tools without a concrete need. If a temporary tool path is needed, keep it in the current work directory, not in the user's home directory.

### 3. Convert

From the `nemo-skills` source repo, the helper lives at:

```bash
bun skills/ebook-to-markdown/scripts/ebook-to-markdown.mjs \
  /path/to/book.epub \
  --out /path/to/output-dir
```

If `bun` is not available, use Node:

```bash
node skills/ebook-to-markdown/scripts/ebook-to-markdown.mjs \
  /path/to/book.epub \
  --out /path/to/output-dir
```

For AZW3/MOBI, make sure either Calibre `ebook-convert` or `mobiunpack` is on `PATH`, then run the same helper:

```bash
bun skills/ebook-to-markdown/scripts/ebook-to-markdown.mjs \
  /path/to/book.azw3 \
  --out /path/to/output-dir
```

### 4. Verify

Before reporting success, verify:

```bash
ls -lh /path/to/output-dir
wc -l /path/to/output-dir/*.md
rg -n '\.xhtml|filepos|kindle:|calibre_pb' /path/to/output-dir/*.md || true
rg -n '!\[[^\]]*\]\(([^)]+)\)' /path/to/output-dir/*.md || true
```

Also check:

- the Markdown opens with readable text, not mojibake
- chapter headings are present and in order
- internal EPUB `.xhtml#...` links were removed or rewritten
- every local image reference points to an existing file
- output is not just page images, blank lines, page headers, or OCR garbage
- the helper did not report `appears to be scanned/image-only`

### 5. Report

Report:

- source file path
- output Markdown path
- asset folder path and image count
- conversion route used, for example `AZW3 -> EPUB -> Markdown`
- verification result and any known quality limitation

Keep the final report short. Do not paste the book content into chat.

## Helper Script Notes

The bundled helper is intentionally conservative:

- EPUB spine order is the authority for reading order.
- Internal ebook links like `part0002.xhtml#filepos...` are rendered as plain text in a single Markdown output.
- Remote HTTP links are preserved.
- Images are copied into the `.assets/` folder and referenced relatively.
- AZW3/MOBI support requires either Calibre `ebook-convert` or `mobiunpack`.
- The helper rejects image-only EPUB/AZW3/MOBI/HTML/PDF inputs when extractable text is too low.
- PDF support requires `pdftotext`; scanned PDFs need OCR first.

## Error Handling

- **DRM/encryption**: Stop and report that the file cannot be converted with normal local tools. Do not attempt DRM removal.
- **No Calibre for AZW3/MOBI**: Try `mobiunpack` if available; if neither exists, recommend installing Calibre.
- **EPUB parse failure**: Try Calibre `ebook-convert source.epub normalized.epub`, then rerun the helper.
- **Image-only EPUB/AZW3/MOBI/HTML**: Report that OCR is required. Do not produce a Markdown file with only page image embeds.
- **Missing images**: Do not call the conversion complete until broken local image references are fixed or clearly reported.
- **PDF has no text layer**: Report that OCR is needed. Do not claim a clean Markdown conversion.
- **Huge book**: Keep intermediate files in a dedicated output directory and report approximate size/line count.
