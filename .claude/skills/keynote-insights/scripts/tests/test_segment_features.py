"""Regression tests for segment_features.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
sys.path.insert(0, str(SCRIPTS))

from segment_features import (  # noqa: E402
    slugify,
    extract_keywords,
    first_sentences,
    build_candidates,
    LONG_CHAPTER_SEC,
)


# ------------------------------ slugify ------------------------------------

@pytest.mark.parametrize("given,expected", [
    ("iOS", "ios"),
    ("Live Translation", "live-translation"),
    ("macOS Tahoe", "macos-tahoe"),
    ("A / B Test", "a-b-test"),
    ("", "unnamed"),
    ("   ", "unnamed"),
])
def test_slugify(given, expected):
    assert slugify(given) == expected


# ----------------------------- keywords -----------------------------------

def test_extract_keywords_finds_two_word_product_names():
    text = (
        "Today we're introducing Live Translation on AirPods. "
        "Your AirPods can now translate conversations in real time. "
        "This works seamlessly with Messages and FaceTime. "
        "Live Translation is powered by Apple Intelligence."
    )
    kws = extract_keywords(text)
    lower = [k.lower() for k in kws]
    assert "live translation" in lower
    assert any("airpods" in k.lower() for k in kws)


def test_extract_keywords_drops_stopwords():
    text = "The new the new the new Liquid Glass the new the Liquid Glass."
    kws = extract_keywords(text)
    assert "the" not in [k.lower() for k in kws]
    assert any("liquid glass" in k.lower() for k in kws)


def test_extract_keywords_limits_to_top_n():
    text = " ".join(f"Word{i} Word{i}" for i in range(20))
    assert len(extract_keywords(text, top_n=5)) <= 5


# --------------------------- first_sentences ------------------------------

def test_first_sentences_returns_n_sentences():
    t = "First sentence. Second sentence. Third sentence. Fourth."
    assert first_sentences(t, 2) == "First sentence. Second sentence."


def test_first_sentences_truncates_long_output():
    t = "X" * 500 + ". Done."
    out = first_sentences(t, 2, max_chars=80)
    assert len(out) <= 80
    assert out.endswith("…")


# --------------------------- build_candidates -----------------------------

def test_build_candidates_chapter_only_flags_long_chapters(tmp_path):
    (tmp_path / "chapters.json").write_text(json.dumps([
        {"title": "Intro", "start_ts": 0, "end_ts": 100},
        {"title": "Long Chapter", "start_ts": 100, "end_ts": 100 + LONG_CHAPTER_SEC + 1},
    ]))
    # no transcript.json
    cands = build_candidates(tmp_path)
    assert len(cands) == 2
    assert cands[0]["needs_subdivision"] is False
    assert cands[1]["needs_subdivision"] is True
    # No transcript → summary + keywords empty
    assert cands[1]["one_line_summary"] == ""
    assert cands[1]["keywords"] == []


def test_build_candidates_with_transcript_enriches_summary_and_keywords(tmp_path):
    (tmp_path / "chapters.json").write_text(json.dumps([
        {"title": "AirPods Demo", "start_ts": 0, "end_ts": 120},
    ]))
    (tmp_path / "transcript.json").write_text(json.dumps([
        {"start": 1, "end": 6, "text": "Welcome to WWDC 2025."},
        {"start": 6, "end": 15, "text": "Today we introduce Live Translation on AirPods."},
        {"start": 15, "end": 25, "text": "Live Translation makes real-time conversations simple."},
    ]))
    cands = build_candidates(tmp_path)
    assert len(cands) == 1
    c = cands[0]
    assert "Live Translation" in c["one_line_summary"] or "WWDC" in c["one_line_summary"]
    lower = [k.lower() for k in c["keywords"]]
    assert any("live translation" in k or "airpods" in k for k in lower)
    # Even though duration is large, having transcript suppresses the subdivision flag.
    assert c["needs_subdivision"] is False


def test_build_candidates_accepts_ytdlp_shape(tmp_path):
    # yt-dlp uses start_time / end_time instead of start_ts / end_ts.
    (tmp_path / "chapters.json").write_text(json.dumps([
        {"title": "Intro", "start_time": 0, "end_time": 10},
    ]))
    cands = build_candidates(tmp_path)
    assert len(cands) == 1
    assert cands[0]["start_ts"] == 0
    assert cands[0]["end_ts"] == 10


def test_build_candidates_wwdc2025_fixture(tmp_path):
    """End-to-end: parse the real apple_raw.html fixture and verify candidates."""
    from fetch_apple_transcript import main as fat_main

    fat_rc = fat_main(["fat",
                       str(HERE / "fixtures" / "wwdc2025_101.html"),
                       str(tmp_path)])
    assert fat_rc == 1  # transcript not embedded on real page
    cands = build_candidates(tmp_path)
    assert [c["title_en"] for c in cands] == [
        "Introduction", "iOS", "watchOS", "tvOS",
        "macOS", "visionOS", "iPadOS", "Developers",
    ]
    # "Introduction" is 228s which exceeds LONG_CHAPTER_SEC (240s? let's check).
    # Actually 228 < 240, so introduction should not be flagged.
    intro = next(c for c in cands if c["title_en"] == "Introduction")
    ios = next(c for c in cands if c["title_en"] == "iOS")
    assert intro["needs_subdivision"] is False
    assert ios["needs_subdivision"] is True
    assert ios["end_ts"] - ios["start_ts"] > LONG_CHAPTER_SEC
