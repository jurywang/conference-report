#!/usr/bin/env python3
"""make_gif.py — Make a short, compact UX GIF around the best frame.

Usage:
    make_gif.py <workdir> <feature_id> [--seconds 4] [--width 640] [--fps 12]

Picks the timestamp of best_0.png (by mapping back from frame index to the
feature's [start_ts, end_ts]) and runs:

    ffmpeg -ss <start> -t <seconds> -i video.mp4 \
           -vf "fps=<fps>,scale=<width>:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" \
           -loop 0 gifs/<feature_id>.gif

Falls back to the midpoint of the feature span if best.json is missing.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def best_timestamp(workdir: Path, feature_id: str) -> float:
    for name in ("features_selected.json", "features_candidates.json"):
        p = workdir / name
        if p.exists():
            for feat in json.loads(p.read_text()):
                if feat["id"] == feature_id:
                    start = float(feat["start_ts"])
                    end = float(feat["end_ts"])
                    break
            else:
                continue
            break
    else:
        raise SystemExit(f"Feature '{feature_id}' not found.")

    best_json = workdir / "frames" / feature_id / "best.json"
    if best_json.exists():
        data = json.loads(best_json.read_text())
        selected = data.get("selected") or []
        if selected:
            frames = sorted((workdir / "frames" / feature_id).glob("f_*.png"))
            idx = selected[0]
            fps_used = len(frames) / max(0.5, end - start)
            return start + idx / fps_used
    # Fallback: midpoint
    return (start + end) / 2


def make_gif(workdir: Path, feature_id: str, seconds: float, width: int, fps: int) -> Path:
    ts = best_timestamp(workdir, feature_id)
    out_dir = workdir / "gifs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{feature_id}.gif"

    vf = (
        f"fps={fps},scale={width}:-1:flags=lanczos,"
        "split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer"
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{ts:.3f}", "-t", f"{seconds}",
        "-i", str(workdir / "video.mp4"),
        "-vf", vf,
        "-loop", "0",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir", type=Path)
    ap.add_argument("feature_id")
    ap.add_argument("--seconds", type=float, default=4.0)
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--fps", type=int, default=12)
    args = ap.parse_args(argv[1:])
    out = make_gif(args.workdir, args.feature_id, args.seconds, args.width, args.fps)
    print(f"==> GIF: {out} ({out.stat().st_size//1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
