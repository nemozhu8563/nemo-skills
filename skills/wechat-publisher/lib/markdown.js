// lib/markdown.js
import { readFile } from 'fs/promises';
import matter from 'gray-matter';

export async function parseMarkdown(filePath) {
  const content = await readFile(filePath, 'utf-8');
  const { data: frontmatter, content: markdownContent } = matter(content);

  // Process Obsidian Callouts: > [!type] title -> <blockquote class="callout-type">
  let processedContent = processCallouts(markdownContent);

  // Convert Obsidian image embeds to standard markdown images.
  processedContent = processedContent.replace(/!\[\[([^\]]+)\]\]/g, (match, path) => {
    return `![](${path.trim()})`;
  });

  // Process wikilinks: [[Page]] -> Page
  processedContent = processedContent.replace(
    /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g,
    (match, page, display) => display || page
  );

  // Remove standalone #tags (at line start, not part of heading or inline)
  // Remove lines that are only hashtags
  processedContent = processedContent.replace(/^\s*#[a-zA-Z][\w-]*(\s+#[a-zA-Z][\w-]*)*\s*$/gm, '');

  // Drop trailing reference-only section from the article body.
  processedContent = processedContent.replace(/\n## Links[\s\S]*$/m, '');

  // Extract images
  const images = extractImages(processedContent);

  return {
    content: processedContent,
    frontmatter,
    images
  };
}

function extractImages(content) {
  const remote = [];
  const local = [];

  // Match markdown images: ![alt](url)
  const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
  let match;

  while ((match = imageRegex.exec(content)) !== null) {
    const url = match[2];

    if (url.startsWith('http://') || url.startsWith('https://')) {
      remote.push({
        alt: match[1],
        url: url
      });
    } else {
      local.push({
        alt: match[1],
        path: url
      });
    }
  }

  return { remote, local };
}

// Obsidian Callout types mapping
const CALLOUT_TYPES = {
  'note': { icon: '📝', label: '注意', color: 'info' },
  'summary': { icon: '📋', label: '摘要', color: 'info' },
  'abstract': { icon: '📋', label: '摘要', color: 'info' },
  'tldr': { icon: '📋', label: '摘要', color: 'info' },
  'tip': { icon: '💡', label: '提示', color: 'success' },
  'hint': { icon: '💡', label: '提示', color: 'success' },
  'important': { icon: '❗', label: '重要', color: 'warning' },
  'success': { icon: '✅', label: '成功', color: 'success' },
  'check': { icon: '✅', label: '完成', color: 'success' },
  'done': { icon: '✅', label: '完成', color: 'success' },
  'question': { icon: '❓', label: '问题', color: 'info' },
  'help': { icon: '❓', label: '帮助', color: 'info' },
  'faq': { icon: '❓', label: 'FAQ', color: 'info' },
  'warning': { icon: '⚠️', label: '警告', color: 'warning' },
  'caution': { icon: '⚠️', label: '注意', color: 'warning' },
  'attention': { icon: '⚠️', label: '注意', color: 'warning' },
  'failure': { icon: '❌', label: '失败', color: 'danger' },
  'fail': { icon: '❌', label: '失败', color: 'danger' },
  'missing': { icon: '❌', label: '缺失', color: 'danger' },
  'danger': { icon: '⛔', label: '危险', color: 'danger' },
  'error': { icon: '⛔', label: '错误', color: 'danger' },
  'bug': { icon: '🐛', label: 'Bug', color: 'danger' },
  'example': { icon: '📖', label: '示例', color: 'info' },
  'quote': { icon: '💬', label: '引用', color: 'default' }
};

function processCallouts(content) {
  // Match Obsidian callout blocks: > [!type] optional title
  // Supports multi-line blockquotes that start with [!type]
  const lines = content.split('\n');
  const result = [];
  let inCallout = false;
  let currentCallout = null;
  let calloutLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const calloutMatch = line.match(/^>\s*\[!([a-z]+)\](.*?)$/);

    if (calloutMatch) {
      // Start of new callout
      if (inCallout) {
        // End previous callout
        result.push(buildCalloutHTML(currentCallout, calloutLines.join('\n')));
        calloutLines = [];
      }

      const type = calloutMatch[1].toLowerCase();
      const title = calloutMatch[2].trim();
      const typeInfo = CALLOUT_TYPES[type] || CALLOUT_TYPES['note'];

      currentCallout = {
        type: type,
        icon: typeInfo.icon,
        label: title || typeInfo.label,
        color: typeInfo.color
      };
      inCallout = true;
    } else if (inCallout) {
      // Check if this line is part of the callout (starts with >)
      if (line.match(/^>/)) {
        calloutLines.push(line.replace(/^>\s?/, ''));
      } else {
        // End of callout
        result.push(buildCalloutHTML(currentCallout, calloutLines.join('\n')));
        calloutLines = [];
        inCallout = false;
        currentCallout = null;
        result.push(line);
      }
    } else {
      result.push(line);
    }
  }

  // Don't forget the last callout
  if (inCallout && currentCallout) {
    result.push(buildCalloutHTML(currentCallout, calloutLines.join('\n')));
  }

  return result.join('\n');
}

function buildCalloutHTML(callout, content) {
  // Use a special callout marker that will be converted to HTML after markdown parsing
  // Format: :::callout-type [icon] label\ncontn\n:::
  const trimmedContent = content.trim();
  return `:::callout-${callout.color} ${callout.icon} ${callout.label}
${trimmedContent}
:::`;
}
