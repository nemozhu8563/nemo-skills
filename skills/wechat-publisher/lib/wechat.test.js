import { describe, expect, it } from 'bun:test';
import { getAccessToken, uploadToWeChat, getProxyConfig, buildArticlePayload } from './wechat.js';

describe('WeChat API Client', () => {
  it('throws on missing credentials', async () => {
    const config = {
      wechat: { appId: '', appSecret: '' }
    };

    await expect(getAccessToken(config)).rejects.toThrow(/AppID and AppSecret are required/);
  });

  it('throws on partial missing credentials', async () => {
    const config = {
      wechat: { appId: 'test', appSecret: '' }
    };

    await expect(getAccessToken(config)).rejects.toThrow(/AppID and AppSecret are required/);
  });

  it('parses proxy config with default http scheme', () => {
    const proxy = getProxyConfig({
      proxy: {
        enabled: true,
        url: '127.0.0.1:10808'
      }
    });

    expect(proxy).toEqual({
      type: 'http',
      protocol: 'http',
      host: '127.0.0.1',
      port: 10808
    });
  });

  it('parses socks proxy config', () => {
    const proxy = getProxyConfig({
      proxy: {
        enabled: true,
        url: 'socks5://127.0.0.1:10808'
      }
    });

    expect(proxy).toEqual({
      type: 'socks',
      url: 'socks5://127.0.0.1:10808'
    });
  });

  it('uses frontmatter title when building article payload', () => {
    const payload = buildArticlePayload({
      html: '<p>Test content</p>',
      title: '前言标题',
      thumbMediaId: null
    });

    expect(payload.articles[0].title).toBe('前言标题');
  });

  it('includes thumb media id when provided', () => {
    const payload = buildArticlePayload({
      html: '<p>Test content</p>',
      title: '标题',
      thumbMediaId: 'media-123'
    });

    expect(payload.articles[0].thumb_media_id).toBe('media-123');
    expect(payload.articles[0].show_cover_pic).toBe(1);
  });
});
