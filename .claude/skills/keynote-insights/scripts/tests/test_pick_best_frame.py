"""Regression tests for pick_best_frame.py.

Covers the two pure-Python pieces (no LLM involved):
  - build_sprite: packs N candidate frames into a 4-col sprite sheet with
    numbered overlays. Verified by checking the output image dimensions
    match 4 * tile_width by ceil(N/4) * tile_height and that the file
    exists on disk.
  - apply_selection: copies frames[idx] into best_<rank>.png based on a
    manually-constructed best.json.

Run:  python3 -m pytest .claude/skills/keynote-insights/scripts/tests/ -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from PIL import Image

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
sys.path.insert(0, str(SCRIPTS))

from pick_best_frame import (  # noqa: E402
    SPRITE_COLS,
    TILE_WIDTH,
    apply_selection,
    build_sprite,
)


def _make_frame(dst: Path, w: int = 1920, h: int = 1080, color=(128, 32, 32)) -> None:
    """Write a solid-color PNG at dst (used as a stand-in for ffmpeg output)."""
    Image.new("RGB", (w, h), color).save(dst)


def _populate(frame_dir: Path, n: int) -> list[Path]:
    frame_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(n):
        p = frame_dir / f"f_{i:03d}.png"
        # Vary the color a little so the sprite isn't a single solid color.
        _make_frame(p, color=(100 + i * 5 % 155, 50, 50))
        paths.append(p)
    return paths


# ----------------------------- build_sprite --------------------------------

def test_build_sprite_writes_sprite_png(tmp_path):
    frame_dir = tmp_path / "frames" / "demo"
    _populate(frame_dir, 8)
    out = build_sprite(frame_dir)
    assert out == frame_dir / "_sprite.png"
    assert out.exists()


def test_build_sprite_dimensions_match_grid(tmp_path):
    frame_dir = tmp_path / "frames" / "demo"
    _populate(frame_dir, 8)  # exactly 2 rows of 4
    out = build_sprite(frame_dir)
    img = Image.open(out)
    assert img.width == TILE_WIDTH * SPRITE_COLS
    # Source is 1920x1080 → tile_h = 480 * 1080/1920 = 270
    tile_h = int(TILE_WIDTH * 1080 / 1920)
    assert img.height == tile_h * 2


def test_build_sprite_rows_ceil_div_cols(tmp_path):
    # 5 frames over 4 cols → 2 rows (last row partial).
    frame_dir = tmp_path / "frames" / "demo"
    _populate(frame_dir, 5)
    out = build_sprite(frame_dir)
    img = Image.open(out)
    tile_h = int(TILE_WIDTH * 1080 / 1920)
    assert img.height == tile_h * 2


def test_build_sprite_raises_on_empty_dir(tmp_path):
    empty_dir = tmp_path / "frames" / "empty"
    empty_dir.mkdir(parents=True)
    with pytest.raises(SystemExit):
        build_sprite(empty_dir)


# ---------------------------- apply_selection ------------------------------

def test_apply_selection_copies_frames_to_best(tmp_path):
    frame_dir = tmp_path / "frames" / "demo"
    _populate(frame_dir, 10)
    (frame_dir / "best.json").write_text(
        json.dumps({"selected": [3, 7], "rationale": "clearest UI"})
    )
    out = apply_selection(frame_dir)
    assert [p.name for p in out] == ["best_0.png", "best_1.png"]
    # best_0 must be bit-identical to f_003.png.
    assert (frame_dir / "best_0.png").read_bytes() == (frame_dir / "f_003.png").read_bytes()
    assert (frame_dir / "best_1.png").read_bytes() == (frame_dir / "f_007.png").read_bytes()


def test_apply_selection_handles_empty_selection(tmp_path):
    frame_dir = tmp_path / "frames" / "demo"
    _populate(frame_dir, 3)
    (frame_dir / "best.json").write_text(json.dumps({"selected": []}))
    out = apply_selection(frame_dir)
    assert out == []
    assert not (frame_dir / "best_0.png").exists()


def test_apply_selection_raises_on_missing_best_json(tmp_path):
    frame_dir = tmp_path / "frames" / "demo"
    _populate(frame_dir, 3)
    # no best.json written
    with pytest.raises(FileNotFoundError):
        apply_selection(frame_dir)
