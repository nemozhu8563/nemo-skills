#!/usr/bin/env node

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

function hasSkill(skillDir) {
  return fs.existsSync(path.join(skillDir, 'SKILL.md'));
}

function resolveWebAccessSkill(options = {}) {
  const vaultRoot = path.resolve(options.vaultRoot || process.cwd());
  const homeDir = path.resolve(options.homeDir || os.homedir());

  const projectCandidates = [
    path.join(vaultRoot, '.agents', 'skills', 'web-access'),
    path.join(vaultRoot, '.skills', 'web-access')
  ];

  for (const skillDir of projectCandidates) {
    if (hasSkill(skillDir)) {
      return {
        status: 'found',
        scope: 'project',
        skillDir,
        skillFile: path.join(skillDir, 'SKILL.md')
      };
    }
  }

  const globalSkillDir = path.join(homeDir, '.codex', 'skills', 'web-access');
  if (hasSkill(globalSkillDir)) {
    return {
      status: 'found',
      scope: 'global',
      skillDir: globalSkillDir,
      skillFile: path.join(globalSkillDir, 'SKILL.md')
    };
  }

  return {
    status: 'fallback',
    scope: 'legacy',
    skillDir: null,
    skillFile: null,
    reason: 'web-access skill not found in project or global locations'
  };
}

function main(argv = process.argv.slice(2)) {
  const vaultRoot = argv[0] || process.cwd();
  const result = resolveWebAccessSkill({ vaultRoot });
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

if (require.main === module) {
  main();
}

module.exports = {
  resolveWebAccessSkill
};
