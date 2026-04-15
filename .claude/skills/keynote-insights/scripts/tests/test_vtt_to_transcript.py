"""Regression tests for vtt_to_transcript.py.

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

from vtt_to_transcript import main as vtt_main, parse_vtt  # noqa: E402


# ------------------------------- parse_vtt ---------------------------------

def test_parse_vtt_basic_three_cues():
    vtt = (
        "WEBVTT\n\n"
        "00:00:01.000 --> 00:00:03.500\nHello, world.\n\n"
        "00:00:04.000 --> 00:00:06.000\nSecond cue.\n\n"
        "00:00:07.250 --> 00:00:09.000\nThird cue.\n"
    )
    cues = parse_vtt(vtt)
    assert len(cues) == 3
    assert cues[0] == {"start": 1.0, "end": 3.5, "text": "Hello, world."}
    assert cues[2]["start"] == 7.25


def test_parse_vtt_supports_hour_component():
    vtt = "WEBVTT\n\n01:02:03.000 --> 01:02:05.000\nLater in the video.\n"
    cues = parse_vtt(vtt)
    assert len(cues) == 1
    assert cues[0]["start"] == pytest.approx(3723.0)
    assert cues[0]["end"] == pytest.approx(3725.0)


def test_parse_vtt_strips_inline_tags():
    # YouTube auto-captions frequently inject <c> and timestamp tags.
    # The tags themselves go, but the wrapped words stay.
    vtt = (
        "WEBVTT\n\n"
        "00:00:00.000 --> 00:00:02.000\n"
        "Hello <00:00:00.500><c>from</c> Apple.\n"
    )
    cues = parse_vtt(vtt)
    assert cues[0]["text"] == "Hello from Apple."


def test_parse_vtt_joins_multiline_payload():
    vtt = (
        "WEBVTT\n\n"
        "00:00:05.000 --> 00:00:10.000\n"
        "First line.\nSecond line.\nThird line.\n"
    )
    cues = parse_vtt(vtt)
    assert len(cues) == 1
    assert cues[0]["text"] == "First line. Second line. Third line."


def test_parse_vtt_dedups_rolling_captions():
    # YouTube sometimes emits the same phrase across two consecutive cues.
    vtt = (
        "WEBVTT\n\n"
        "00:00:00.000 --> 00:00:02.000\nHello world.\n\n"
        "00:00:02.000 --> 00:00:04.000\nHello world.\n\n"
        "00:00:04.000 --> 00:00:06.000\nSecond phrase.\n"
    )
    cues = parse_vtt(vtt)
    assert len(cues) == 2
    # First cue should span the merged window.
    assert cues[0]["start"] == 0.0
    assert cues[0]["end"] == 4.0
    assert cues[1]["text"] == "Second phrase."


def test_parse_vtt_ignores_notes_and_empty_payload():
    vtt = (
        "WEBVTT\n\n"
        "NOTE This is a comment block\nmultiline\n\n"
        "00:00:01.000 --> 00:00:02.000\n\n"  # empty payload, dropped
        "00:00:03.000 --> 00:00:04.000\nReal cue.\n"
    )
    cues = parse_vtt(vtt)
    assert len(cues) == 1
    assert cues[0]["text"] == "Real cue."


def test_parse_vtt_accepts_comma_millisecond_separator():
    # Some SRT-to-VTT conversions leave the comma separator.
    vtt = "WEBVTT\n\n00:00:01,000 --> 00:00:02,500\nSRT-style.\n"
    cues = parse_vtt(vtt)
    assert cues == [{"start": 1.0, "end": 2.5, "text": "SRT-style."}]


def test_parse_vtt_empty_input_returns_empty():
    assert parse_vtt("") == []
    assert parse_vtt("WEBVTT\n") == []


# --------------------------------- main ------------------------------------

def test_main_writes_json_and_returns_zero(tmp_path):
    src = tmp_path / "in.vtt"
    dst = tmp_path / "out.json"
    src.write_text(
        "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHi.\n",
        encoding="utf-8",
    )
    rc = vtt_main(["vtt_to_transcript.py", str(src), str(dst)])
    assert rc == 0
    data = json.loads(dst.read_text())
    assert data[0]["text"] == "Hi."


def test_main_returns_one_for_empty_vtt(tmp_path):
    src = tmp_path / "empty.vtt"
    dst = tmp_path / "out.json"
    src.write_text("WEBVTT\n", encoding="utf-8")
    rc = vtt_main(["vtt_to_transcript.py", str(src), str(dst)])
    assert rc == 1
    assert json.loads(dst.read_text()) == []


def test_main_returns_two_on_missing_input(tmp_path):
    rc = vtt_main(["vtt_to_transcript.py", str(tmp_path / "no.vtt"), str(tmp_path / "o.json")])
    assert rc == 2


def test_main_bad_args_returns_two(tmp_path):
    rc = vtt_main(["vtt_to_transcript.py", str(tmp_path / "only-one-arg.vtt")])
    assert rc == 2
