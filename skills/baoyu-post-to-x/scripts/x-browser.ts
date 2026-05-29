import { spawn } from 'node:child_process';
import fs from 'node:fs';
import { mkdir } from 'node:fs/promises';
import process from 'node:process';
import {
  CHROME_CANDIDATES_FULL,
  CdpConnection,
  copyImageToClipboard,
  findChromeExecutable,
  getDefaultProfileDir,
  getFreePort,
  insertTextIntoComposer,
  pasteFromClipboard,
  sleep,
  waitForChromeDebugPort,
} from './x-utils.js';

const X_COMPOSE_URL = 'https://x.com/compose/post';
const EDITOR_SELECTOR = '[data-testid="tweetTextarea_0"]';
const FILE_INPUT_SELECTOR = '[data-testid="fileInput"], input[type="file"][accept*="image"], input[type="file"]';
const ATTACHMENT_SELECTOR = [
  '[data-testid="attachments"] img',
  '[data-testid="attachments"] [role="img"]',
  '[data-testid="tweetPhoto"] img',
  '[data-testid="mediaPreview"] img',
].join(', ');
const UPLOAD_PROGRESS_SELECTOR = [
  '[role="progressbar"]',
  '.upload-progress',
  '[aria-label*="uploading" i]',
  '[aria-label*="上传" i]',
].join(', ');

interface XBrowserOptions {
  text?: string;
  images?: string[];
  submit?: boolean;
  timeoutMs?: number;
  profileDir?: string;
  chromePath?: string;
}

async function getAttachmentState(
  cdp: CdpConnection,
  sessionId: string,
): Promise<{ attachmentCount: number; uploadInProgress: boolean; tweetButtonEnabled: boolean }> {
  const result = await cdp.send<{ result: { value: { attachmentCount: number; uploadInProgress: boolean; tweetButtonEnabled: boolean } } }>('Runtime.evaluate', {
    expression: `(() => {
      const attachmentCount = document.querySelectorAll(${JSON.stringify(ATTACHMENT_SELECTOR)}).length;
      const uploadInProgress = document.querySelectorAll(${JSON.stringify(UPLOAD_PROGRESS_SELECTOR)}).length > 0;
      const tweetButton = document.querySelector('[data-testid="tweetButton"]');
      const tweetButtonEnabled = !!tweetButton && !tweetButton.disabled && tweetButton.getAttribute('aria-disabled') !== 'true';
      return { attachmentCount, uploadInProgress, tweetButtonEnabled };
    })()`,
    returnByValue: true,
  }, { sessionId });

  return result.result.value;
}

async function waitForAttachmentCount(
  cdp: CdpConnection,
  sessionId: string,
  beforeCount: number,
  timeoutMs = 15_000,
): Promise<boolean> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    await sleep(500);
    const state = await getAttachmentState(cdp, sessionId);
    if (state.attachmentCount > beforeCount) return true;
  }
  return false;
}

async function waitForUploadReady(
  cdp: CdpConnection,
  sessionId: string,
  expectedCount: number,
  timeoutMs = 30_000,
): Promise<boolean> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    await sleep(1000);
    const state = await getAttachmentState(cdp, sessionId);
    if (state.attachmentCount >= expectedCount && (!state.uploadInProgress || state.tweetButtonEnabled)) return true;
  }
  return false;
}

async function clickComposerSubmitButton(cdp: CdpConnection, sessionId: string): Promise<boolean> {
  const result = await cdp.send<{ result: { value: boolean } }>('Runtime.evaluate', {
    expression: `(() => {
      const candidates = Array.from(document.querySelectorAll('[data-testid="tweetButton"], [data-testid="tweetButtonInline"]'));
      const visible = candidates.filter((el) => {
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
      });
      const preferred = visible.find((el) => {
        const dialog = el.closest('[role="dialog"]');
        if (!dialog) return false;
        const textArea = dialog.querySelector('[data-testid="tweetTextarea_0"]');
        return !!textArea;
      }) ?? visible[visible.length - 1];
      if (!preferred) return false;
      preferred.click();
      return true;
    })()`,
    returnByValue: true,
  }, { sessionId });

  return result.result.value;
}

