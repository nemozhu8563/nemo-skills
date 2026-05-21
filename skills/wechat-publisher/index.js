#!/usr/bin/env node

import notifier from 'node-notifier';
import { dirname, basename, resolve } from 'path';
import { fileURLToPath } from 'url';
import { readConfig, getConfigPath } from './lib/config.js';
import { parseMarkdown } from './lib/markdown.js';
import { generateHTML } from './lib/template.js';
import { uploadImages, replaceImageLinks } from './lib/image.js';
import { uploadToWeChat, uploadThumbToWechat } from './lib/wechat.js';
import { listTemplates } from './templates/styles.js';
import { savePreviewHTML } from './lib/preview.js';
import { resolveThumbnailSource } from './lib/publish.js';

export async function wechatPublisher(params) {
  const { filePath, template, configPath } = params;

  console.log(`Processing ${filePath}...`);

  try {
    console.log('Checking configuration...');
    const resolvedConfigPath = getConfigPath({ configPath });
    const config = await readConfig({ configPath });

    if (!config.wechat.appId || !config.wechat.appSecret) {
      throw new Error(`WeChat AppID/AppSecret not configured. Please edit: ${resolvedConfigPath}`);
    }

    let selectedTemplate = template || config.defaults.template;

    if (!template) {
      console.log('\nAvailable templates:');
      const templates = listTemplates();
      templates.forEach(t => console.log(`  - ${t.id}: ${t.name}`));
      console.log(`\nUsing default template: ${selectedTemplate}`);
    }

    console.log('Parsing Markdown...');
    const parsed = await parseMarkdown(filePath);

    if (parsed.images.local.length > 0) {
      console.log(`Uploading ${parsed.images.local.length} local image(s)...`);
      const uploadedImages = await uploadImages(
        parsed.images,
        dirname(filePath),
        config
      );

      parsed.content = replaceImageLinks(
        parsed.content,
        [...parsed.images.remote, ...uploadedImages]
      );
    }

    console.log(`Generating HTML with template: ${selectedTemplate}...`);
    const html = await generateHTML(parsed.content, selectedTemplate);

    console.log('Saving preview HTML...');
    const previewPath = await savePreviewHTML(html, basename(filePath, '.md'), selectedTemplate);
    console.log(`  Preview saved to: ${previewPath}`);

    let thumbMediaId = null;
    const thumbSource = await resolveThumbnailSource({
      filePath,
      localImages: parsed.images.local,
      remoteImages: parsed.images.remote,
      config
    });

    if (thumbSource) {
      console.log(`Uploading thumbnail from preferred source: ${thumbSource}`);
      try {
        thumbMediaId = await uploadThumbToWechat(config, thumbSource);
      } catch (error) {
        console.warn(`  Warning: Failed to upload thumbnail: ${error.message}`);
        console.warn('  Continuing without thumbnail...');
      }
    }

    console.log('Uploading to WeChat draft box...');
    const title = parsed.frontmatter.title || basename(filePath, '.md');
    const result = await uploadToWeChat(config, html, filePath, thumbMediaId, title);

    console.log('\nSuccessfully uploaded to WeChat draft box!');
    console.log(`  Media ID: ${result.media_id}`);
    console.log('  Please check your WeChat Official Account backend to view the draft.');

    return result;

  } catch (error) {
    console.error('\nError:', error.message);

    notifier.notify({
      title: 'WeChat Publisher Error',
      message: error.message,
      sound: true,
      wait: true
    });

    throw error;
  }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === resolve(process.argv[1])) {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.error('Usage: bun run publish -- <markdown-file> [template]');
    process.exit(1);
  }

  wechatPublisher({
    filePath: args[0],
    template: args[1]
  }).catch(() => process.exit(1));
}
