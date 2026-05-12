---
name: kie-image-gen
description: Provider/channel for kie.ai Nano Banana image generation. Prefer `baoyu-image-gen` for ordinary user-facing image requests; use this skill directly only when the kie.ai backend is explicitly required.
---

# Kie Image Generator

Provider for kie.ai's Nano Banana 2 model with 1K resolution. It is designed to be called by router or visual workflow skills.

## Prerequisites

**API Key Required**: Get your API key from https://kie.ai/api-key

Recommended: store the key outside the repository in a user-level config file.

Supported config locations, in load order:

1. `process.env.KIE_API_KEY`
2. `<cwd>/.baoyu-skills/.env`
3. Windows: `%APPDATA%\baoyu-skills\kie-image-gen\.env`
4. macOS: `~/Library/Application Support/baoyu-skills/kie-image-gen/.env`
5. Linux: `${XDG_CONFIG_HOME:-~/.config}/baoyu-skills/kie-image-gen/.env`
6. `~/.baoyu-skills/.env`

Example `.env`:

```bash
KIE_API_KEY=your-api-key-here
```

You can also set an environment variable directly:
```bash
export KIE_API_KEY="your-api-key-here"
```

## Usage

This skill is designed to be called by other image generation skills (like `baoyu-cover-image`, `baoyu-article-illustrator`).

**Direct usage**:
```bash
/kie-image-gen "A beautiful sunset over mountains"
```

**With options**:
```bash
/kie-image-gen "A beautiful sunset" --aspect-ratio 16:9 --output sunset.png
```

**IMPORTANT - Path Best Practices**:

When calling this skill from scripts or other skills, **always use absolute paths** for the `--output` parameter to avoid path resolution issues:

```bash
# ✅ GOOD: Use absolute path
node scripts/generate.js "prompt" --output="/absolute/path/to/output.png"

# ❌ BAD: Relative path may resolve incorrectly if working directory changes
cd some/directory && node scripts/generate.js "prompt" --output="../../output.png"
```

**Why absolute paths?**
- The script resolves relative paths based on `process.cwd()` (current working directory)
- If you `cd` into a different directory before running the script, relative paths will resolve incorrectly
- Absolute paths always work regardless of where the script is executed from

**Example in practice**:
```bash
# Get absolute path first
PROJECT_ROOT="/c/Users/username/project"

# Use absolute path for output
node .claude/skills/kie-image-gen/scripts/generate.js \
  "A beautiful sunset" \
  --aspect-ratio 16:9 \
  --output="${PROJECT_ROOT}/assets/sunset.png"
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--aspect-ratio <ratio>` | Image aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4, 21:9, etc.) | `1:1` |
| `--output <path>` | Output file path | `./output.png` |
| `--format <format>` | Output format (jpg, png) | `png` |

**Note on aspect ratios**:
- For WeChat Official Account covers (2.35:1 required), use `21:9` (2.33:1) which is visually identical
- If exact 2.35:1 is needed, use `scripts/crop-to-wechat.js` to crop the generated image

## Workflow

### Step 1: Validate API Key

Check if `KIE_API_KEY` environment variable is set:
- Read from environment variable
- Or read from user-level config file
- Or read from `<cwd>/.baoyu-skills/.env`
- If not found, show error and exit

### Step 2: Prepare Request

Build request payload:
```javascript
{
  "model": "nano-banana-2",
  "input": {
    "prompt": "<user-prompt>",
    "aspect_ratio": "<aspect-ratio>",  // from --aspect-ratio option
    "resolution": "1K",                 // fixed to 1K
    "output_format": "<format>",        // from --format option
    "google_search": false
  }
}
```

### Step 3: Create Generation Task

Call kie.ai API to create task:
```bash
curl -X POST https://api.kie.ai/api/v1/jobs/createTask \
  -H "Authorization: Bearer $KIE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '<request-payload>'
```

Extract `taskId` from response.

### Step 4: Poll Task Status

