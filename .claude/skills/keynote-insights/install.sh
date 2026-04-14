#!/usr/bin/env bash
# Install / link the keynote-insights skill.
#
# 1. Checks system dependencies (ffmpeg, yt-dlp) and prints install hints.
# 2. Installs Python dependencies from requirements.txt.
# 3. Symlinks this skill dir into ~/.claude/skills/keynote-insights so it can
#    be used outside this repo as well.

set -euo pipefail

SKILL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TARGET_LINK="${HOME}/.claude/skills/keynote-insights"

echo "==> keynote-insights skill location: ${SKILL_DIR}"

# ---- 1. system deps ---------------------------------------------------------
MISSING_SYS=()
for cmd in ffmpeg yt-dlp; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    MISSING_SYS+=("$cmd")
  fi
done

if (( ${#MISSING_SYS[@]} > 0 )); then
  echo "==> Missing system tools: ${MISSING_SYS[*]}"
  echo "    macOS:   brew install ${MISSING_SYS[*]}"
  echo "    Debian:  sudo apt-get install -y ${MISSING_SYS[*]}"
  echo "    (yt-dlp can also be installed via: pipx install yt-dlp)"
fi

# ---- 2. python deps ---------------------------------------------------------
echo "==> Installing Python dependencies"
python3 -m pip install --quiet --upgrade -r "${SKILL_DIR}/requirements.txt"

# ---- 3. symlink to global skills dir ---------------------------------------
mkdir -p "${HOME}/.claude/skills"
if [[ -L "${TARGET_LINK}" || -e "${TARGET_LINK}" ]]; then
  CURRENT="$(readlink "${TARGET_LINK}" 2>/dev/null || echo "")"
  if [[ "${CURRENT}" == "${SKILL_DIR}" ]]; then
    echo "==> Symlink already points here: ${TARGET_LINK}"
  else
    echo "==> ${TARGET_LINK} already exists (target: ${CURRENT:-<file>}). Skipping."
    echo "    Remove it manually if you want to re-link:"
    echo "      rm -f ${TARGET_LINK}"
  fi
else
  ln -s "${SKILL_DIR}" "${TARGET_LINK}"
  echo "==> Linked ${TARGET_LINK} -> ${SKILL_DIR}"
fi

echo "==> Done. Use the skill by asking Claude to 'make a PPT report of WWDC <year>'."
