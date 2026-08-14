#!/usr/bin/env bash
set -euo pipefail

default_project_dir="/Users/nemo/Documents/Obsidian/04_Projects/AI出海/游戏热词雷达"
project_dir="${GAME_KEYWORD_RADAR_PROJECT_DIR:-$default_project_dir}"

if [[ ! -f "$project_dir/package.json" ]]; then
  printf 'Game keyword radar project not found: %s\n' "$project_dir" >&2
  printf 'Set GAME_KEYWORD_RADAR_PROJECT_DIR to the project directory.\n' >&2
  exit 2
fi

exec npm --prefix "$project_dir" run radar -- "$@"
