#!/usr/bin/env python3
"""pick_best_frame.py — Ask Claude vision which candidate frame best shows UX.

Usage:
    pick_best_frame.py <workdir> <feature_id>

This script is meant to be **called by Claude via the skill**, not run in CI:
the LLM-as-judge step needs an LLM. The script itself:

    1. Builds a sprite-sheet (4 cols × N rows) of all candidate frames with
       Pillow, annotating each tile with its index (0, 1, 2, …).
    2. Writes the sprite sheet to ``frames/<id>/_sprite.png``.
    3. Emits a prompt template to stdout that Claude should paste into its
       reasoning, along with the sprite sheet image.
    4. Once Claude decides the winning indices, it writes
       ``frames/<id>/best.json`` with:
           { "selected": [7, 12], "rationale": "…" }
       and this script's ``apply`` subcommand copies those to
       ``frames/<id>/best_0.png`` etc.

Running `pick_best_frame.py build-sprite` does step 1-3.
Running `pick_best_frame.py apply` does step 4 after Claude updates best.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SPRITE_COLS = 4
TILE_WIDTH = 480   # per-tile width in sprite (original PNG is 1920)


def build_sprite(frame_dir: Path) -> Path:
    frames = sorted(frame_dir.glob("f_*.png"))
    if not frames:
        raise SystemExit(f"No frames in {frame_dir}")

    rows = (len(frames) + SPRITE_COLS - 1) // SPRITE_COLS
    sample = Image.open(frames[0])
    ar = sample.height / sample.width
    tile_h = int(TILE_WIDTH * ar)

    sheet = Image.new("RGB", (TILE_WIDTH * SPRITE_COLS, tile_h * rows), "white")
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
    except OSError:
        font = ImageFont.load_default()

    for i, fp in enumerate(frames):
        img = Image.open(fp).resize((TILE_WIDTH, tile_h))
        r, c = divmod(i, SPRITE_COLS)
        sheet.paste(img, (c * TILE_WIDTH, r * tile_h))
        draw = ImageDraw.Draw(sheet)
        # Big index in top-left of each tile, with a dark box behind for legibility.
        label = f"{i}"
        x0, y0 = c * TILE_WIDTH + 8, r * tile_h + 8
        draw.rectangle([x0, y0, x0 + 56, y0 + 48], fill="black")
        draw.text((x0 + 10, y0 + 4), label, fill="yellow", font=font)

    out = frame_dir / "_sprite.png"
    sheet.save(out, optimize=True)
    return out


def apply_selection(frame_dir: Path) -> list[Path]:
    best = json.loads((frame_dir / "best.json").read_text())
    selected = best.get("selected", [])
    frames = sorted(frame_dir.glob("f_*.png"))
    out_paths = []
    for rank, idx in enumerate(selected):
        src = frames[idx]
        dst = frame_dir / f"best_{rank}.png"
        dst.write_bytes(src.read_bytes())
        out_paths.append(dst)
    return out_paths


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp1 = sub.add_parser("build-sprite", help="Build sprite sheet for LLM review")
    sp1.add_argument("workdir", type=Path)
    sp1.add_argument("feature_id")

    sp2 = sub.add_parser("apply", help="Copy LLM-selected frames to best_N.png")
    sp2.add_argument("workdir", type=Path)
    sp2.add_argument("feature_id")

    args = ap.parse_args(argv[1:])
    frame_dir = args.workdir / "frames" / args.feature_id

    if args.cmd == "build-sprite":
        out = build_sprite(frame_dir)
        print(f"==> Sprite: {out}")
        print("Now ask Claude (with this image attached):")
        print(
            "    'Among these numbered candidate frames of the {feature} demo, "
            "pick 1-3 that most clearly show the key UI elements. "
            "Write frames/{id}/best.json as {\"selected\":[...],\"rationale\":...}'"
            .format(feature=args.feature_id, id=args.feature_id)
        )
    elif args.cmd == "apply":
        paths = apply_selection(frame_dir)
        print(f"==> Copied {len(paths)} best frames: {[p.name for p in paths]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
