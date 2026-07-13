const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const skillRoot = path.resolve(__dirname, '..');
const contractFiles = [
  path.join(__dirname, 'SKILL.md'),
  path.join(skillRoot, 'llm-wiki-ingest', 'SKILL.md'),
  path.join(skillRoot, 'llm-wiki-bootstrap', 'SKILL.md'),
  path.join(skillRoot, 'llm-wiki-weekly-lint', 'SKILL.md'),
  path.join(skillRoot, 'llm-wiki-weekly-lint', 'references', '知识质量检查.md')
];

function readContract(filePath) {
  return fs.readFileSync(filePath, 'utf-8');
}

test('all absorption entrypoints preserve target-specific reverse provenance', () => {
  for (const filePath of contractFiles) {
    const contract = readContract(filePath);
    assert.match(contract, /03_Notes/);
    assert.match(contract, /`source_refs`/);
    assert.match(contract, /`source_ref`/);
    assert.match(contract, /AI_Media|expression.asset|表达资产/i);
    assert.match(contract, /cannot replace|不能替代/i);
  }
});

test('all absorption entrypoints preserve existing derived refs', () => {
  for (const filePath of contractFiles) {
    const contract = readContract(filePath);
    assert.match(contract, /`derived_refs`/);
    assert.match(contract, /merge|preserv|合并|保留/i);
  }
});

test('governance artifacts cannot be used as absorbed-state proof', () => {
  for (const filePath of contractFiles) {
    const contract = readContract(filePath);
    assert.match(contract, /\.llm-wiki/);
    assert.match(contract, /registry|policy|lifecycle|topology|治理/i);
    assert.match(contract, /never derive or sync|never.*sync.*absorbed|绝不.*同步|绝不能.*同步/is);
  }
});

test('asset reference keeps per-entry source provenance contract', () => {
  const assetReference = readContract(
    path.join(skillRoot, 'llm-wiki-ingest', 'references', 'ai-media-expression-assets.md')
  );

  assert.match(assetReference, /per-entry|Entry Shape|Entry/);
  assert.match(assetReference, /source_ref/);
  assert.match(assetReference, /source_url/);
  assert.match(assetReference, /source_path/);
  assert.match(assetReference, /local source note/);
  assert.match(assetReference, /cannot replace/i);
  assert.doesNotMatch(assetReference, /source_ref` or source URL\/path/i);
});

test('all absorption entrypoints distinguish source capture from LLM Wiki-only intake fields', () => {
  for (const filePath of contractFiles) {
    const contract = readContract(filePath);
    assert.match(contract, /type: source/);
    assert.match(contract, /status: active/);
    assert.match(contract, /title/);
    assert.match(contract, /source/);
    assert.match(contract, /llm_status: new/);
    assert.match(contract, /blank|空白/i);
    assert.match(contract, /only `llm_status`|只有 `llm_status`/i);
  }
});
