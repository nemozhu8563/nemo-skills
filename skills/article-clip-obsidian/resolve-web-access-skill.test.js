const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const { resolveWebAccessSkill } = require('./resolve-web-access-skill');

function makeTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'resolve-web-access-'));
}

function writeSkill(root, relativeDir) {
  const skillDir = path.join(root, relativeDir);
  fs.mkdirSync(skillDir, { recursive: true });
  fs.writeFileSync(path.join(skillDir, 'SKILL.md'), '---\nname: web-access\n---\n', 'utf-8');
  return skillDir;
}

test('prefers project .agents web-access over global web-access', () => {
  const vaultRoot = makeTempDir();
  const homeDir = makeTempDir();
  const projectSkill = writeSkill(vaultRoot, '.agents/skills/web-access');
  writeSkill(homeDir, '.codex/skills/web-access');

  const result = resolveWebAccessSkill({ vaultRoot, homeDir });

  assert.equal(result.status, 'found');
  assert.equal(result.scope, 'project');
  assert.equal(result.skillDir, projectSkill);
});

test('uses legacy project .skills before global web-access', () => {
  const vaultRoot = makeTempDir();
  const homeDir = makeTempDir();
  const projectSkill = writeSkill(vaultRoot, '.skills/web-access');
  writeSkill(homeDir, '.codex/skills/web-access');

  const result = resolveWebAccessSkill({ vaultRoot, homeDir });

  assert.equal(result.status, 'found');
  assert.equal(result.scope, 'project');
  assert.equal(result.skillDir, projectSkill);
});

test('uses global web-access when project web-access is absent', () => {
  const vaultRoot = makeTempDir();
  const homeDir = makeTempDir();
  const globalSkill = writeSkill(homeDir, '.codex/skills/web-access');

  const result = resolveWebAccessSkill({ vaultRoot, homeDir });

  assert.equal(result.status, 'found');
  assert.equal(result.scope, 'global');
  assert.equal(result.skillDir, globalSkill);
});

test('falls back only when project and global web-access are absent', () => {
  const result = resolveWebAccessSkill({
    vaultRoot: makeTempDir(),
    homeDir: makeTempDir()
  });

  assert.equal(result.status, 'fallback');
  assert.equal(result.scope, 'legacy');
  assert.match(result.reason, /not found/);
});
