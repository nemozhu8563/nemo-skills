import { afterEach, describe, expect, test } from 'bun:test';
import { mkdtemp, readFile, readdir, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

import {
  assertRunCanStart,
  claimRun,
  createInitialRunState,
  writeRunState,
} from './x-post-with-reply.js';

const tempDirs: string[] = [];

afterEach(async () => {
  await Promise.all(tempDirs.splice(0).map((dir) => rm(dir, { recursive: true, force: true })));
});

async function tempResultFile(): Promise<string> {
  const dir = await mkdtemp(path.join(os.tmpdir(), 'x-post-with-reply-'));
  tempDirs.push(dir);
  return path.join(dir, 'data', 'run.json');
}

describe('x-post-with-reply run state', () => {
  test('persists atomic structured state without leaving temporary files', async () => {
    const resultFile = await tempResultFile();
    const state = createInitialRunState('项目地址：https://github.com/Google/skills');

    await writeRunState(resultFile, state);
    state.status = 'succeeded';
    state.mainPostSubmitted = true;
    state.mainPostUrl = 'https://x.com/nemoisme/status/123';
    state.replySubmitClicked = true;
    state.replySubmitted = true;
    state.replyVerified = true;
    await writeRunState(resultFile, state);

    const persisted = JSON.parse(await readFile(resultFile, 'utf8'));
    expect(persisted.status).toBe('succeeded');
    expect(persisted.repoSlug).toBe('google/skills');
    expect(persisted.replyVerified).toBe(true);
    expect(await readdir(path.dirname(resultFile))).toEqual(['run.json']);
  });

  test('blocks a duplicate run after an externally visible stage', async () => {
    const resultFile = await tempResultFile();
    const state = createInitialRunState('项目地址：https://github.com/google/skills');
    state.status = 'failed';
    state.mainPostSubmitClicked = true;
    await writeRunState(resultFile, state);

    await expect(assertRunCanStart(resultFile)).rejects.toThrow('Refusing to start');
  });

  test('allows retry when a previous failure occurred before submission', async () => {
    const resultFile = await tempResultFile();
    const state = createInitialRunState('项目地址：https://github.com/google/skills');
    state.status = 'failed';
    state.error = 'Chrome failed before composer was ready';
    await writeRunState(resultFile, state);

    await expect(assertRunCanStart(resultFile)).resolves.toBeUndefined();
  });

  test('uses an exclusive lock to reject concurrent starts', async () => {
    const resultFile = await tempResultFile();
    const state = createInitialRunState('项目地址：https://github.com/google/skills');
    const lockFile = await claimRun(resultFile, state);

    await expect(claimRun(resultFile, createInitialRunState())).rejects.toThrow('result-file lock');
    await rm(lockFile, { force: true });
  });

  test('requires result files to live at an explicit absolute path', async () => {
    const state = createInitialRunState();
    await expect(writeRunState('relative/run.json', state)).rejects.toThrow('absolute path');
  });
});