async function uploadImageViaFileInput(
  cdp: CdpConnection,
  sessionId: string,
  imagePath: string,
): Promise<boolean> {
  const { root } = await cdp.send<{ root: { nodeId: number } }>('DOM.getDocument', {}, { sessionId });
  const { nodeId } = await cdp.send<{ nodeId: number }>('DOM.querySelector', {
    nodeId: root.nodeId,
    selector: FILE_INPUT_SELECTOR,
  }, { sessionId });

  if (!nodeId || nodeId === 0) return false;

  await cdp.send('DOM.setFileInputFiles', {
    nodeId,
    files: [imagePath],
  }, { sessionId });

  return true;
}

async function pasteImageFromClipboard(
  cdp: CdpConnection,
  sessionId: string,
  imagePath: string,
): Promise<boolean> {
  if (!copyImageToClipboard(imagePath)) {
    console.warn(`[x-browser] Failed to copy image to clipboard: ${imagePath}`);
    return false;
  }

  await sleep(500);

  await cdp.send('Runtime.evaluate', {
    expression: `document.querySelector(${JSON.stringify(EDITOR_SELECTOR)})?.focus()`,
  }, { sessionId });
  await sleep(200);

  console.log('[x-browser] Pasting from clipboard...');
  const pasteSuccess = pasteFromClipboard('Google Chrome', 5, 500);

  if (pasteSuccess) return true;

  console.log('[x-browser] Paste script failed, trying CDP fallback...');
  const modifiers = process.platform === 'darwin' ? 4 : 2;
  await cdp.send('Input.dispatchKeyEvent', {
    type: 'keyDown',
    key: 'v',
    code: 'KeyV',
    modifiers,
    windowsVirtualKeyCode: 86,
  }, { sessionId });
  await cdp.send('Input.dispatchKeyEvent', {
    type: 'keyUp',
    key: 'v',
    code: 'KeyV',
    modifiers,
    windowsVirtualKeyCode: 86,
  }, { sessionId });
  return true;
}

