import { spawn } from 'node:child_process';
import fs from 'node:fs';
import { mkdir, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';

import { parseMarkdown } from './md-to-html.js';
import {
  CHROME_CANDIDATES_BASIC,
  CdpConnection,
  copyHtmlToClipboard,
  copyImageToClipboard,
  findChromeExecutable,
  getDefaultProfileDir,
  getFreePort,
  getReusableChromeDebugSession,
  pasteFromClipboard,
  rememberChromeDebugPort,
  sleep,
  waitForChromeDebugPort,
} from './x-utils.js';

const X_ARTICLES_URL = 'https://x.com/compose/articles';

const I18N_SELECTORS = {
  createArticleButton: [
    '[data-testid="empty_state_button_text"]',
    '[aria-label="create"]',
  ],
  titleInput: [
    'textarea[placeholder="Add a title"]',
    'textarea[placeholder="添加标题"]',
    'textarea[placeholder="タイトルを追加"]',
    'textarea[placeholder="제목 추가"]',
    'textarea[name="Article Title"]',
  ],
  addPhotosButton: [
    '[aria-label="Add photos or video"]',
    '[aria-label="添加照片或视频"]',
    '[aria-label="写真や動画を追加"]',
    '[aria-label="사진 또는 동영상 추가"]',
  ],
  previewButton: [
    'a[href*="/preview"]',
    '[data-testid="previewButton"]',
    'button[aria-label*="preview" i]',
    'button[aria-label*="预览" i]',
    'button[aria-label*="プレビュー" i]',
    'button[aria-label*="미리보기" i]',
  ],
  publishButton: [
    '[data-testid="publishButton"]',
    'button[aria-label*="publish" i]',
    'button[aria-label*="发布" i]',
    'button[aria-label*="公開" i]',
    'button[aria-label*="게시" i]',
  ],
};

const EDITOR_CONTENT_SELECTOR = [
  '.DraftEditor-editorContainer [data-contents="true"]',
  '[data-testid="composer"]',
].join(', ');

const EDITOR_INPUT_SELECTOR = [
  '.DraftEditor-editorContainer [contenteditable="true"]',
  '[data-testid="composer"][contenteditable="true"]',
  '[role="textbox"][contenteditable="true"]',
].join(', ');

const APPLY_BUTTON_TEXT = ['Apply', '应用', '適用', '적용'];

interface ArticleOptions {
  markdownPath: string;
  coverImage?: string;
  title?: string;
  submit?: boolean;
  profileDir?: string;
  chromePath?: string;
}

export async function publishArticle(options: ArticleOptions): Promise<void> {
  const { markdownPath, submit = false, profileDir = getDefaultProfileDir() } = options;

  console.log('[x-article] Parsing markdown...');
  const parsed = await parseMarkdown(markdownPath, {
    title: options.title,
    coverImage: options.coverImage,
  });

  console.log(`[x-article] Title: ${parsed.title}`);
  console.log(`[x-article] Cover: ${parsed.coverImage ?? 'none'}`);
  console.log(`[x-article] Content images: ${parsed.contentImages.length}`);

  // Save HTML to temp file
  const htmlPath = path.join(os.tmpdir(), 'x-article-content.html');
  await writeFile(htmlPath, parsed.html, 'utf-8');
  console.log(`[x-article] HTML saved to: ${htmlPath}`);

  const chromePath = options.chromePath ?? findChromeExecutable(CHROME_CANDIDATES_BASIC);
  if (!chromePath) throw new Error('Chrome not found');

  await mkdir(profileDir, { recursive: true });
  const reusable = await getReusableChromeDebugSession(profileDir);
  let port = reusable?.port;
  let wsUrl = reusable?.wsUrl;
  let launchedChrome = false;
  let chrome: ReturnType<typeof spawn> | null = null;

  if (reusable) {
    console.log(`[x-article] Reusing Chrome debug session on port ${reusable.port} (profile: ${profileDir})`);
  } else {
    port = await getFreePort();
    console.log(`[x-article] Launching Chrome...`);
    chrome = spawn(chromePath, [
      `--remote-debugging-port=${port}`,
      `--user-data-dir=${profileDir}`,
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-blink-features=AutomationControlled',
      '--start-maximized',
      X_ARTICLES_URL,
    ], { stdio: 'ignore' });
    launchedChrome = true;
  }

  let cdp: CdpConnection | null = null;

  try {
    if (!wsUrl) {
      wsUrl = await waitForChromeDebugPort(port!, 30_000, { includeLastError: true });
      rememberChromeDebugPort(profileDir, port!);
    }
    cdp = await CdpConnection.connect(wsUrl, 30_000, { defaultTimeoutMs: 30_000 });

    // Get page target
    const targets = await cdp.send<{ targetInfos: Array<{ targetId: string; url: string; type: string }> }>('Target.getTargets');
    let pageTarget = launchedChrome
      ? targets.targetInfos.find((t) => t.type === 'page' && t.url.includes('x.com'))
      : undefined;

    if (!pageTarget) {
      const { targetId } = await cdp.send<{ targetId: string }>('Target.createTarget', { url: X_ARTICLES_URL });
      pageTarget = { targetId, url: X_ARTICLES_URL, type: 'page' };
    }

    const { sessionId } = await cdp.send<{ sessionId: string }>('Target.attachToTarget', { targetId: pageTarget.targetId, flatten: true });

    await cdp.send('Page.enable', {}, { sessionId });
    await cdp.send('Runtime.enable', {}, { sessionId });
    await cdp.send('DOM.enable', {}, { sessionId });

    console.log('[x-article] Waiting for articles page...');
    await sleep(3000);

    const waitForElement = async (selector: string, timeoutMs = 60_000): Promise<boolean> => {
      const start = Date.now();
      while (Date.now() - start < timeoutMs) {
        const result = await cdp!.send<{ result: { value: boolean } }>('Runtime.evaluate', {
          expression: `!!document.querySelector('${selector}')`,
          returnByValue: true,
        }, { sessionId });
        if (result.result.value) return true;
        await sleep(500);
      }
      return false;
    };

    const waitForAnySelector = async (selectors: string[], timeoutMs = 60_000): Promise<boolean> => {
      return waitForElement(selectors.join(', '), timeoutMs);
    };

    const clickBySelectorsOrText = async (selectors: string[], texts: string[] = []): Promise<boolean> => {
      const result = await cdp!.send<{ result: { value: boolean } }>('Runtime.evaluate', {
        expression: `(() => {
          const selectors = ${JSON.stringify(selectors)};
          for (const selector of selectors) {
            const el = document.querySelector(selector);
            if (el) { el.click(); return true; }
          }

          const texts = ${JSON.stringify(texts)};
          const candidates = Array.from(document.querySelectorAll('button, a, div[role="button"]'));
          const el = candidates.find((candidate) => texts.includes((candidate.innerText || '').trim()));
          if (el) { el.click(); return true; }
          return false;
        })()`,
        returnByValue: true,
      }, { sessionId });
      return result.result.value;
    };

    const removePlaceholderText = async (placeholder: string): Promise<boolean> => {
      const result = await cdp!.send<{ result: { value: boolean } }>('Runtime.evaluate', {
        expression: `(() => {
          const editor = document.querySelector(${JSON.stringify(EDITOR_CONTENT_SELECTOR)});
          const input = document.querySelector(${JSON.stringify(EDITOR_INPUT_SELECTOR)});
          if (!editor || !input) return false;

          const placeholder = ${JSON.stringify(placeholder)};
          const walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT, null, false);
          let node;

          while ((node = walker.nextNode())) {
            const text = node.textContent || '';
            const idx = text.indexOf(placeholder);
            if (idx === -1) continue;

            const range = document.createRange();
            range.setStart(node, idx);
            range.setEnd(node, idx + placeholder.length);

            const sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);

            input.focus();
            const deleted = document.execCommand('delete');
            input.dispatchEvent(new InputEvent('input', {
              bubbles: true,
              inputType: 'deleteContentBackward',
              data: null,
            }));

            return deleted && !(editor.innerText || '').includes(placeholder);
          }

          return false;
        })()`,
        returnByValue: true,
      }, { sessionId });

      return result.result.value;
    };

    console.log('[x-article] Looking for article create button...');
    const createButtonFound = await waitForAnySelector(I18N_SELECTORS.createArticleButton, 10_000);

    if (createButtonFound) {
      console.log('[x-article] Clicking article create button...');
      await clickBySelectorsOrText(I18N_SELECTORS.createArticleButton, ['Write', '撰写', '作成', '작성']);
      await sleep(5000);
    }

    // Wait for editor (title textarea)
    const titleSelectors = I18N_SELECTORS.titleInput.join(', ');
    console.log('[x-article] Waiting for editor...');
    const editorFound = await waitForElement(titleSelectors, 90_000);
    if (!editorFound) {
      console.log('[x-article] Editor not found. Please ensure you have X Premium and are logged in.');
      await sleep(60_000);
      throw new Error('Editor not found');
    }

    // Upload cover image
    if (parsed.coverImage) {
      console.log('[x-article] Uploading cover image...');

      // Click "Add photos or video" button
      const addPhotosSelectors = JSON.stringify(I18N_SELECTORS.addPhotosButton);
      await cdp.send('Runtime.evaluate', {
        expression: `(() => {
          const selectors = ${addPhotosSelectors};
          for (const sel of selectors) {
            const el = document.querySelector(sel);
            if (el) { el.click(); return true; }
          }
          return false;
        })()`,
      }, { sessionId });
      await sleep(500);

      // Use file input directly
      const { root } = await cdp.send<{ root: { nodeId: number } }>('DOM.getDocument', {}, { sessionId });
      const { nodeId } = await cdp.send<{ nodeId: number }>('DOM.querySelector', {
        nodeId: root.nodeId,
        selector: '[data-testid="fileInput"], input[type="file"][accept*="image"]',
      }, { sessionId });

      if (nodeId) {
        await cdp.send('DOM.setFileInputFiles', {
          nodeId,
          files: [parsed.coverImage],
        }, { sessionId });
        console.log('[x-article] Cover image file set');

        // Wait for Apply button to appear and click it
        console.log('[x-article] Waiting for Apply button...');
        const applyFound = await waitForElement('[data-testid="applyButton"], button, div[role="button"]', 15_000);
        if (applyFound) {
          const clicked = await clickBySelectorsOrText(['[data-testid="applyButton"]'], APPLY_BUTTON_TEXT);
          if (!clicked) {
            console.log('[x-article] Apply button text not found, continuing...');
          } else {
            console.log('[x-article] Cover image applied');
            await sleep(1000);
          }
        } else {
          console.log('[x-article] Apply button not found, continuing...');
        }
      }
    }

    // Fill title using keyboard input
    if (parsed.title) {
      console.log('[x-article] Filling title...');

      // Focus title input
      const titleInputSelectors = JSON.stringify(I18N_SELECTORS.titleInput);
      await cdp.send('Runtime.evaluate', {
        expression: `(() => {
          const selectors = ${titleInputSelectors};
          for (const sel of selectors) {
            const el = document.querySelector(sel);
            if (el) { el.focus(); return true; }
          }
          return false;
        })()`,
      }, { sessionId });
      await sleep(200);

      // Type title character by character using insertText
      await cdp.send('Input.insertText', { text: parsed.title }, { sessionId });
      await sleep(300);

      // Tab out to trigger save
      await cdp.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 }, { sessionId });
      await cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 }, { sessionId });
      await sleep(500);
    }

    // Insert HTML content
    console.log('[x-article] Inserting content...');

    // Read HTML content
    const htmlContent = fs.readFileSync(htmlPath, 'utf-8');

    // Focus on editor body
    await cdp.send('Runtime.evaluate', {
      expression: `(() => {
        const editor = document.querySelector(${JSON.stringify(EDITOR_INPUT_SELECTOR)});
        if (editor) {
          editor.focus();
          editor.click();
          return true;
        }
        return false;
      })()`,
    }, { sessionId });
    await sleep(300);

    // Method 1: Simulate paste event with HTML data
    console.log('[x-article] Attempting to insert HTML via paste event...');
    const pasteResult = await cdp.send<{ result: { value: boolean } }>('Runtime.evaluate', {
      expression: `(() => {
        const editor = document.querySelector(${JSON.stringify(EDITOR_INPUT_SELECTOR)});
        if (!editor) return false;

        const html = ${JSON.stringify(htmlContent)};

        // Create a paste event with HTML data
        const dt = new DataTransfer();
        dt.setData('text/html', html);
        dt.setData('text/plain', html.replace(/<[^>]*>/g, ''));

        const pasteEvent = new ClipboardEvent('paste', {
          bubbles: true,
          cancelable: true,
          clipboardData: dt
        });

        editor.dispatchEvent(pasteEvent);
        return true;
      })()`,
      returnByValue: true,
    }, { sessionId });

    await sleep(1000);

    // Check if content was inserted
    const contentCheck = await cdp.send<{ result: { value: number } }>('Runtime.evaluate', {
      expression: `document.querySelector(${JSON.stringify(EDITOR_CONTENT_SELECTOR)})?.innerText?.length || 0`,
      returnByValue: true,
    }, { sessionId });

    if (contentCheck.result.value > 50) {
      console.log(`[x-article] Content inserted successfully (${contentCheck.result.value} chars)`);
    } else {
      console.log('[x-article] Paste event may not have worked, trying insertHTML...');

      // Method 2: Use execCommand insertHTML
      await cdp.send('Runtime.evaluate', {
        expression: `(() => {
          const editor = document.querySelector(${JSON.stringify(EDITOR_INPUT_SELECTOR)});
          if (!editor) return false;
          editor.focus();
          document.execCommand('insertHTML', false, ${JSON.stringify(htmlContent)});
          return true;
        })()`,
      }, { sessionId });

      await sleep(1000);

      // Check again
      const check2 = await cdp.send<{ result: { value: number } }>('Runtime.evaluate', {
        expression: `document.querySelector(${JSON.stringify(EDITOR_CONTENT_SELECTOR)})?.innerText?.length || 0`,
        returnByValue: true,
      }, { sessionId });

      if (check2.result.value > 50) {
        console.log(`[x-article] Content inserted via execCommand (${check2.result.value} chars)`);
      } else {
        console.log('[x-article] Auto-insert failed. HTML copied to clipboard - please paste manually (Cmd+V)');
        copyHtmlToClipboard(htmlPath);
        // Wait for manual paste
        console.log('[x-article] Waiting 30s for manual paste...');
        await sleep(30_000);
      }
    }

    // Insert content images (reverse order to maintain positions)
    if (parsed.contentImages.length > 0) {
      console.log('[x-article] Inserting content images...');

      // First, check what placeholders exist in the editor
      const editorContent = await cdp.send<{ result: { value: string } }>('Runtime.evaluate', {
        expression: `document.querySelector(${JSON.stringify(EDITOR_CONTENT_SELECTOR)})?.innerText || ''`,
        returnByValue: true,
      }, { sessionId });

      console.log('[x-article] Checking for placeholders in content...');
      for (const img of parsed.contentImages) {
        if (editorContent.result.value.includes(img.placeholder)) {
          console.log(`[x-article] Found: ${img.placeholder}`);
        } else {
          console.log(`[x-article] NOT found: ${img.placeholder}`);
        }
      }

      // Process images in sequential order (1, 2, 3, ...)
      const sortedImages = [...parsed.contentImages].sort((a, b) => a.blockIndex - b.blockIndex);

      for (let i = 0; i < sortedImages.length; i++) {
        const img = sortedImages[i]!;
        console.log(`[x-article] [${i + 1}/${sortedImages.length}] Inserting image at placeholder: ${img.placeholder}`);

        // Helper to select placeholder with retry
        const selectPlaceholder = async (maxRetries = 3): Promise<boolean> => {
          for (let attempt = 1; attempt <= maxRetries; attempt++) {
            // Find, scroll to, and select the placeholder text in the editor.
            await cdp!.send('Runtime.evaluate', {
              expression: `(() => {
                const editor = document.querySelector(${JSON.stringify(EDITOR_CONTENT_SELECTOR)});
                if (!editor) return false;

                const placeholder = ${JSON.stringify(img.placeholder)};

                // Search through all text nodes in the editor
                const walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT, null, false);
                let node;

                while ((node = walker.nextNode())) {
                  const text = node.textContent || '';
                  const idx = text.indexOf(placeholder);
                  if (idx !== -1) {
                    // Found the placeholder - scroll to it first
                    const parentElement = node.parentElement;
                    if (parentElement) {
                      parentElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }

                    // Select it
                    const range = document.createRange();
                    range.setStart(node, idx);
                    range.setEnd(node, idx + placeholder.length);
                    const sel = window.getSelection();
                    sel.removeAllRanges();
                    sel.addRange(range);
                    return true;
                  }
                }
                return false;
              })()`,
            }, { sessionId });

            // Wait for scroll and selection to settle
            await sleep(800);

            // Verify selection matches the placeholder
            const selectionCheck = await cdp!.send<{ result: { value: string } }>('Runtime.evaluate', {
              expression: `window.getSelection()?.toString() || ''`,
              returnByValue: true,
            }, { sessionId });

            const selectedText = selectionCheck.result.value.trim();
            if (selectedText === img.placeholder) {
              console.log(`[x-article] Selection verified: "${selectedText}"`);
              return true;
            }

            if (attempt < maxRetries) {
              console.log(`[x-article] Selection attempt ${attempt} got "${selectedText}", retrying...`);
              await sleep(500);
            } else {
              console.warn(`[x-article] Selection failed after ${maxRetries} attempts, got: "${selectedText}"`);
            }
          }
          return false;
        };

        // Try to select the placeholder
        const selected = await selectPlaceholder(3);
        if (!selected) {
          throw new Error(`Could not select ${img.placeholder}. Not continuing because preview would retain an image placeholder.`);
        }

        console.log(`[x-article] Copying image: ${path.basename(img.localPath)}`);

        // Retry logic for image insertion
        let imageAppeared = false;
        const maxRetries = 2;

        for (let retry = 0; retry < maxRetries && !imageAppeared; retry++) {
          if (retry > 0) {
            console.log(`[x-article] Retry ${retry}/${maxRetries - 1} for image: ${path.basename(img.localPath)}`);
            // Re-select placeholder for retry
            const reselected = await selectPlaceholder(3);
            if (!reselected) {
              console.warn(`[x-article] Could not re-select placeholder for retry`);
              break;
            }
          }

          // Copy image to clipboard
          if (!copyImageToClipboard(img.localPath)) {
            console.warn(`[x-article] Failed to copy image to clipboard`);
            continue;
          }

          // Wait for clipboard to be fully ready (longer on Windows for large images)
          await sleep(3500);

          const beforePaste = await cdp.send<{ result: { value: { imageCount: number; hasPlaceholder: boolean } } }>('Runtime.evaluate', {
            expression: `(() => {
              const editor = document.querySelector(${JSON.stringify(EDITOR_CONTENT_SELECTOR)});
              return {
                imageCount: editor?.querySelectorAll('img').length || 0,
                hasPlaceholder: !!editor?.innerText.includes(${JSON.stringify(img.placeholder)}),
              };
            })()`,
            returnByValue: true,
          }, { sessionId });

          if (!beforePaste.result.value.hasPlaceholder) {
            console.warn(`[x-article] Placeholder disappeared before paste; retrying selection to avoid corrupting image positions.`);
            continue;
          }

          // Focus editor to keep the selected placeholder as the paste target.
          await cdp.send('Runtime.evaluate', {
            expression: `(() => {
              const editor = document.querySelector(${JSON.stringify(EDITOR_INPUT_SELECTOR)});
              if (editor) editor.focus();
            })()`,
          }, { sessionId });
          await sleep(300);

          // Paste image using paste script (activates Chrome, sends real keystroke)
          console.log(`[x-article] Pasting image...`);
          if (pasteFromClipboard('Google Chrome', 5, 1000)) {
            console.log(`[x-article] Paste keystroke sent: ${path.basename(img.localPath)}`);
          } else {
            console.warn(`[x-article] Failed to send paste keystroke after retries`);
            continue;
          }

          // First, wait for image to appear in editor (not just paste keystroke)
          console.log(`[x-article] Waiting for image to appear in editor...`);
          const appearWaitTime = 10000; // 10 seconds to appear
          const appearStartTime = Date.now();

          while (Date.now() - appearStartTime < appearWaitTime) {
            await sleep(500);

            // Check if an image element appeared in the editor
            const imageCheck = await cdp.send<{ result: { value: { imageCount: number; hasPlaceholder: boolean } } }>('Runtime.evaluate', {
              expression: `(() => {
                const editor = document.querySelector(${JSON.stringify(EDITOR_CONTENT_SELECTOR)});
                return {
                  imageCount: editor?.querySelectorAll('img').length || 0,
                  hasPlaceholder: !!editor?.innerText.includes(${JSON.stringify(img.placeholder)}),
                };
              })()`,
              returnByValue: true,
            }, { sessionId });

            if (imageCheck.result.value.imageCount > beforePaste.result.value.imageCount && !imageCheck.result.value.hasPlaceholder) {
              imageAppeared = true;
              console.log(`[x-article] Image appeared in editor after ${Date.now() - appearStartTime}ms`);
              break;
            }

            if (imageCheck.result.value.imageCount > beforePaste.result.value.imageCount && imageCheck.result.value.hasPlaceholder) {
              console.warn(`[x-article] Image appeared but ${img.placeholder} remained. Removing placeholder text now...`);
              const removed = await removePlaceholderText(img.placeholder);
              if (!removed) {
                console.warn(`[x-article] Could not remove ${img.placeholder} after image appeared; retrying...`);
                continue;
              }

              const cleanupCheck = await cdp.send<{ result: { value: { imageCount: number; hasPlaceholder: boolean } } }>('Runtime.evaluate', {
                expression: `(() => {
                  const editor = document.querySelector(${JSON.stringify(EDITOR_CONTENT_SELECTOR)});
                  return {
                    imageCount: editor?.querySelectorAll('img').length || 0,
                    hasPlaceholder: !!editor?.innerText.includes(${JSON.stringify(img.placeholder)}),
                  };
                })()`,
                returnByValue: true,
              }, { sessionId });

              if (cleanupCheck.result.value.imageCount > beforePaste.result.value.imageCount && !cleanupCheck.result.value.hasPlaceholder) {
                imageAppeared = true;
                console.log(`[x-article] Placeholder removed after image insert: ${img.placeholder}`);
                break;
              }
            }
          }

          if (!imageAppeared) {
            const restoreCheck = await cdp.send<{ result: { value: boolean } }>('Runtime.evaluate', {
              expression: `(() => {
                const editor = document.querySelector(${JSON.stringify(EDITOR_CONTENT_SELECTOR)});
                return !!editor?.innerText.includes(${JSON.stringify(img.placeholder)});
              })()`,
              returnByValue: true,
            }, { sessionId });

            if (!restoreCheck.result.value) {
              console.warn(`[x-article] Paste removed placeholder without inserting an image; restoring placeholder for manual recovery.`);
              await cdp.send('Runtime.evaluate', {
                expression: `(() => {
                  const editor = document.querySelector(${JSON.stringify(EDITOR_INPUT_SELECTOR)});
                  if (!editor) return false;
                  editor.focus();
                  document.execCommand('insertText', false, ${JSON.stringify(img.placeholder)});
                  return true;
                })()`,
              }, { sessionId });
              await sleep(500);
            }
          }

          if (!imageAppeared && retry < maxRetries - 1) {
            console.warn(`[x-article] Image did not appear after ${appearWaitTime}ms, will retry...`);
            await sleep(1000);
          }
        }

        if (!imageAppeared) {
          console.warn(`[x-article] Image did not appear after ${maxRetries} attempts - skipping`);
          continue;
        }

        // Now wait for upload to complete
        console.log(`[x-article] Waiting for upload to complete...`);
        let uploadComplete = false;
        const maxWaitTime = 30000; // 30 seconds max
        const checkInterval = 2000; // Check every 2 seconds
        const startTime = Date.now();

        while (Date.now() - startTime < maxWaitTime) {
          await sleep(checkInterval);

          // Check if there are any upload progress indicators
          const uploadCheck = await cdp.send<{ result: { value: boolean } }>('Runtime.evaluate', {
            expression: `(() => {
              // Check for upload progress indicators (spinners, progress bars, etc.)
              const progressIndicators = document.querySelectorAll('[role="progressbar"], .upload-progress, [aria-label*="uploading" i], [aria-label*="上传" i]');
              return progressIndicators.length === 0; // Upload complete when no progress indicators
            })()`,
            returnByValue: true,
          }, { sessionId });

          if (uploadCheck.result.value) {
            uploadComplete = true;
            console.log(`[x-article] Upload completed after ${Date.now() - startTime}ms`);
            break;
          }
        }

        if (!uploadComplete) {
          console.warn(`[x-article] Upload may not have completed after ${maxWaitTime}ms`);
        }

        // Additional wait to ensure stability between images
        await sleep(1500);
      }

      console.log('[x-article] All images processed.');
    }

    console.log('[x-article] Verifying editor before preview...');
    const editorVerification = await cdp.send<{ result: { value: { imageCount: number; placeholderCount: number; placeholders: string[]; textLength: number; href: string } } }>('Runtime.evaluate', {
      expression: `(() => {
        const editor = document.querySelector(${JSON.stringify(EDITOR_CONTENT_SELECTOR)});
        const text = editor?.innerText || '';
        const placeholders = Array.from(new Set(text.match(/\\[\\[IMAGE_PLACEHOLDER_\\d+\\]\\]|NEMO_X_IMAGE_\\d+/g) || []));
        return {
          imageCount: editor?.querySelectorAll('img').length || 0,
          placeholderCount: placeholders.length,
          placeholders,
          textLength: text.length,
          href: location.href,
        };
      })()`,
      returnByValue: true,
    }, { sessionId });

    const editorState = editorVerification.result.value;
    console.log(`[x-article] Editor verification: ${editorState.imageCount}/${parsed.contentImages.length} images, ${editorState.placeholderCount} placeholders, ${editorState.textLength} chars`);

    if (editorState.placeholderCount > 0) {
      throw new Error(`Editor still contains ${editorState.placeholderCount} image placeholder(s): ${editorState.placeholders.join(', ')}. Not opening preview. Draft URL: ${editorState.href}`);
    }

    if (editorState.imageCount < parsed.contentImages.length) {
      throw new Error(`Editor contains ${editorState.imageCount} image(s), expected at least ${parsed.contentImages.length}. Not opening publish flow.`);
    }

    // Before preview: blur editor to trigger save
    console.log('[x-article] Triggering content save...');
    await cdp.send('Runtime.evaluate', {
      expression: `(() => {
        // Blur editor to trigger any pending saves
        const editor = document.querySelector(${JSON.stringify(EDITOR_INPUT_SELECTOR)});
        if (editor) {
          editor.blur();
        }
        // Also click elsewhere to ensure focus is lost
        document.body.click();
      })()`,
    }, { sessionId });
    await sleep(1500);

    // Click Preview button
    console.log('[x-article] Opening preview...');
    const previewSelectors = JSON.stringify(I18N_SELECTORS.previewButton);
    const previewClicked = await cdp.send<{ result: { value: boolean } }>('Runtime.evaluate', {
      expression: `(() => {
        const selectors = ${previewSelectors};
        for (const sel of selectors) {
          const el = document.querySelector(sel);
          if (el) { el.click(); return true; }
        }
        return false;
      })()`,
      returnByValue: true,
    }, { sessionId });

    if (previewClicked.result.value) {
      console.log('[x-article] Preview opened');
      await sleep(3000);
    } else {
      console.log('[x-article] Preview button not found');
    }

    const previewVerification = await cdp.send<{ result: { value: { href: string; hasTitle: boolean; imageCount: number; placeholderCount: number } } }>('Runtime.evaluate', {
      expression: `(() => {
        const text = document.body.innerText || '';
        return {
          href: location.href,
          hasTitle: ${JSON.stringify(parsed.title)} ? text.includes(${JSON.stringify(parsed.title)}) : true,
          imageCount: document.querySelectorAll('img').length,
          placeholderCount: (text.match(/IMAGE_PLACEHOLDER|NEMO_X_IMAGE/g) || []).length,
        };
      })()`,
      returnByValue: true,
    }, { sessionId });

    const previewState = previewVerification.result.value;
    console.log(`[x-article] Preview verification: url=${previewState.href}, title=${previewState.hasTitle}, images=${previewState.imageCount}, placeholders=${previewState.placeholderCount}`);

    if (previewState.placeholderCount > 0) {
      throw new Error(`Preview still contains ${previewState.placeholderCount} image placeholder(s).`);
    }

    if (!previewState.hasTitle) {
      throw new Error('Preview does not contain the expected article title.');
    }

    // X Articles should stop at preview. The final publish click is intentionally
    // manual so the account owner can make the last audience/reply decision.
    if (submit) {
      console.log('[x-article] --submit is ignored for X Articles. Preview is ready; publish manually after review.');
    } else {
      console.log('[x-article] Article composed and preview opened. Publish manually after review.');
    }

  } finally {
    // Disconnect CDP but keep browser open
    if (cdp) {
      cdp.close();
    }
    // Don't kill Chrome - let user review and close manually
  }
}

