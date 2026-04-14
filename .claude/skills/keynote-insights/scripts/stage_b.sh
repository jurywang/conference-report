#!/usr/bin/env bash
# stage_b.sh — Run the video-dependent half of the pipeline for a feature.
#
# Must be invoked in an environment where video.mp4 is already on disk
# (e.g. after `fetch_video.sh <url> <workdir>` succeeded) because extract_frames
# and make_gif both call ffmpeg against workdir/video.mp4.
#
# Usage:
#   stage_b.sh <workdir> <feature_id> [--fps 2] [--max-frames 40] [--gif-seconds 4]
#
# Produces:
#   <workdir>/frames/<feature_id>/f_*.png
#   <workdir>/frames/<feature_id>/_sprite.png
#   (claude writes <workdir>/frames/<feature_id>/best.json after reviewing _sprite)
#   <workdir>/frames/<feature_id>/best_0.png, best_1.png, ...
#   <workdir>/gifs/<feature_id>.gif

set -euo pipefail

if [[ $# -lt 2 ]]; then
  cat <<'USAGE' >&2
Usage: stage_b.sh <workdir> <feature_id> [--fps 2] [--max-frames 40] [--gif-seconds 4]

Example:
  stage_b.sh workspace/wwdc2025 live-translation --fps 2 --max-frames 40

Prereq: workdir/video.mp4 must exist. If sandbox/network blocks video
downloads, run fetch_video.sh on a machine with network access first.
USAGE
  exit 2
fi

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKDIR="$1"
FEATURE="$2"
shift 2

FPS=2
MAX_FRAMES=40
GIF_SEC=4
while [[ $# -gt 0 ]]; do
  case "$1" in
    --fps) FPS="$2"; shift 2 ;;
    --max-frames) MAX_FRAMES="$2"; shift 2 ;;
    --gif-seconds) GIF_SEC="$2"; shift 2 ;;
    *) echo "Unknown flag: $1" >&2; exit 2 ;;
  esac
done

if [[ ! -f "$WORKDIR/video.mp4" ]]; then
  echo "ERROR: $WORKDIR/video.mp4 missing. Run fetch_video.sh first." >&2
  exit 3
fi

echo "==> [1/4] Extracting candidate frames (fps=$FPS, max=$MAX_FRAMES)"
python3 "$SKILL_DIR/scripts/extract_frames.py" \
  "$WORKDIR" "$FEATURE" --fps "$FPS" --max "$MAX_FRAMES"

echo "==> [2/4] Building sprite sheet for Claude vision review"
python3 "$SKILL_DIR/scripts/pick_best_frame.py" build-sprite \
  "$WORKDIR" "$FEATURE"

cat <<EOF

[HUMAN/CLAUDE STEP]
Open $WORKDIR/frames/$FEATURE/_sprite.png and pick 1-3 tile indices that
best show the feature's UI. Write the JSON below to
$WORKDIR/frames/$FEATURE/best.json, then re-run this script from step 3:

    { "selected": [7, 12], "rationale": "…" }

Then rerun: bash $0 $WORKDIR $FEATURE --skip-to-apply
(or just run 'pick_best_frame.py apply' and 'make_gif.py' yourself)
EOF

if [[ ! -f "$WORKDIR/frames/$FEATURE/best.json" ]]; then
  echo
  echo "==> Paused at sprite review. Re-run after writing best.json."
  exit 0
fi

echo "==> [3/4] Applying best-frame selection"
python3 "$SKILL_DIR/scripts/pick_best_frame.py" apply \
  "$WORKDIR" "$FEATURE"

echo "==> [4/4] Building GIF (${GIF_SEC}s)"
python3 "$SKILL_DIR/scripts/make_gif.py" \
  "$WORKDIR" "$FEATURE" --seconds "$GIF_SEC"

echo
echo "Stage B complete for '$FEATURE'. Next:"
echo "  1. Run analyst_roundup.py plan + Claude WebSearch → commentary/$FEATURE.md"
echo "  2. Claude appends $FEATURE to slides.json (thesis_zh + impact_bullets + quotes)"
echo "  3. python3 scripts/build_ppt.py $WORKDIR → final .pptx"
