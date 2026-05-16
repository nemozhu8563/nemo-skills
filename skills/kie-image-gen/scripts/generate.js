#!/usr/bin/env node

const fs = require('fs');
const os = require('os');
const path = require('path');
const https = require('https');

function getUserConfigDir() {
  if (process.platform === 'win32') {
    return path.join(process.env.APPDATA || path.join(os.homedir(), 'AppData', 'Roaming'), 'baoyu-skills', 'kie-image-gen');
  }
  if (process.platform === 'darwin') {
    return path.join(os.homedir(), 'Library', 'Application Support', 'baoyu-skills', 'kie-image-gen');
  }
  return path.join(process.env.XDG_CONFIG_HOME || path.join(os.homedir(), '.config'), 'baoyu-skills', 'kie-image-gen');
}

function parseEnvFile(envPath) {
  const envContent = fs.readFileSync(envPath, 'utf8');
  envContent.split('\n').forEach(line => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) return;

    const idx = trimmed.indexOf('=');
    if (idx === -1) return;

    const key = trimmed.slice(0, idx).trim();
    let value = trimmed.slice(idx + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }

    if (key && value && !process.env[key]) {
      process.env[key] = value;
    }
  });
}

// Load environment variables with file priority:
// ~/.baoyu-skills/.env -> user config dir -> <cwd>/.baoyu-skills/.env
// process.env remains highest priority because existing keys are never overwritten.
function loadEnv() {
  const possiblePaths = [
    path.join(os.homedir(), '.baoyu-skills', '.env'),
    path.join(getUserConfigDir(), '.env'),
    path.join(process.cwd(), '.baoyu-skills', '.env'),
  ];

  for (const envPath of possiblePaths) {
    if (fs.existsSync(envPath)) {
      parseEnvFile(envPath);
    }
  }
}

loadEnv();

const API_KEY = process.env.KIE_API_KEY;
const BASE_URL = 'https://api.kie.ai/api/v1/jobs';

if (!API_KEY) {
  console.error('Error: KIE_API_KEY not found in environment variables');
  console.error('Get your API key from: https://kie.ai/api-key');
  console.error('');
  console.error('Supported config locations:');
  console.error('  1. process.env.KIE_API_KEY');
  console.error('  2. <cwd>/.baoyu-skills/.env');
  console.error(`  3. ${path.join(getUserConfigDir(), '.env')}`);
  console.error(`  4. ${path.join(os.homedir(), '.baoyu-skills', '.env')}`);
  process.exit(1);
}

// Parse command line arguments
const args = process.argv.slice(2);
let prompt = '';
let aspectRatio = '1:1';
let outputPath = './output.png';
let format = 'png';

for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  if (arg.startsWith('--aspect-ratio=') || arg === '--aspect-ratio') {
    aspectRatio = arg.includes('=') ? arg.split('=')[1] : args[++i];
  } else if (arg.startsWith('--output=') || arg === '--output') {
    outputPath = arg.includes('=') ? arg.split('=')[1] : args[++i];
  } else if (arg.startsWith('--format=') || arg === '--format') {
    format = arg.includes('=') ? arg.split('=')[1] : args[++i];
  } else if (!prompt) {
    prompt = arg;
  }
}

if (!prompt) {
  console.error('Usage: node generate.js "<prompt>" [options]');
  console.error('');
  console.error('Options:');
  console.error('  --aspect-ratio=<ratio>  Image aspect ratio (default: 1:1)');
  console.error('                          Options: 1:1, 16:9, 9:16, 4:3, 3:4, 21:9, etc.');
  console.error('  --output=<path>         Output file path (default: ./output.png)');
  console.error('  --format=<format>       Output format: jpg or png (default: png)');
  process.exit(1);
}

// Create task
async function createTask() {
  const payload = {
    model: 'nano-banana-2',
    input: {
      prompt: prompt,
      aspect_ratio: aspectRatio,
      resolution: '1K',
      output_format: format === 'png' ? 'png' : 'jpg',
      google_search: false
    }
  };

  return new Promise((resolve, reject) => {
    const data = JSON.stringify(payload);
    const options = {
      hostname: 'api.kie.ai',
      path: '/api/v1/jobs/createTask',
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': Buffer.byteLength(data, 'utf8')
      }
    };

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        try {
          const response = JSON.parse(body);
          if (response.code === 200) {
            resolve(response.data.taskId);
          } else {
            reject(new Error(`API Error: ${response.msg}`));
          }
        } catch (error) {
          reject(new Error(`Failed to parse response: ${body}`));
        }
      });
    });

    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

// Query task status
async function queryTask(taskId) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.kie.ai',
      path: `/api/v1/jobs/recordInfo?taskId=${taskId}`,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${API_KEY}`
      }
    };

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        try {
          const response = JSON.parse(body);
          if (response.code === 200) {
            resolve(response.data);
          } else {
            reject(new Error(`API Error: ${response.msg}`));
          }
        } catch (error) {
          reject(new Error(`Failed to parse response: ${body}`));
        }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

// Download image
async function downloadImage(url, outputPath) {
  return new Promise((resolve, reject) => {
    // Ensure output directory exists
    const outputDir = path.dirname(outputPath);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    https.get(url, (res) => {
      const fileStream = fs.createWriteStream(outputPath);
      res.pipe(fileStream);
      fileStream.on('finish', () => {
        fileStream.close();
        resolve();
      });
      fileStream.on('error', reject);
    }).on('error', reject);
  });
}

// Main function
async function main() {
  try {
    console.log('Creating generation task...');
    console.log(`Prompt: ${prompt}`);
    console.log(`Aspect Ratio: ${aspectRatio}`);
    console.log(`Resolution: 1K`);
    console.log('');

    const taskId = await createTask();
    console.log(`Task created: ${taskId}`);
    console.log('Waiting for generation to complete...');

    let attempts = 0;
    const maxAttempts = 60; // 2 minutes max

    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
      const taskData = await queryTask(taskId);

      if (taskData.state === 'success') {
        const resultJson = JSON.parse(taskData.resultJson);
        const imageUrl = resultJson.resultUrls[0];

        console.log('\nGeneration complete! Downloading image...');
        await downloadImage(imageUrl, outputPath);

        console.log('');
        console.log('✓ Success!');
        console.log(`  Output: ${path.resolve(outputPath)}`);
        console.log(`  URL: ${imageUrl}`);
        console.log(`  Time: ${taskData.costTime}ms`);
        return;
      } else if (taskData.state === 'fail') {
        throw new Error(`Generation failed: ${taskData.failMsg} (Code: ${taskData.failCode})`);
      }

      attempts++;
      process.stdout.write('.');
    }

    throw new Error('Timeout: Generation took too long (>2 minutes)');
  } catch (error) {
    console.error(`\n✗ Error: ${error.message}`);
    process.exit(1);
  }
}

main();