function printUsage(): never {
  console.log(`Publish Markdown article to X (Twitter) Articles

Usage:
  npx -y bun x-article.ts <markdown_file> [options]

Options:
  --title <title>     Override title
  --cover <image>     Override cover image
  --submit            Ignored for X Articles; final publish is manual
  --profile <dir>     Chrome profile directory
  --help              Show this help

Markdown frontmatter:
  ---
  title: My Article Title
  cover_image: /path/to/cover.jpg
  ---

Example:
  npx -y bun x-article.ts article.md
  npx -y bun x-article.ts article.md --cover ./hero.png
  npx -y bun x-article.ts article.md --submit  # still stops at preview
`);
  process.exit(0);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    printUsage();
  }

  let markdownPath: string | undefined;
  let title: string | undefined;
  let coverImage: string | undefined;
  let submit = false;
  let profileDir: string | undefined;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i]!;
    if (arg === '--title' && args[i + 1]) {
      title = args[++i];
    } else if (arg === '--cover' && args[i + 1]) {
      coverImage = args[++i];
    } else if (arg === '--submit') {
      submit = true;
    } else if (arg === '--profile' && args[i + 1]) {
      profileDir = args[++i];
    } else if (!arg.startsWith('-')) {
      markdownPath = arg;
    }
  }

  if (!markdownPath) {
    console.error('Error: Markdown file path required');
    process.exit(1);
  }

  if (!fs.existsSync(markdownPath)) {
    console.error(`Error: File not found: ${markdownPath}`);
    process.exit(1);
  }

  await publishArticle({ markdownPath, title, coverImage, submit, profileDir });
}

await main().catch((err) => {
  console.error(`Error: ${err instanceof Error ? err.message : String(err)}`);
  process.exit(1);
});
