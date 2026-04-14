#!/usr/bin/env python3
"""vtt_to_transcript.py — Convert a WebVTT subtitle file to our transcript.json shape.

Used as a fallback when Apple's page doesn't embed the transcript (the common case)
and we've downloaded the YouTube auto-captions via ``fetch_video.sh`` instead.

Output shape matches fetch_apple_transcript.py so downstream scripts
(segment_features.py, etc.) don't need to special-case it:

    [{"start": 12.34, "end": 18.90, "text": "..."}, ...]

Usage:
    vtt_to_transcript.py <input.vtt> <output.json>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# HH:MM:SS.mmm --> HH:MM:SS.mmm (HH is optional)
_CUE_RE = re.compile(
    r"^(?:(\d{1,2}):)?(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*"
    r"(?:(\d{1,2}):)?(\d{2}):(\d{2})[.,](\d{3})"
)
# Strip inline <c>, <00:00:01.000> tags and &amp; entities that YouTube puts in.
_TAG_RE = re.compile(r"<[^>]+>")


def _ts(h: str | None, m: str, s: str, ms: str) -> float:
    return (int(h or 0) * 3600) + (int(m) * 60) + int(s) + (int(ms) / 1000.0)


def parse_vtt(text: str) -> list[dict]:
    cues: list[dict] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = _CUE_RE.match(lines[i].strip())
        if not m:
            i += 1
            continue
        start = _ts(m.group(1), m.group(2), m.group(3), m.group(4))
        end = _ts(m.group(5), m.group(6), m.group(7), m.group(8))
        i += 1
        payload: list[str] = []
        while i < len(lines) and lines[i].strip():
            payload.append(_TAG_RE.sub("", lines[i]).strip())
            i += 1
        text_joined = " ".join(p for p in payload if p).strip()
        if text_joined:
            cues.append({"start": start, "end": end, "text": text_joined})
    # De-dup consecutive cues with identical text (YouTube rolling captions).
    deduped: list[dict] = []
    for c in cues:
        if deduped and deduped[-1]["text"] == c["text"]:
            deduped[-1]["end"] = c["end"]
            continue
        deduped.append(c)
    return deduped


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(f"Usage: {argv[0]} <input.vtt> <output.json>", file=sys.stderr)
        return 2
    src = Path(argv[1])
    dst = Path(argv[2])
    if not src.exists():
        print(f"missing {src}", file=sys.stderr)
        return 2
    cues = parse_vtt(src.read_text(encoding="utf-8"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(cues, ensure_ascii=False, indent=2))
    print(f"==> Wrote {dst} ({len(cues)} cues)")
    return 0 if cues else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
