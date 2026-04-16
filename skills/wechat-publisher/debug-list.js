#!/usr/bin/env node

import { parseMarkdown } from './lib/markdown.js';
import { generateHTML } from './lib/template.js';
import { marked } from 'marked';

const testMarkdown = `接入GSC后，你能够：
- 检查哪些页面已被Google收录
- 发现网站的SEO问题
- 查看用户通过什么搜索词找到你
- 主动提交新页面加速收录`;

marked.setOptions({ breaks: true, gfm: true });

console.log('=== Step 1: marked.js output ===');
const markedOutput = marked.parse(testMarkdown);
console.log(markedOutput);

console.log('\n=== Step 2: After generateHTML ===');
const finalOutput = await generateHTML(testMarkdown, 'template-tech');
console.log(finalOutput);
