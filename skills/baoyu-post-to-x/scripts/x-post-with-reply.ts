import process from 'node:process';

import { postToX } from './x-browser.js';
import { replyToX } from './x-reply.js';
import { closeChromeDebugSession, getDefaultProfileDir } from './x-utils.js';

function printUsage(exitCode = 0): never {
  console.log(`Usage: npx -y bun x-post-with-reply.ts --submit --reply <reply text> <main post text>

Options:
  --reply <text>     Reply text posted under the main post
  --image <path>     Add image to the main post (repeatable, max 4)
  --submit           Submit both the main post and reply
  --profile <dir>    Dedicated Chrome profile directory`);
  process.exit(exitCode);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  if (args.includes('--help') || args.includes('-h')) printUsage();

  const images: string[] = [];
  const textParts: string[] = [];
  let replyText: string | undefined;
  let profileDir: string | undefined;
  let submit = false;
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index]!;
    if (arg === '--reply' && args[index + 1]) replyText = args[++index];
    else if (arg === '--image' && args[index + 1]) images.push(args[++index]!);
    else if (arg === '--profile' && args[index + 1]) profileDir = args[++index];
    else if (arg === '--submit') submit = true;
    else if (!arg.startsWith('-')) textParts.push(arg);
  }
  const text = textParts.join(' ').trim();
  if (!text) printUsage(1);
  if (submit && !replyText?.trim()) throw new Error('--reply is required with --submit.');

  let mainPostSubmitted = false;
  let mainPostUrl: string | undefined;
  let replySubmitted = false;
  let retainedChrome = false;
  const activeProfileDir = profileDir ?? getDefaultProfileDir();
  try {
    const mainPost = await postToX({
      text,
      images,
      submit,
      profileDir: activeProfileDir,
      keepChromeOpen: submit,
    });
    mainPostSubmitted = submit;
    mainPostUrl = mainPost.postUrl;
    retainedChrome = mainPost.retainedChrome === true;
    if (!submit) {
      console.log('[x-post-with-reply] Main post composed in preview mode; reply was skipped.');
      return;
    }
    if (!mainPostUrl) throw new Error('Main post submitted, but its X status URL was not detected; reply was not posted.');
    const reply = await replyToX({ tweetUrl: mainPostUrl, text: replyText!, submit: true, profileDir: activeProfileDir });
    replySubmitted = reply.submitted;
    if (!replySubmitted) throw new Error('Reply composer completed without submitting the reply.');
    console.log('[x-post-with-reply] Main post and reply submitted.');
  } catch (error) {
    console.error(`[x-post-with-reply] Stages: main_post_submitted=${mainPostSubmitted}; main_post_url=${mainPostUrl ?? 'unavailable'}; reply_submitted=${replySubmitted}`);
    throw error;
  } finally {
    if (retainedChrome) {
      try {
        await closeChromeDebugSession(activeProfileDir);
      } catch (error) {
        console.warn(`[x-post-with-reply] Failed to close retained Chrome session: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
  }
}

if (import.meta.main) {
  await main().catch((error) => {
    console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  });
}
