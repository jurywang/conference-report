#!/usr/bin/env python3
"""extract_frames.py — Sample candidate frames for one feature via ffmpeg.

Usage:
    extract_frames.py <workdir> <feature_id> [--fps 2] [--max 40]

Input:
    <workdir>/video.mp4
    <workdir>/features_candidates.json  (or features_selected.json)

Output:
    <workdir>/frames/<feature_id>/f_000.png ... f_NNN.png   (1920-wide PNG)

Algorithm:
    - Read the feature's ``start_ts`` / ``end_ts``.
    - Run:
        ffmpeg -ss <start> -to <end> -i video.mp4 \
               -vf "fps=<fps>,scale=1920:-2" frames/<id>/f_%03d.png
    - Cap to ``--max`` frames. ``fps=2`` over 20s → 40 frames, which is the
      sweet spot for the pick_best_frame.py sprite-sheet prompt.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def find_feature(workdir: Path, feature_id: str) -> dict:
    for name in ("features_selected.json", "features_candidates.json"):
        p = workdir / name
        if p.exists():
            for feat in json.loads(p.read_text()):
                if feat["id"] == feature_id:
                    return feat
    raise SystemExit(f"Feature '{feature_id}' not found in {workdir}.")


def extract(workdir: Path, feature_id: str, fps: float, max_frames: int) -> Path:
    feat = find_feature(workdir, feature_id)
    start = float(feat["start_ts"])
    end = float(feat["end_ts"])
    duration = max(0.5, end - start)
    out_dir = workdir / "frames" / feature_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Cap: duration * fps ≤ max_frames
    if duration * fps > max_frames:
        fps = max_frames / duration

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{start:.3f}", "-to", f"{end:.3f}",
        "-i", str(workdir / "video.mp4"),
        "-vf", f"fps={fps:.4f},scale=1920:-2",
        str(out_dir / "f_%03d.png"),
    ]
    subprocess.run(cmd, check=True)
    n = len(list(out_dir.glob("f_*.png")))
    # Truncate if ffmpeg emitted more than max (edge case when fps rounding).
    extras = sorted(out_dir.glob("f_*.png"))[max_frames:]
    for e in extras:
        e.unlink()
    return out_dir


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir", type=Path)
    ap.add_argument("feature_id")
    ap.add_argument("--fps", type=float, default=2.0)
    ap.add_argument("--max", dest="max_frames", type=int, default=40)
    args = ap.parse_args(argv[1:])
    out = extract(args.workdir, args.feature_id, args.fps, args.max_frames)
    print(f"==> Extracted {len(list(out.glob('f_*.png')))} frames to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
