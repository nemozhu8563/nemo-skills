#!/usr/bin/env node

/**
 * Crop image to WeChat cover ratio (2.35:1)
 *
 * Usage: node crop-to-wechat.js <input-image> [output-image]
 *
 * Strategy:
 * 1. Generate image with 21:9 ratio (closest to 2.35:1)
 * 2. Crop to exact 2.35:1 by trimming top/bottom edges
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

// Parse arguments
const args = process.argv.slice(2);
const inputPath = args[0];
const outputPath = args[1] || inputPath.replace(/(\.\w+)$/, '-wechat$1');

if (!inputPath) {
  console.error('Usage: node crop-to-wechat.js <input-image> [output-image]');
  console.error('');
  console.error('Example:');
  console.error('  node crop-to-wechat.js cover.png cover-wechat.png');
  process.exit(1);
}

if (!fs.existsSync(inputPath)) {
  console.error(`Error: Input file not found: ${inputPath}`);
  process.exit(1);
}

async function cropToWechat() {
  try {
    // Check if Sharp is available (Node.js image processing)
    try {
      const sharp = require('sharp');
      await cropWithSharp(sharp);
      return;
    } catch (e) {
      console.log('Sharp not available, trying ImageMagick...');
    }

    // Fallback to ImageMagick
    await cropWithImageMagick();
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

async function cropWithSharp(sharp) {
  console.log('Using Sharp for cropping...');

  const image = sharp(inputPath);
  const metadata = await image.metadata();

  const { width, height } = metadata;
  const currentRatio = width / height;
  const targetRatio = 2.35;

  console.log(`Current: ${width}x${height} (${currentRatio.toFixed(2)}:1)`);
  console.log(`Target: 2.35:1`);

  let cropWidth, cropHeight, left, top;

  if (currentRatio > targetRatio) {
    // Image is wider than target, crop sides
    cropHeight = height;
    cropWidth = Math.round(height * targetRatio);
    left = Math.round((width - cropWidth) / 2);
    top = 0;
  } else {
    // Image is taller than target, crop top/bottom
    cropWidth = width;
    cropHeight = Math.round(width / targetRatio);
    left = 0;
    top = Math.round((height - cropHeight) / 2);
  }

  console.log(`Cropping to: ${cropWidth}x${cropHeight}`);

  await image
    .extract({ left, top, width: cropWidth, height: cropHeight })
    .toFile(outputPath);

  console.log(`✓ Success! Saved to: ${outputPath}`);
  console.log(`  Final size: ${cropWidth}x${cropHeight} (${(cropWidth/cropHeight).toFixed(2)}:1)`);
}

async function cropWithImageMagick() {
  console.log('Using ImageMagick for cropping...');

  // Get image dimensions
  const { stdout: identify } = await execAsync(`magick identify -format "%wx%h" "${inputPath}"`);
  const [width, height] = identify.trim().split('x').map(Number);

  const currentRatio = width / height;
  const targetRatio = 2.35;

  console.log(`Current: ${width}x${height} (${currentRatio.toFixed(2)}:1)`);
  console.log(`Target: 2.35:1`);

  let cropGeometry;

  if (currentRatio > targetRatio) {
    // Image is wider, crop sides
    const cropWidth = Math.round(height * targetRatio);
    cropGeometry = `${cropWidth}x${height}+${Math.round((width - cropWidth) / 2)}+0`;
  } else {
    // Image is taller, crop top/bottom
    const cropHeight = Math.round(width / targetRatio);
    cropGeometry = `${width}x${cropHeight}+0+${Math.round((height - cropHeight) / 2)}`;
  }

  console.log(`Cropping with geometry: ${cropGeometry}`);

  await execAsync(`magick "${inputPath}" -crop ${cropGeometry} +repage "${outputPath}"`);

  console.log(`✓ Success! Saved to: ${outputPath}`);
}

cropToWechat();