export async function postToX(options: XBrowserOptions): Promise<void> {
  const { text, images = [], submit = false, timeoutMs = 120_000, profileDir = getDefaultProfileDir() } = options;

  const chromePath = options.chromePath ?? findChromeExecutable(CHROME_CANDIDATES_FULL);
  if (!chromePath) throw new Error('Chrome not found. Set X_BROWSER_CHROME_PATH env var.');

  await mkdir(profileDir, { recursive: true });

  const port = await getFreePort();
  console.log(`[x-browser] Launching Chrome (profile: ${profileDir})`);

  const chrome = spawn(chromePath, [
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${profileDir}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-blink-features=AutomationControlled',
    '--start-maximized',
    X_COMPOSE_URL,
  ], { stdio: 'ignore' });

  let cdp: CdpConnection | null = null;

  try {
    const wsUrl = await waitForChromeDebugPort(port, 30_000, { includeLastError: true });
    cdp = await CdpConnection.connect(wsUrl, 30_000, { defaultTimeoutMs: 15_000 });

    const targets = await cdp.send<{ targetInfos: Array<{ targetId: string; url: string; type: string }> }>('Target.getTargets');
    let pageTarget = targets.targetInfos.find((t) => t.type === 'page' && t.url.includes('x.com'));

    if (!pageTarget) {
      const { targetId } = await cdp.send<{ targetId: string }>('Target.createTarget', { url: X_COMPOSE_URL });
      pageTarget = { targetId, url: X_COMPOSE_URL, type: 'page' };
    }

    const { sessionId } = await cdp.send<{ sessionId: string }>('Target.attachToTarget', { targetId: pageTarget.targetId, flatten: true });

    await cdp.send('Page.enable', {}, { sessionId });
    await cdp.send('Runtime.enable', {}, { sessionId });
    await cdp.send('Input.setIgnoreInputEvents', { ignore: false }, { sessionId });

    console.log('[x-browser] Waiting for X editor...');
    await sleep(3000);

    const waitForEditor = async (): Promise<boolean> => {
      const start = Date.now();
      while (Date.now() - start < timeoutMs) {
        const result = await cdp!.send<{ result: { value: boolean } }>('Runtime.evaluate', {
          expression: `!!document.querySelector(${JSON.stringify(EDITOR_SELECTOR)})`,
          returnByValue: true,
        }, { sessionId });
        if (result.result.value) return true;
        await sleep(1000);
      }
      return false;
    };

    const editorFound = await waitForEditor();
    if (!editorFound) {
      console.log('[x-browser] Editor not found. Please log in to X in the browser window.');
      console.log('[x-browser] Waiting for login...');
      const loggedIn = await waitForEditor();
      if (!loggedIn) throw new Error('Timed out waiting for X editor. Please log in first.');
    }

    if (text) {
      console.log('[x-browser] Typing text...');
      await insertTextIntoComposer(cdp, sessionId, text);
    }

    for (const imagePath of images) {
      if (!fs.existsSync(imagePath)) {
        console.warn(`[x-browser] Image not found: ${imagePath}`);
        continue;
      }

      console.log(`[x-browser] Pasting image: ${imagePath}`);

      const beforeState = await getAttachmentState(cdp, sessionId);
      let attachmentAppeared = false;

      console.log('[x-browser] Uploading via file input...');
      const fileInputUsed = await uploadImageViaFileInput(cdp, sessionId, imagePath);
      if (fileInputUsed) {
        attachmentAppeared = await waitForAttachmentCount(cdp, sessionId, beforeState.attachmentCount);
      }

      if (!attachmentAppeared) {
        console.log('[x-browser] File input path did not confirm attachment, falling back to clipboard paste...');
        const pasteTriggered = await pasteImageFromClipboard(cdp, sessionId, imagePath);
        if (pasteTriggered) {
          attachmentAppeared = await waitForAttachmentCount(cdp, sessionId, beforeState.attachmentCount);
        }
      }

      if (!attachmentAppeared) {
        throw new Error(`Image did not appear in composer: ${imagePath}`);
      }

      const expectedCount = beforeState.attachmentCount + 1;
      console.log(`[x-browser] Attachment detected (${expectedCount} total), waiting for upload completion...`);
      const uploadReady = await waitForUploadReady(cdp, sessionId, expectedCount);
      if (!uploadReady) {
        throw new Error(`Image upload did not finish in time: ${imagePath}`);
      }
    }

    if (submit) {
      console.log('[x-browser] Submitting post...');
      const clicked = await clickComposerSubmitButton(cdp, sessionId);
      if (!clicked) {
        throw new Error('Could not find a visible composer submit button.');
      }
      await sleep(2000);
      console.log('[x-browser] Post submitted!');
    } else {
      console.log('[x-browser] Post composed (preview mode). Add --submit to post.');
      console.log('[x-browser] Browser will stay open for 30 seconds for preview...');
      await sleep(30_000);
    }
  } finally {
    if (cdp) {
      try { await cdp.send('Browser.close', {}, { timeoutMs: 5_000 }); } catch {}
      cdp.close();
    }

    setTimeout(() => {
      if (!chrome.killed) try { chrome.kill('SIGKILL'); } catch {}
    }, 2_000).unref?.();
    try { chrome.kill('SIGTERM'); } catch {}
  }
}

function printUsage(): never {
  console.log(`Post to X (Twitter) using real Chrome browser

Usage:
  npx -y bun x-browser.ts [options] [text]

Options:
  --image <path>   Add image (can be repeated, max 4)
  --submit         Actually post (default: preview only)
  --profile <dir>  Chrome profile directory
  --help           Show this help

Examples:
  npx -y bun x-browser.ts "Hello from CLI!"
  npx -y bun x-browser.ts "Check this out" --image ./screenshot.png
  npx -y bun x-browser.ts "Post it!" --image a.png --image b.png --submit
`);
  process.exit(0);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  if (args.includes('--help') || args.includes('-h')) printUsage();

  const images: string[] = [];
  let submit = false;
  let profileDir: string | undefined;
  const textParts: string[] = [];

  for (let i = 0; i < args.length; i++) {
    const arg = args[i]!;
    if (arg === '--image' && args[i + 1]) {
      images.push(args[++i]!);
    } else if (arg === '--submit') {
      submit = true;
    } else if (arg === '--profile' && args[i + 1]) {
      profileDir = args[++i];
    } else if (!arg.startsWith('-')) {
      textParts.push(arg);
    }
  }

  const text = textParts.join(' ').trim() || undefined;

  if (!text && images.length === 0) {
    console.error('Error: Provide text or at least one image.');
    process.exit(1);
  }

  await postToX({ text, images, submit, profileDir });
}

await main().catch((err) => {
  console.error(`Error: ${err instanceof Error ? err.message : String(err)}`);
  process.exit(1);
});
