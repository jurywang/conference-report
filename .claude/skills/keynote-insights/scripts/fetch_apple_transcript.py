#!/usr/bin/env python3
"""fetch_apple_transcript.py — Scrape Apple's developer.apple.com transcript.

Apple's session pages (e.g. https://developer.apple.com/videos/play/wwdc2025/101/)
embed an official timestamped transcript as JSON inside a ``<script>`` tag.
This is the highest-quality source we have — use it before falling back to
YouTube auto-captions or Whisper.

Usage:
    fetch_apple_transcript.py <apple_session_url> <workdir>

Output:
    <workdir>/transcript.json   — list of {start: float, end: float, text: str}

Implementation plan (TODO):
    1. GET the page with a desktop User-Agent.
    2. Parse HTML with BeautifulSoup; find the <script> tag whose content
       contains a "transcript" JSON key (Apple names it something like
       ``window.__APOLLO_STATE__`` or embeds it in ``data-react-props``).
    3. Walk the JSON, extract the transcript cues, normalize to the schema
       above, write to ``workdir/transcript.json``.
    4. If anything fails (page structure changed / non-Apple URL), exit
       non-zero and print a clear message so callers fall back to VTT.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup


UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15"
)


def fetch_apple_transcript(url: str, workdir: Path) -> Path:
    workdir.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    # TODO: identify and parse the transcript JSON blob.
    #   Apple has historically used either:
    #     - a <script> tag with ``window.__APOLLO_STATE__ = {...}``, or
    #     - a transcript tab rendered server-side with timestamp <span>s.
    #   Start by dumping all scripts to a sibling file during development:
    #       (workdir / "apple_raw.html").write_text(resp.text, encoding="utf-8")
    #   Then reverse-engineer and narrow down.
    raise NotImplementedError(
        "TODO: implement Apple transcript parsing. "
        "For now, fall back to the YouTube VTT produced by fetch_video.sh."
    )


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(f"Usage: {argv[0]} <apple_session_url> <workdir>", file=sys.stderr)
        return 2
    url, workdir = argv[1], Path(argv[2])
    out = fetch_apple_transcript(url, workdir)
    print(f"==> Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
