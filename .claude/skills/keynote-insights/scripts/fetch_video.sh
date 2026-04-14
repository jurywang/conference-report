#!/usr/bin/env bash
# fetch_video.sh — Download a keynote video, subtitles, and chapters via yt-dlp.
#
# Usage:
#   fetch_video.sh <youtube_url_or_apple_url> <workdir>
#
# Outputs in <workdir>:
#   video.mp4              — best <=1080p mp4 merged
#   subtitles.en.vtt       — English subtitles (auto or manual)
#   chapters.json          — YouTube chapter markers (if available)
#   info.json              — full yt-dlp metadata
#
# Note: Apple's developer.apple.com URLs also play HLS via yt-dlp.

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <video_url> <workdir>" >&2
  exit 2
fi

URL="$1"
WORKDIR="$2"
mkdir -p "${WORKDIR}"

if ! command -v yt-dlp >/dev/null 2>&1; then
  echo "ERROR: yt-dlp is not installed. See install.sh for hints." >&2
  exit 3
fi

echo "==> Downloading video to ${WORKDIR}"

# --write-info-json produces <id>.info.json with chapters embedded.
# --write-auto-subs + --sub-langs en.* pulls English auto-captions.
# --convert-subs vtt normalizes format.
yt-dlp \
  --no-progress \
  --no-playlist \
  --format 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]' \
  --merge-output-format mp4 \
  --output "${WORKDIR}/video.%(ext)s" \
  --write-info-json \
  --write-auto-subs \
  --write-subs \
  --sub-langs 'en.*,en' \
  --convert-subs vtt \
  "${URL}"

# Normalize filenames: yt-dlp may produce video.info.json / video.en.vtt etc.
if [[ -f "${WORKDIR}/video.info.json" ]]; then
  python3 -c "
import json, pathlib, sys
p = pathlib.Path('${WORKDIR}/video.info.json')
info = json.loads(p.read_text())
chapters = info.get('chapters') or []
pathlib.Path('${WORKDIR}/chapters.json').write_text(
    json.dumps(chapters, ensure_ascii=False, indent=2)
)
pathlib.Path('${WORKDIR}/info.json').write_text(
    json.dumps({
        'id': info.get('id'),
        'title': info.get('title'),
        'duration': info.get('duration'),
        'uploader': info.get('uploader'),
        'upload_date': info.get('upload_date'),
        'webpage_url': info.get('webpage_url'),
    }, ensure_ascii=False, indent=2)
)
print(f'==> Saved chapters.json ({len(chapters)} markers) and info.json')
"
fi

# Pick the first English VTT and symlink to a stable name.
SUB=$(ls "${WORKDIR}"/video.en*.vtt 2>/dev/null | head -n1 || true)
if [[ -n "${SUB}" ]]; then
  ln -sf "$(basename "${SUB}")" "${WORKDIR}/subtitles.en.vtt"
  echo "==> Subtitles linked: ${WORKDIR}/subtitles.en.vtt -> $(basename "${SUB}")"
else
  echo "WARN: no English subtitles found. fetch_apple_transcript.py is your next bet." >&2
fi

echo "==> Done."
