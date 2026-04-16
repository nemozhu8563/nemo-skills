// templates/styles.js
// CSS属性限制为微信支持的：
// color, font-size, font-weight, line-height, text-align
// background/background-color, padding, margin, border, border-radius
export const TEMPLATES = {
  'template-minimal': {
    name: '简约专业',
    css: `h1{color:#2c3e50;font-size:28px;border-bottom:3px solid #3498db;padding-bottom:10px;margin:20px 0 15px 0;font-weight:600}h2{color:#2c3e50;font-size:24px;border-left:4px solid #3498db;padding-left:12px;margin:20px 0 15px 0;font-weight:600}h3{color:#34495e;font-size:20px;margin:20px 0 15px 0;font-weight:600}p{color:#34495e;font-size:16px;margin:12px 0;line-height:1.8}code{background:#f7f7f7;color:#e74c3c;padding:2px 6px;border-radius:3px;font-family:'Monaco','Menlo',monospace;font-size:14px}pre{background:#2c3e50;color:#ecf0f1;padding:15px;border-radius:6px;margin:15px 0}pre code{background:transparent;color:#ecf0f1;padding:0}strong{color:#2c3e50;font-weight:600}blockquote{border-left:4px solid #3498db;padding-left:15px;margin:15px 0;color:#7f8c8d;font-style:italic}table{width:100%;border-collapse:collapse;margin:15px 0}th{background:#3498db;color:white;padding:12px;text-align:left;font-weight:600}td{padding:12px;border:1px solid #e0e0e0;color:#34495e}tr:nth-child(even){background:#f8f9fa}hr{border:none;border-top:2px solid #e0e0e0;margin:25px 0}`
  },
  'template-tech': {
    name: '科技蓝',
    css: `h1{color:#0066cc;font-size:28px;background:#0066cc;color:white;padding:15px 20px;border-radius:6px;margin:20px 0 15px 0;font-weight:600}h2{color:#0066cc;font-size:24px;border-bottom:2px solid #0066cc;padding-bottom:8px;margin:20px 0 15px 0;font-weight:600}h3{color:#0088dd;font-size:20px;margin:20px 0 15px 0;font-weight:600}p{color:#333;font-size:16px;margin:12px 0;line-height:1.8}code{background:#e8f4f8;color:#0066cc;padding:2px 6px;border-radius:3px;font-family:'Monaco','Menlo',monospace;font-size:14px}pre{background:#1e1e1e;color:#d4d4d4;padding:15px;border-radius:6px;border-left:4px solid #0066cc;margin:15px 0}pre code{background:transparent;color:#d4d4d4;padding:0}strong{color:#0066cc;font-weight:600}blockquote{border-left:4px solid #0066cc;background:#f0f8ff;padding:15px;margin:15px 0;color:#555;border-radius:4px}table{width:100%;border-collapse:collapse;margin:15px 0;border:1px solid #0066cc}th{background:#0066cc;color:white;padding:12px;text-align:left;font-weight:600}td{padding:12px;border:1px solid #ddd;color:#333}tr:nth-child(even){background:#f0f8ff}hr{border:none;border-top:2px dashed #0066cc;margin:25px 0}`
  },
  'template-elegant': {
    name: '优雅黑',
    css: `h1{color:#1a1a1a;font-size:32px;border-bottom:1px solid #333;padding-bottom:15px;margin:20px 0 15px 0;font-weight:600}h2{color:#1a1a1a;font-size:24px;border-left:6px solid #333;padding-left:15px;margin:20px 0 15px 0;font-weight:600}h3{color:#333;font-size:20px;margin:20px 0 15px 0;font-weight:600}p{color:#3a3a3a;font-size:16px;margin:12px 0;line-height:2}code{background:#f0f0f0;color:#c7254e;padding:3px 8px;border-radius:4px;border:1px solid #e0e0e0;font-family:'Monaco','Menlo',monospace;font-size:14px}pre{background:#282c34;color:#abb2bf;padding:20px;border-radius:8px;margin:15px 0}pre code{background:transparent;color:#abb2bf;padding:0;border:none}strong{color:#1a1a1a;font-weight:700}blockquote{border-left:5px solid #333;padding-left:20px;margin:15px 0;color:#666;font-style:italic;font-size:15px}table{width:100%;border-collapse:collapse;margin:15px 0}th{background:#333;color:white;padding:15px;text-align:left;font-weight:600}td{padding:15px;border:1px solid #e8e8e8;color:#3a3a3a}tr:nth-child(even){background:#fafafa}hr{border:none;border-top:1px solid #d0d0d0;margin:30px 0}`
  },
  'template-fresh': {
    name: '清新绿',
    css: `h1{color:#2d8659;font-size:28px;background:#2d8659;color:white;padding:15px 20px;border-radius:8px;margin:20px 0 15px 0;font-weight:600}h2{color:#2d8659;font-size:24px;border-bottom:3px solid #3cb371;padding-bottom:8px;margin:20px 0 15px 0;font-weight:600}h3{color:#3cb371;font-size:20px;margin:20px 0 15px 0;font-weight:600}p{color:#444;font-size:16px;margin:12px 0;line-height:1.8}code{background:#e8f5e9;color:#2d8659;padding:2px 6px;border-radius:3px;font-family:'Monaco','Menlo',monospace;font-size:14px}pre{background:#263238;color:#aed581;padding:15px;border-radius:6px;border-left:4px solid #3cb371;margin:15px 0}pre code{background:transparent;color:#aed581;padding:0}strong{color:#2d8659;font-weight:600}blockquote{border-left:4px solid #3cb371;background:#f1f8f4;padding:15px;margin:15px 0;color:#555;border-radius:4px}table{width:100%;border-collapse:collapse;margin:15px 0}th{background:#3cb371;color:white;padding:12px;text-align:left;font-weight:600}td{padding:12px;border:1px solid #e0e0e0;color:#444}tr:nth-child(even){background:#f1f8f4}hr{border:none;border-top:2px solid #c8e6c9;margin:25px 0}`
  },
  'template-minimal-bw': {
    name: '极简黑白',
    css: `h1{color:#000;font-size:32px;border-bottom:3px solid #000;padding-bottom:12px;margin:20px 0 15px 0;font-weight:700}h2{color:#000;font-size:26px;border-bottom:2px solid #333;padding-bottom:10px;margin:20px 0 15px 0;font-weight:700}h3{color:#333;font-size:22px;margin:20px 0 15px 0;font-weight:700}p{color:#000;font-size:16px;margin:12px 0;line-height:2}code{background:#f5f5f5;color:#000;padding:3px 8px;border-radius:3px;border:1px solid #e0e0e0;font-family:'Monaco','Menlo',monospace;font-size:14px}pre{background:#f5f5f5;color:#000;padding:20px;border-radius:4px;border:1px solid #d0d0d0;margin:15px 0}pre code{background:transparent;color:#000;padding:0;border:none}strong{color:#000;font-weight:700}blockquote{border-left:5px solid #000;padding-left:20px;margin:15px 0;color:#333;font-style:italic}table{width:100%;border-collapse:collapse;margin:15px 0;border:2px solid #000}th{background:#000;color:white;padding:15px;text-align:left;font-weight:700}td{padding:15px;border:1px solid #d0d0d0;color:#000}tr:nth-child(even){background:#fafafa}hr{border:none;border-top:2px solid #000;margin:30px 0}`
  },
  'template-warm-orange': {
    name: '暖橙活力',
    css: `h1{color:#ff6b35;font-size:28px;background:#ff6b35;color:white;padding:15px 20px;border-radius:8px;margin:20px 0 15px 0;font-weight:600}h2{color:#ff6b35;font-size:24px;border-bottom:3px solid #ff6b35;padding-bottom:8px;margin:20px 0 15px 0;font-weight:600}h3{color:#f77f00;font-size:20px;margin:20px 0 15px 0;font-weight:600}p{color:#333;font-size:16px;margin:12px 0;line-height:1.8}code{background:#fff4ed;color:#ff6b35;padding:2px 6px;border-radius:3px;font-family:'Monaco','Menlo',monospace;font-size:14px}pre{background:#2d2d2d;color:#ffb088;padding:15px;border-radius:6px;border-left:4px solid #ff6b35;margin:15px 0}pre code{background:transparent;color:#ffb088;padding:0}strong{color:#ff6b35;font-weight:600}blockquote{border-left:4px solid #ff6b35;background:#fff4ed;padding:15px;margin:15px 0;color:#555;border-radius:4px}table{width:100%;border-collapse:collapse;margin:15px 0}th{background:#ff6b35;color:white;padding:12px;text-align:left;font-weight:600}td{padding:12px;border:1px solid #e0e0e0;color:#333}tr:nth-child(even){background:#fff9f5}hr{border:none;border-top:2px solid #ff6b35;margin:25px 0}`
  },
  'template-dark': {
    name: '深色护眼',
    css: `h1{color:#88c0d0;font-size:28px;background:#5e81ac;color:#eceff4;padding:15px 20px;border-radius:8px;margin:20px 0 15px 0;font-weight:600}h2{color:#81a1c1;font-size:24px;border-bottom:3px solid #5e81ac;padding-bottom:8px;margin:20px 0 15px 0;font-weight:600}h3{color:#88c0d0;font-size:20px;margin:20px 0 15px 0;font-weight:600}p{color:#d8dee9;font-size:16px;margin:12px 0;line-height:1.8}code{background:#3b4252;color:#8fbcbb;padding:2px 6px;border-radius:3px;font-family:'Monaco','Menlo',monospace;font-size:14px}pre{background:#3b4252;color:#d8dee9;padding:15px;border-radius:6px;border-left:4px solid #5e81ac;margin:15px 0}pre code{background:transparent;color:#d8dee9;padding:0}strong{color:#88c0d0;font-weight:600}blockquote{border-left:4px solid #5e81ac;background:#3b4252;padding:15px;margin:15px 0;color:#d8dee9;border-radius:4px}table{width:100%;border-collapse:collapse;margin:15px 0}th{background:#5e81ac;color:#eceff4;padding:12px;text-align:left;font-weight:600}td{padding:12px;border:1px solid #4c566a;color:#d8dee9}tr:nth-child(even){background:#3b4252}hr{border:none;border-top:2px solid #4c566a;margin:25px 0}`
  },
  'template-business': {
    name: '商务正式',
    css: `h1{color:#1a3a52;font-size:28px;background:#1a3a52;color:white;padding:15px 20px;border-radius:6px;margin:20px 0 15px 0;font-weight:600}h2{color:#1a3a52;font-size:24px;border-left:5px solid #1a3a52;padding-left:15px;margin:20px 0 15px 0;font-weight:600}h3{color:#2c5f7c;font-size:20px;margin:20px 0 15px 0;font-weight:600}p{color:#333;font-size:16px;margin:12px 0;line-height:1.9}code{background:#e8f1f5;color:#1a3a52;padding:2px 6px;border-radius:3px;font-family:'Monaco','Menlo',monospace;font-size:14px}pre{background:#1e1e1e;color:#a9b7c6;padding:15px;border-radius:6px;border-left:4px solid #2c5f7c;margin:15px 0}pre code{background:transparent;color:#a9b7c6;padding:0}strong{color:#1a3a52;font-weight:600}blockquote{border-left:5px solid #1a3a52;background:#e8f1f5;padding:15px 20px;margin:15px 0;color:#555;border-radius:4px}table{width:100%;border-collapse:collapse;margin:15px 0}th{background:#1a3a52;color:white;padding:15px;text-align:left;font-weight:600}td{padding:15px;border:1px solid #d0d9e0;color:#333}tr:nth-child(even){background:#f5f8fa}hr{border:none;border-top:2px solid #d0d9e0;margin:30px 0}`
  }
};

export function getTemplate(name) {
  return TEMPLATES[name] || TEMPLATES['template-tech'];
}

export function listTemplates() {
  return Object.entries(TEMPLATES).map(([key, value]) => ({
    id: key,
    name: value.name
  }));
}
