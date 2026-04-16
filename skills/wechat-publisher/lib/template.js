// lib/template.js
import { marked } from 'marked';
import { getTemplate } from '../templates/styles.js';
import juice from 'juice';

export async function generateHTML(markdown, templateName) {
  const template = getTemplate(templateName);

  // First, process callout markers to proper HTML blockquote format
  const processedMarkdown = processCalloutMarkers(markdown);

  marked.setOptions({
    breaks: true,
    gfm: true
  });

  const bodyHTML = marked.parse(processedMarkdown);

  // Create complete HTML document with CSS in head
  const fullHTML = `
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>${template.css}</style>
</head>
<body>${bodyHTML}</body>
</html>`;

  // Use Juice to inline CSS
  let inlinedHTML = juice(fullHTML, {
    removeStyleTags: true,
    preserveImportant: true,
    preserveMediaQueries: false,
    applyWidthAttributes: false,
    applyHeightAttributes: false,
    applyAttributesTableElements: false
  });

  // Remove class attributes from code blocks (微信会剥离class)
  inlinedHTML = inlinedHTML.replace(/class="language-\w+"/g, '');

  // Fix list items: remove empty <p> tags that cause extra spacing in WeChat
  // When list items have blank lines between them, marked wraps them in <p> tags
  // WeChat editor treats these <p> tags as separators, inserting empty <li> elements
  inlinedHTML = inlinedHTML.replace(/<li>(<p[^>]*>)(<strong[^>]*>)([^<]*)(<\/strong>)(<\/p>)\s*<\/li>/g, '<li>$2$3$4</li>');
  inlinedHTML = inlinedHTML.replace(/<li>(<p[^>]*>)([^<]+)(<\/p>)\s*<\/li>/g, '<li>$2</li>');

  // Remove newlines inside list tags - WeChat ProseMirror editor converts them to empty <li> elements
  inlinedHTML = inlinedHTML.replace(/<(ul|ol)>([\s\S]*?)<\/\1>/g, (match, tag, content) => {
    const cleanContent = content.replace(/\n\s*/g, '');
    return `<${tag}>${cleanContent}</${tag}>`;
  });

  // Extract body content
  const bodyMatch = inlinedHTML.match(/<body>([\s\S]*)<\/body>/);
  return bodyMatch ? bodyMatch[1] : inlinedHTML;
}

// Process callout markers before markdown parsing
// Format: :::callout-type icon label\ncontent\n:::
function processCalloutMarkers(markdown) {
  const lines = markdown.split('\n');
  const result = [];
  let inCallout = false;
  let currentCallout = null;
  let calloutContent = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const calloutMatch = line.match(/^:::callout-([a-z]+)\s+(.+)$/);

    if (calloutMatch) {
      // Start of new callout
      if (inCallout) {
        result.push(buildCalloutBlock(currentCallout, calloutContent.join('\n')));
        calloutContent = [];
      }

      currentCallout = {
        type: calloutMatch[1],
        title: calloutMatch[2]
      };
      inCallout = true;
    } else if (line === ':::') {
      // End of callout
      if (inCallout && currentCallout) {
        result.push(buildCalloutBlock(currentCallout, calloutContent.join('\n')));
        calloutContent = [];
        inCallout = false;
        currentCallout = null;
      }
    } else if (inCallout) {
      calloutContent.push(line);
    } else {
      result.push(line);
    }
  }

  // Don't forget the last callout
  if (inCallout && currentCallout) {
    result.push(buildCalloutBlock(currentCallout, calloutContent.join('\n')));
  }

  return result.join('\n');
}

// Build callout block in proper HTML format with inline styles
function buildCalloutBlock(callout, content) {
  const trimmedContent = content.trim();
  const styles = getCalloutInlineStyles(callout.type);
  // Use inline styles instead of class
  return `<blockquote style="${styles}">
**${callout.title}**
${trimmedContent}
</blockquote>`;
}

// Get inline styles for callout types
function getCalloutInlineStyles(type) {
  const styles = {
    'info': 'border-left:4px solid #2196f3;background:#e3f2fd;padding:15px;margin:15px 0;border-radius:4px',
    'success': 'border-left:4px solid #4caf50;background:#e8f5e9;padding:15px;margin:15px 0;border-radius:4px',
    'warning': 'border-left:4px solid #ff9800;background:#fff3e0;padding:15px;margin:15px 0;border-radius:4px',
    'danger': 'border-left:4px solid #f44336;background:#ffebee;padding:15px;margin:15px 0;border-radius:4px',
    'default': 'border-left:4px solid #9e9e9e;background:#f5f5f5;padding:15px;margin:15px 0;border-radius:4px'
  };
  return styles[type] || styles['default'];
}