Poll task status every 2 seconds:
```bash
curl -X GET "https://api.kie.ai/api/v1/jobs/recordInfo?taskId=<taskId>" \
  -H "Authorization: Bearer $KIE_API_KEY"
```

Check `data.state`:
- `waiting`: Continue polling
- `success`: Extract result URL from `data.resultJson`
- `fail`: Show error from `data.failMsg` and exit

**Max polling time**: 120 seconds (60 attempts × 2 seconds)

### Step 5: Download Image

When task succeeds:
1. Parse `data.resultJson` to get `resultUrls[0]`
2. Download image from URL
3. Save to output path

### Step 6: Output Result

Show success message with:
- Output file path
- Image URL
- Generation time (from `data.costTime`)

## Implementation Script

Create `scripts/generate.js`:

```javascript
#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const https = require('https');

// Load environment variables
require('dotenv').config();

const API_KEY = process.env.KIE_API_KEY;
const BASE_URL = 'https://api.kie.ai/api/v1/jobs';

if (!API_KEY) {
  console.error('Error: KIE_API_KEY not found in environment variables');
  console.error('Get your API key from: https://kie.ai/api-key');
  process.exit(1);
}

// Parse command line arguments
const args = process.argv.slice(2);
const prompt = args[0];
const aspectRatio = args.find(arg => arg.startsWith('--aspect-ratio='))?.split('=')[1] || '1:1';
const outputPath = args.find(arg => arg.startsWith('--output='))?.split('=')[1] || './output.png';
const format = args.find(arg => arg.startsWith('--format='))?.split('=')[1] || 'png';

if (!prompt) {
  console.error('Usage: node generate.js "<prompt>" [--aspect-ratio=<ratio>] [--output=<path>] [--format=<format>]');
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
        'Content-Type': 'application/json',
        'Content-Length': data.length
      }
    };

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        const response = JSON.parse(body);
        if (response.code === 200) {
          resolve(response.data.taskId);
        } else {
          reject(new Error(`API Error: ${response.msg}`));
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
        const response = JSON.parse(body);
        if (response.code === 200) {
          resolve(response.data);
        } else {
          reject(new Error(`API Error: ${response.msg}`));
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
    https.get(url, (res) => {
      const fileStream = fs.createWriteStream(outputPath);
      res.pipe(fileStream);
      fileStream.on('finish', () => {
        fileStream.close();
        resolve();
      });
    }).on('error', reject);
  });
}

// Main function
async function main() {
  try {
    console.log('Creating generation task...');
    const taskId = await createTask();
    console.log(`Task created: ${taskId}`);

    console.log('Waiting for generation to complete...');
    let attempts = 0;
    const maxAttempts = 60;

    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 2000));
      const taskData = await queryTask(taskId);

      if (taskData.state === 'success') {
        const resultJson = JSON.parse(taskData.resultJson);
        const imageUrl = resultJson.resultUrls[0];

        console.log('Generation complete! Downloading image...');
        await downloadImage(imageUrl, outputPath);

        console.log(`\nSuccess!`);
        console.log(`Output: ${outputPath}`);
        console.log(`URL: ${imageUrl}`);
        console.log(`Time: ${taskData.costTime}ms`);
        return;
      } else if (taskData.state === 'fail') {
        throw new Error(`Generation failed: ${taskData.failMsg}`);
      }

      attempts++;
      process.stdout.write('.');
    }

    throw new Error('Timeout: Generation took too long');
  } catch (error) {
    console.error(`\nError: ${error.message}`);
    process.exit(1);
  }
}

main();
```

## Notes

- Resolution is fixed to 1K (1024x1024 or equivalent based on aspect ratio)
- Generation typically takes 10-30 seconds
- API key is required - get it from https://kie.ai/api-key
- Supports multiple aspect ratios: 1:1, 16:9, 9:16, 4:3, 3:4, 21:9, etc.
- Output format: jpg or png
