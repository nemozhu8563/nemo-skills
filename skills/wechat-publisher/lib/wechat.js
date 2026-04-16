// lib/wechat.js
import axios from 'axios';
import FormData from 'form-data';
import fs from 'fs';
import https from 'https';
import { SocksProxyAgent } from 'socks-proxy-agent';

const API_BASE = 'https://api.weixin.qq.com/cgi-bin';

// Create https agent to avoid SSL issues
const httpsAgent = new https.Agent({
  rejectUnauthorized: false
});

export function getProxyConfig(config = {}) {
  const rawProxyUrl = config.proxy?.enabled ? config.proxy.url : '';
  if (!rawProxyUrl) {
    return null;
  }

  const proxyUrl = rawProxyUrl.includes('://') ? rawProxyUrl : `http://${rawProxyUrl}`;
  const parsed = new URL(proxyUrl);

  if (parsed.protocol.startsWith('socks')) {
    return {
      type: 'socks',
      url: proxyUrl
    };
  }

  return {
    type: 'http',
    protocol: parsed.protocol.replace(':', ''),
    host: parsed.hostname,
    port: parsed.port ? Number(parsed.port) : parsed.protocol === 'https:' ? 443 : 80
  };
}

function createAxiosOptions(config = {}) {
  const proxy = getProxyConfig(config);
  const options = {};

  if (proxy) {
    if (proxy.type === 'socks') {
      const agent = new SocksProxyAgent(proxy.url, {
        rejectUnauthorized: false
      });
      options.proxy = false;
      options.httpAgent = agent;
      options.httpsAgent = agent;
    } else {
      options.proxy = {
        protocol: proxy.protocol,
        host: proxy.host,
        port: proxy.port
      };
    }
  } else {
    options.httpsAgent = httpsAgent;
  }

  return options;
}

export async function getAccessToken(config) {
  const { appId, appSecret } = config.wechat;

  if (!appId || !appSecret) {
    throw new Error('WeChat AppID and AppSecret are required. Please run configuration.');
  }

  const url = `${API_BASE}/token`;
  const params = {
    grant_type: 'client_credential',
    appid: appId,
    secret: appSecret
  };

  try {
    const response = await axios.get(url, {
      params,
      ...createAxiosOptions(config)
    });

    if (response.data.errcode) {
      throw new Error(`WeChat API error: ${response.data.errmsg} (code: ${response.data.errcode})`);
    }

    return response.data.access_token;
  } catch (error) {
    if (error.response) {
      throw new Error(`WeChat API request failed: ${error.response.data.errmsg || error.message}`);
    }
    throw error;
  }
}

export async function uploadThumbToWechat(config, imagePath) {
  const accessToken = await getAccessToken(config);

  // Check if it's a URL or local path
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    // Download image from URL
    console.log(`  Downloading image from URL: ${imagePath}`);
    const imageResponse = await axios.get(imagePath, {
      responseType: 'arraybuffer',
      ...createAxiosOptions(config)
    });

    // Get file extension from URL or default to jpg
    const urlPath = new URL(imagePath).pathname;
    const ext = urlPath.split('.').pop() || 'jpg';

    // Create temp file
    const tempDir = process.env.TEMP || '/tmp';
    const tempPath = `${tempDir}/wechat_thumb_${Date.now()}.${ext}`;

    fs.writeFileSync(tempPath, imageResponse.data);

    // Upload to WeChat
    try {
      const mediaId = await uploadImageFile(config, tempPath);
      fs.unlinkSync(tempPath);
      return mediaId;
    } catch (error) {
      fs.unlinkSync(tempPath);
      throw error;
    }
  } else {
    // Local file path
    return await uploadImageFile(config, imagePath);
  }
}

async function uploadImageFile(config, imagePath) {
  const accessToken = await getAccessToken(config);

  if (!fs.existsSync(imagePath)) {
    throw new Error(`Image file not found: ${imagePath}`);
  }

  console.log(`  Uploading thumbnail to WeChat: ${imagePath}`);

  const formData = new FormData();
  formData.append('media', fs.createReadStream(imagePath));
  formData.append('type', 'thumb');

  const url = `${API_BASE}/material/add_material?access_token=${accessToken}&type=thumb`;

  try {
    const response = await axios.post(url, formData, {
      headers: formData.getHeaders(),
      ...createAxiosOptions(config)
    });

    if (response.data.errcode && response.data.errcode !== 0) {
      throw new Error(`WeChat API error: ${response.data.errmsg} (code: ${response.data.errcode})`);
    }

    console.log(`  Thumbnail uploaded successfully, media_id: ${response.data.media_id}`);
    return response.data.media_id;
  } catch (error) {
    if (error.response) {
      throw new Error(`Failed to upload thumbnail: ${error.response.data.errmsg || error.message}`);
    }
    throw error;
  }
}

export async function uploadArticleImageToWeChat(config, imagePath) {
  const accessToken = await getAccessToken(config);

  if (!fs.existsSync(imagePath)) {
    throw new Error(`Image file not found: ${imagePath}`);
  }

  console.log(`  Uploading article image to WeChat: ${imagePath}`);

  const formData = new FormData();
  formData.append('media', fs.createReadStream(imagePath));

  const url = `${API_BASE}/media/uploadimg?access_token=${accessToken}`;

  try {
    const response = await axios.post(url, formData, {
      headers: formData.getHeaders(),
      ...createAxiosOptions(config)
    });

    if (response.data.errcode && response.data.errcode !== 0) {
      throw new Error(`WeChat API error: ${response.data.errmsg} (code: ${response.data.errcode})`);
    }

    if (!response.data.url) {
      throw new Error(`WeChat API returned no url. Response: ${JSON.stringify(response.data)}`);
    }

    return response.data.url;
  } catch (error) {
    if (error.response) {
      throw new Error(`Failed to upload article image: ${error.response.data.errmsg || error.message}`);
    }
    throw error;
  }
}

export function buildArticlePayload({ html, title, thumbMediaId = null }) {
  const article = {
    title,
    author: '',
    digest: '',
    content: html,
    content_source_url: '',
    show_cover_pic: 0,
    need_open_comment: 1,
    only_fans_can_comment: 0
  };

  // Only add thumb_media_id if we have one
  if (thumbMediaId) {
    article.thumb_media_id = thumbMediaId;
    article.show_cover_pic = 1;
  }

  const payload = {
    articles: [article]
  };

  return payload;
}

export async function uploadToWeChat(config, html, filePath, thumbMediaId = null, articleTitle = null) {
  const accessToken = await getAccessToken(config);
  const title = articleTitle || filePath;
  const payload = buildArticlePayload({
    html,
    title,
    thumbMediaId
  });

  try {
    const url = `${API_BASE}/draft/add?access_token=${accessToken}`;
    const response = await axios.post(url, payload, createAxiosOptions(config));

    // Debug log
    console.log(`  Response: ${JSON.stringify(response.data)}`);

    // Check for error (only if errcode exists and is not 0)
    if (response.data.errcode && response.data.errcode !== 0) {
      throw new Error(`WeChat API error: ${response.data.errmsg} (code: ${response.data.errcode})`);
    }

    if (!response.data.media_id) {
      throw new Error(`WeChat API returned no media_id. Response: ${JSON.stringify(response.data)}`);
    }

    return {
      success: true,
      media_id: response.data.media_id,
      url: 'https://mp.weixin.qq.com/'
    };
  } catch (error) {
    if (error.response) {
      throw new Error(`Failed to upload to WeChat: ${error.response.data.errmsg || error.message}`);
    }
    throw error;
  }
}
