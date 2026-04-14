#!/usr/bin/env python3
"""fetch_apple_transcript.py — Parse an Apple developer session page.

Emits two JSON artifacts:
    <workdir>/chapters.json       — always, from <li class="chapter-item">
    <workdir>/transcript.json     — only if the page contains <span data-start>
                                    sentence spans; otherwise this file is
                                    skipped and the exit code signals
                                    "transcript unavailable; use VTT fallback".

Exit codes:
    0  — both chapters.json and transcript.json written
    1  — chapters.json written, transcript NOT available on the page
         (common when the page renders transcript via client-side JS; caller
          should fall back to yt-dlp VTT / Whisper)
    2  — page could not be parsed at all (missing chapter markers)

Usage:
    fetch_apple_transcript.py <apple_session_url_or_html_path> <workdir>

Passing a local .html path lets tests run without network.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup


UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15"
)


def _load_html(source: str) -> str:
    p = Path(source)
    if p.exists():
        return p.read_text(encoding="utf-8")
    resp = requests.get(source, headers={"User-Agent": UA}, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_chapters(html: str) -> list[dict]:
    """Extract chapters from <li class="chapter-item" data-start-time="..."> markers.

    Each Apple session page renders chapters as:

        <li class="chapter-item" data-start-time="228">
            0:03:48 - <a ... data-start-time="228"
                           data-chapter-end-time="2495"
                           data-chapter-lenght="2267"
                           data-chapter-index="2">iOS</a>
        </li>
    """
    soup = BeautifulSoup(html, "lxml")
    out: list[dict] = []
    for li in soup.select("li.chapter-item"):
        anchor = li.find("a", attrs={"data-chapter-index": True})
        if not anchor:
            continue
        try:
            out.append({
                "index": int(anchor["data-chapter-index"]),
                "title": anchor.get_text(strip=True),
                "start_ts": float(anchor["data-start-time"]),
                "end_ts": float(anchor["data-chapter-end-time"]),
            })
        except (KeyError, ValueError):
            continue
    out.sort(key=lambda c: c["index"])
    return out


_SENTENCE_SELECTORS = [
    # Primary: post-JS transform wraps each sentence in <a class="sentence" data-start-time>
    "a.sentence[data-start-time]",
    # Pre-JS markup that play.js transforms at load: <span data-start=...>text</span>
    # We grab the parent text so sentence boundaries are preserved.
    "span[data-start]",
]


def parse_transcript(html: str) -> list[dict]:
    """Return sentence-level transcript cues if the page contains them.

    Output items: {"start": float_seconds, "end": float_seconds | None, "text": str}

    The end timestamp is derived from the next cue's start (or None for the
    last cue). Apple's markup only tags starts.
    """
    soup = BeautifulSoup(html, "lxml")
    cues: list[dict] = []
    for selector in _SENTENCE_SELECTORS:
        els = soup.select(selector)
        if not els:
            continue
        for el in els:
            start_attr = el.get("data-start-time") or el.get("data-start")
            if not start_attr:
                continue
            try:
                start = float(start_attr)
            except ValueError:
                continue
            text = el.get_text(" ", strip=True)
            if not text:
                continue
            cues.append({"start": start, "text": text})
        if cues:
            break

    cues.sort(key=lambda c: c["start"])
    for i, c in enumerate(cues):
        c["end"] = cues[i + 1]["start"] if i + 1 < len(cues) else None
    return cues


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(f"Usage: {argv[0]} <apple_session_url_or_html_path> <workdir>",
              file=sys.stderr)
        return 2
    source, workdir = argv[1], Path(argv[2])
    workdir.mkdir(parents=True, exist_ok=True)

    html = _load_html(source)
    # Stash raw HTML for debugging / regression fixtures.
    (workdir / "apple_raw.html").write_text(html, encoding="utf-8")

    chapters = parse_chapters(html)
    if not chapters:
        print(f"ERROR: no chapter-item markers in {source}", file=sys.stderr)
        return 2
    (workdir / "chapters.json").write_text(
        json.dumps(chapters, ensure_ascii=False, indent=2)
    )
    print(f"==> chapters.json: {len(chapters)} chapters "
          f"(total {int(chapters[-1]['end_ts'] - chapters[0]['start_ts'])}s)")

    cues = parse_transcript(html)
    if cues:
        (workdir / "transcript.json").write_text(
            json.dumps(cues, ensure_ascii=False, indent=2)
        )
        print(f"==> transcript.json: {len(cues)} cues")
        return 0

    # Transcript not embedded (common: loaded via browser JS on demand).
    print("WARN: transcript not embedded on page. "
          "Fall back to yt-dlp VTT or Whisper.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
