// lib/config.js
import { readFile, writeFile, mkdir } from 'fs/promises';
import { join, dirname } from 'path';
import { homedir } from 'os';
import { existsSync } from 'fs';

const DEFAULT_CONFIG = {
  wechat: {
    appId: '',
    appSecret: ''
  },
  proxy: {
    enabled: false,
    url: ''
  },
  defaults: {
    template: 'template-tech'
  }
};

export function getDefaultConfigPath() {
  return join(homedir(), '.agents', 'wechat-publisher.json');
}

export function getConfigPath(options = {}) {
  return options.configPath || process.env.WECHAT_PUBLISHER_CONFIG || getDefaultConfigPath();
}

function mergeConfig(config = {}) {
  return {
    wechat: {
      appId: config.wechat?.appId || DEFAULT_CONFIG.wechat.appId,
      appSecret: config.wechat?.appSecret || DEFAULT_CONFIG.wechat.appSecret
    },
    proxy: {
      enabled: config.proxy?.enabled ?? DEFAULT_CONFIG.proxy.enabled,
      url: config.proxy?.url || DEFAULT_CONFIG.proxy.url
    },
    defaults: {
      template: config.defaults?.template || DEFAULT_CONFIG.defaults.template
    }
  };
}

async function ensureConfigFile(configPath) {
  const configDir = dirname(configPath);

  if (!existsSync(configDir)) {
    await mkdir(configDir, { recursive: true });
  }

  if (!existsSync(configPath)) {
    await writeFile(configPath, JSON.stringify(DEFAULT_CONFIG, null, 2));
    return false;
  }

  return true;
}

export async function readConfig(options = {}) {
  const configPath = getConfigPath(options);
  const configExists = await ensureConfigFile(configPath);

  if (!configExists) {
    return DEFAULT_CONFIG;
  }

  const content = await readFile(configPath, 'utf-8');
  const config = JSON.parse(content);
  return mergeConfig(config);
}

export async function saveConfig(config, options = {}) {
  const configPath = getConfigPath(options);
  const configDir = dirname(configPath);

  if (!existsSync(configDir)) {
    await mkdir(configDir, { recursive: true });
  }

  await writeFile(configPath, JSON.stringify(mergeConfig(config), null, 2));
}

export { DEFAULT_CONFIG };
