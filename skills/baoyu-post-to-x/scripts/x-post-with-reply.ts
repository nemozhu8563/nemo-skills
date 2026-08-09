import { mkdir, open, readFile, rename, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

import { postToX } from './x-browser.js';
import { ReplyVerificationError, replyToX, repoSlugFromReplyText } from './x-reply.js';
import { closeChromeDebugSession, getDefaultProfileDir } from './x-utils.js';

export type XPostWithReplyRunStatus = 'running' | 'preview' | 'succeeded' | 'failed';

export interface XPostWithReplyRunState {
  version: 1;
  status: XPostWithReplyRunStatus;
  pid: number;
  repoSlug?: string;
  startedAt: string;
  updatedAt: string;
  mainPostSubmitClicked: boolean;
  mainPostSubmitted: boolean;
  mainPostUrl?: string;
  replySubmitClicked: boolean;
  replySubmitted: boolean;
  replyVerified: boolean;
  error?: string;
}

export function createInitialRunState(replyText?: string): XPostWithReplyRunState {
  const now = new Date().toISOString();
  return {
    version: 1,
    status: 'running',
    pid: process.pid,
    repoSlug: replyText ? repoSlugFromReplyText(replyText) : undefined,
    startedAt: now,
    updatedAt: now,
    mainPostSubmitClicked: false,
    mainPostSubmitted: false,
    replySubmitClicked: false,
    replySubmitted: false,
    replyVerified: false,
  };
}

export async function writeRunState(resultFile: string, state: XPostWithReplyRunState): Promise<void> {
  if (!path.isAbsolute(resultFile)) throw new Error('--result-file must be an absolute path.');
  await mkdir(path.dirname(resultFile), { recursive: true });
  state.updatedAt = new Date().toISOString();
  const tempFile = `${resultFile}.${process.pid}.${Date.now()}.tmp`;
  await writeFile(tempFile, `${JSON.stringify(state, null, 2)}\n`, 'utf8');
  try {
    await rename(tempFile, resultFile);
  } catch (error) {
    const code = (error as NodeJS.ErrnoException).code;
    if (process.platform === 'win32' && (code === 'EEXIST' || code === 'EPERM')) {
      await rm(resultFile, { force: true });
      await rename(tempFile, resultFile);
      return;
    }
    await rm(tempFile, { force: true });
    throw error;
  }
}

export async function assertRunCanStart(resultFile: string): Promise<void> {
  if (!path.isAbsolute(resultFile)) throw new Error('--result-file must be an absolute path.');
  try {
    const existing = JSON.parse(await readFile(resultFile, 'utf8')) as Partial<XPostWithReplyRunState>;
    const unsafeToRepeat = existing.status === 'running'
      || existing.status === 'succeeded'
      || existing.mainPostSubmitClicked === true
      || existing.mainPostSubmitted === true
      || existing.replySubmitClicked === true;
    if (unsafeToRepeat) {
      throw new Error(
        `Refusing to start: result file already records a possibly active or externally visible run (${resultFile}).`,
      );
    }
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return;
    throw error;
  }
}

export async function claimRun(
  resultFile: string,
  state: XPostWithReplyRunState,
): Promise<string> {
  if (!path.isAbsolute(resultFile)) throw new Error('--result-file must be an absolute path.');
  await mkdir(path.dirname(resultFile), { recursive: true });
  const lockFile = `${resultFile}.lock`;
  try {
    const lockHandle = await open(lockFile, 'wx');
    try {
      await lockHandle.writeFile(`${JSON.stringify({ pid: process.pid, startedAt: state.startedAt })}\n`, 'utf8');
    } finally {
      await lockHandle.close();
    }
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'EEXIST') {
      throw new Error(`Refusing to start: another run owns the result-file lock (${lockFile}).`);
    }
    throw error;
  }

  try {
    await assertRunCanStart(resultFile);
    await writeRunState(resultFile, state);
    return lockFile;
  } catch (error) {
    await rm(lockFile, { force: true });
    throw error;
  }
}

