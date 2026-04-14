#!/usr/bin/env bash
# stage_a.sh — One-shot Stage A: fetch page → parse chapters/transcript → segment.
#
# Usage:
#   stage_a.sh <apple_session_url_or_html_path> <workdir> [--with-video <yt_url>]
#
# Modes:
#   default  — Apple page only (chapters + transcript if embedded).
#              Fastest; suitable when you only need the candidate list.
#   --with-video <yt_url>
#            — also runs fetch_video.sh to pull the MP4 + VTT + chapters via
#              yt-dlp; useful when the Apple page doesn't embed transcript
#              (which is the common case) and you need subtitles + video.

set -euo pipefail

if [[ $# -lt 2 ]]; then
  cat <<'USAGE' >&2
Usage: stage_a.sh <apple_session_url_or_html_path> <workdir> [--with-video <yt_url>]

Example:
  # Metadata only (no video download)
  stage_a.sh https://developer.apple.com/videos/play/wwdc2025/101/ \
             workspace/wwdc2025

  # Also download the MP4 + subtitles via YouTube
  stage_a.sh https://developer.apple.com/videos/play/wwdc2025/101/ \
             workspace/wwdc2025 \
             --with-video "https://www.youtube.com/watch?v=<id>"
USAGE
  exit 2
fi

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$1"
WORKDIR="$2"
shift 2
VIDEO_URL=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-video) VIDEO_URL="$2"; shift 2 ;;
    *) echo "Unknown flag: $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$WORKDIR"

echo "==> [1/3] Parsing Apple session page: $SOURCE"
set +e
python3 "$SKILL_DIR/scripts/fetch_apple_transcript.py" "$SOURCE" "$WORKDIR"
APPLE_RC=$?
set -e
case $APPLE_RC in
  0) echo "    transcript.json + chapters.json written" ;;
  1) echo "    chapters.json written; transcript NOT embedded (will rely on VTT if --with-video)" ;;
  *) echo "    FAILED to parse Apple page (rc=$APPLE_RC)"; exit $APPLE_RC ;;
esac

if [[ -n "$VIDEO_URL" ]]; then
  echo "==> [2/3] Downloading video + subs: $VIDEO_URL"
  bash "$SKILL_DIR/scripts/fetch_video.sh" "$VIDEO_URL" "$WORKDIR"

  # If transcript wasn't embedded on Apple page, promote the VTT into transcript.json.
  if [[ ! -f "$WORKDIR/transcript.json" && -f "$WORKDIR/subtitles.en.vtt" ]]; then
    echo "    Converting VTT → transcript.json"
    python3 "$SKILL_DIR/scripts/vtt_to_transcript.py" \
      "$WORKDIR/subtitles.en.vtt" "$WORKDIR/transcript.json"
  fi
else
  echo "==> [2/3] Skipping video download (--with-video not set)"
fi

echo "==> [3/3] Building features_candidates.json"
python3 "$SKILL_DIR/scripts/segment_features.py" "$WORKDIR"

echo
echo "Stage A complete. Review $WORKDIR/features_candidates.json,"
echo "edit to pick the subset you want, save as features_selected.json,"
echo "then proceed to Stage B (extract_frames + pick_best_frame + analyst_roundup + build_ppt)."
