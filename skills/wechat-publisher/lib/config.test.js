import { afterEach, describe, expect, it } from 'bun:test';
import { existsSync } from 'fs';
import { mkdtemp, readFile, rm } from 'fs/promises';
import { join } from 'path';
import { tmpdir } from 'os';
import { DEFAULT_CONFIG, getConfigPath, readConfig, saveConfig } from './config.js';

const tempDirs = [];

async function makeTempConfigPath() {
  const dir = await mkdtemp(join(tmpdir(), 'wechat-config-'));
  tempDirs.push(dir);
  return join(dir, 'wechat-publisher.json');
}

afterEach(async () => {
  delete process.env.WECHAT_PUBLISHER_CONFIG;
  while (tempDirs.length > 0) {
    const dir = tempDirs.pop();
    await rm(dir, { recursive: true, force: true });
  }
});

describe('Configuration Management', () => {
  it('creates default config if missing', async () => {
    const configPath = await makeTempConfigPath();

    const config = await readConfig({ configPath });

    expect(config).toEqual(DEFAULT_CONFIG);
    expect(existsSync(configPath)).toBe(true);
  });

  it('reads existing config from an explicit path', async () => {
    const configPath = await makeTempConfigPath();
    const testConfig = {
      wechat: { appId: 'test123', appSecret: 'secret456' },
      proxy: { enabled: true, url: 'http://127.0.0.1:10808' },
      defaults: { template: 'template-minimal' }
    };

    await saveConfig(testConfig, { configPath });
    const config = await readConfig({ configPath });

    expect(config.wechat.appId).toBe('test123');
    expect(config.wechat.appSecret).toBe('secret456');
    expect(config.proxy.enabled).toBe(true);
    expect(config.proxy.url).toBe('http://127.0.0.1:10808');
    expect(config.defaults.template).toBe('template-minimal');
  });

  it('uses env override when no explicit path is provided', async () => {
    const configPath = await makeTempConfigPath();
    process.env.WECHAT_PUBLISHER_CONFIG = configPath;

    await saveConfig({ wechat: { appId: 'env-id', appSecret: 'env-secret' } });
    const config = await readConfig();

    expect(getConfigPath()).toBe(configPath);
    expect(config.wechat.appId).toBe('env-id');
    expect(config.wechat.appSecret).toBe('env-secret');
  });

  it('throws a clear error for malformed config json', async () => {
    const configPath = await makeTempConfigPath();
    await Bun.write(configPath, '{bad json');

    await expect(readConfig({ configPath })).rejects.toThrow();
  });

  it('writes merged defaults when saving partial config', async () => {
    const configPath = await makeTempConfigPath();

    await saveConfig({ wechat: { appId: 'partial' } }, { configPath });
    const raw = JSON.parse(await readFile(configPath, 'utf-8'));

    expect(raw.wechat.appId).toBe('partial');
    expect(raw.wechat.appSecret).toBe('');
    expect(raw.proxy.enabled).toBe(false);
    expect(raw.defaults.template).toBe('template-tech');
  });
});