function printUsage(exitCode = 0): never {
  console.log(`Usage: npx -y bun x-post-with-reply.ts --submit --reply <reply text> <main post text>

Options:
  --reply <text>     Reply text posted under the main post
  --image <path>     Add image to the main post (repeatable, max 4)
  --submit           Submit both the main post and reply
  --profile <dir>    Dedicated Chrome profile directory
  --result-file <path> Persist atomic machine-readable stage state
  --connect-port <port> Connect to an already-running Chrome debug port`);
  process.exit(exitCode);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  if (args.includes('--help') || args.includes('-h')) printUsage();

  const images: string[] = [];
  const textParts: string[] = [];
  let replyText: string | undefined;
  let profileDir: string | undefined;
  let resultFile: string | undefined;
  let connectPort: number | undefined;
  let submit = false;
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index]!;
    if (arg === '--reply' && args[index + 1]) replyText = args[++index];
    else if (arg === '--image' && args[index + 1]) images.push(args[++index]!);
    else if (arg === '--profile' && args[index + 1]) profileDir = args[++index];
    else if (arg === '--result-file' && args[index + 1]) resultFile = args[++index];
    else if (arg === '--connect-port' && args[index + 1]) {
      const parsedPort = Number.parseInt(args[++index]!, 10);
      if (!Number.isInteger(parsedPort) || parsedPort <= 0 || parsedPort > 65_535) {
        throw new Error('--connect-port must be a valid TCP port.');
      }
      connectPort = parsedPort;
    }
    else if (arg === '--submit') submit = true;
    else if (!arg.startsWith('-')) textParts.push(arg);
  }
  const text = textParts.join(' ').trim();
  if (!text) printUsage(1);
  if (submit && !replyText?.trim()) throw new Error('--reply is required with --submit.');

  let mainPostSubmitted = false;
  let mainPostSubmitClicked = false;
  let mainPostUrl: string | undefined;
  let replySubmitClicked = false;
  let replySubmitted = false;
  let replyVerified = false;
  let retainedChrome = false;
  const activeProfileDir = profileDir ?? getDefaultProfileDir();
  const runState = createInitialRunState(replyText);
  let runLockFile: string | undefined;
  let terminalStatePersisted = resultFile == null;
  if (resultFile) {
    runLockFile = await claimRun(resultFile, runState);
  }
  try {
    const mainPost = await postToX({
      text,
      images,
      submit,
      profileDir: activeProfileDir,
      connectPort,
      keepChromeOpen: submit,
      onSubmitClicked: async () => {
        mainPostSubmitClicked = true;
        runState.mainPostSubmitClicked = true;
        if (resultFile) await writeRunState(resultFile, runState);
      },
    });
    mainPostSubmitted = submit;
    mainPostUrl = mainPost.postUrl;
    retainedChrome = mainPost.retainedChrome === true;
    Object.assign(runState, { mainPostSubmitted, mainPostUrl });
    if (resultFile) await writeRunState(resultFile, runState);
    if (!submit) {
      runState.status = 'preview';
      if (resultFile) {
        await writeRunState(resultFile, runState);
        terminalStatePersisted = true;
      }
      console.log('[x-post-with-reply] Main post composed in preview mode; reply was skipped.');
      return;
    }
    if (!mainPostUrl) throw new Error('Main post submitted, but its X status URL was not detected; reply was not posted.');
    const reply = await replyToX({
      tweetUrl: mainPostUrl,
      text: replyText!,
      submit: true,
      profileDir: activeProfileDir,
      connectPort,
      onSubmitClicked: async () => {
        replySubmitClicked = true;
        runState.replySubmitClicked = true;
        if (resultFile) await writeRunState(resultFile, runState);
      },
    });
    replySubmitClicked = reply.submissionClicked;
    replySubmitted = reply.submitted;
    replyVerified = reply.verifiedOnPostPage;
    Object.assign(runState, { replySubmitClicked, replySubmitted, replyVerified });
    if (resultFile) await writeRunState(resultFile, runState);
    if (!replySubmitted) throw new Error('Reply composer completed without submitting the reply.');
    runState.status = 'succeeded';
    if (resultFile) {
      await writeRunState(resultFile, runState);
      terminalStatePersisted = true;
    }
    console.log('[x-post-with-reply] Main post and reply submitted.');
    console.log(`[x-post-with-reply] Result: ${JSON.stringify(runState)}`);
  } catch (error) {
    if (error instanceof ReplyVerificationError) replySubmitClicked = true;
    Object.assign(runState, {
      status: 'failed',
      mainPostSubmitClicked,
      mainPostSubmitted,
      mainPostUrl,
      replySubmitClicked,
      replySubmitted,
      replyVerified,
      error: error instanceof Error ? error.message : String(error),
    });
    if (resultFile) {
      try {
        await writeRunState(resultFile, runState);
        terminalStatePersisted = true;
      } catch (stateError) {
        console.error(`[x-post-with-reply] Failed to persist run state: ${stateError instanceof Error ? stateError.message : String(stateError)}`);
      }
    }
    console.error(`[x-post-with-reply] Stages: main_post_submit_clicked=${mainPostSubmitClicked}; main_post_submitted=${mainPostSubmitted}; main_post_url=${mainPostUrl ?? 'unavailable'}; reply_submit_clicked=${replySubmitClicked}; reply_submitted=${replySubmitted}; reply_verified=${replyVerified}`);
    console.error(`[x-post-with-reply] Result: ${JSON.stringify(runState)}`);
    throw error;
  } finally {
    if (retainedChrome) {
      try {
        await closeChromeDebugSession(activeProfileDir);
      } catch (error) {
        console.warn(`[x-post-with-reply] Failed to close retained Chrome session: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
    if (runLockFile && terminalStatePersisted) await rm(runLockFile, { force: true });
  }
}

if (import.meta.main) {
  await main().catch((error) => {
    console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  });
}
