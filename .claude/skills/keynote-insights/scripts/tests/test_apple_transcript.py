"""Regression tests for fetch_apple_transcript.py.

Run:  python3 -m pytest .claude/skills/keynote-insights/scripts/tests/ -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
sys.path.insert(0, str(SCRIPTS))

from fetch_apple_transcript import (  # noqa: E402
    parse_chapters,
    parse_transcript,
    main as fat_main,
)


FIXTURES = HERE / "fixtures"
WWDC_HTML = FIXTURES / "wwdc2025_101.html"
SYNTH_HTML = FIXTURES / "synthetic_with_transcript.html"


def _html(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ----------------------------- chapters ------------------------------------

def test_parse_chapters_wwdc2025_has_eight_chapters():
    ch = parse_chapters(_html(WWDC_HTML))
    assert len(ch) == 8, f"expected 8 chapters, got {len(ch)}: {[c['title'] for c in ch]}"


def test_parse_chapters_wwdc2025_titles_in_order():
    ch = parse_chapters(_html(WWDC_HTML))
    titles = [c["title"] for c in ch]
    assert titles == [
        "Introduction", "iOS", "watchOS", "tvOS",
        "macOS", "visionOS", "iPadOS", "Developers",
    ]


def test_parse_chapters_wwdc2025_timestamps_are_monotonic():
    ch = parse_chapters(_html(WWDC_HTML))
    for a, b in zip(ch, ch[1:]):
        assert a["start_ts"] < a["end_ts"] == b["start_ts"], \
            f"non-monotonic between {a['title']} and {b['title']}"


def test_parse_chapters_wwdc2025_total_duration_matches_known_runtime():
    # Apple's WWDC 2025 keynote runs ~92:26 = 5546s.
    ch = parse_chapters(_html(WWDC_HTML))
    total = ch[-1]["end_ts"] - ch[0]["start_ts"]
    assert 5540 <= total <= 5560


def test_parse_chapters_returns_empty_on_bad_html():
    assert parse_chapters("<html><body>no chapters here</body></html>") == []


# ----------------------------- transcript ----------------------------------

def test_parse_transcript_absent_on_real_apple_page():
    # The raw WWDC 2025 page does NOT embed transcript sentences; Apple's
    # play.js builds them client-side. Our parser should return [] here.
    assert parse_transcript(_html(WWDC_HTML)) == []


def test_parse_transcript_present_on_synthetic_fixture():
    cues = parse_transcript(_html(SYNTH_HTML))
    assert len(cues) == 5
    assert cues[0]["start"] == 0.0
    assert cues[0]["text"] == "Welcome to WWDC."
    assert cues[-1]["text"] == "This works across Messages and FaceTime."


def test_parse_transcript_derives_end_timestamps_from_next_start():
    cues = parse_transcript(_html(SYNTH_HTML))
    assert cues[0]["end"] == 5.0
    assert cues[1]["end"] == 62.0
    assert cues[-1]["end"] is None


def test_parse_transcript_sorts_by_start():
    html = """
    <a class="sentence" data-start-time="50">B</a>
    <a class="sentence" data-start-time="10">A</a>
    <a class="sentence" data-start-time="30">C</a>
    """
    cues = parse_transcript(html)
    assert [c["text"] for c in cues] == ["A", "C", "B"]
    assert [c["start"] for c in cues] == [10.0, 30.0, 50.0]


# ----------------------------- main entry point ----------------------------

def test_main_exit_code_1_when_transcript_missing(tmp_path):
    rc = fat_main(["fat", str(WWDC_HTML), str(tmp_path)])
    assert rc == 1
    assert (tmp_path / "chapters.json").exists()
    assert not (tmp_path / "transcript.json").exists()
    chapters = json.loads((tmp_path / "chapters.json").read_text())
    assert len(chapters) == 8


def test_main_exit_code_0_when_transcript_available(tmp_path):
    rc = fat_main(["fat", str(SYNTH_HTML), str(tmp_path)])
    assert rc == 0
    assert (tmp_path / "chapters.json").exists()
    assert (tmp_path / "transcript.json").exists()
    cues = json.loads((tmp_path / "transcript.json").read_text())
    assert len(cues) == 5


def test_main_exit_code_2_on_unparseable_input(tmp_path):
    empty = tmp_path / "empty.html"
    empty.write_text("<html></html>")
    rc = fat_main(["fat", str(empty), str(tmp_path / "out")])
    assert rc == 2
