#!/usr/bin/env python3
"""segment_features.py — Turn chapters + transcript into a feature candidate list.

Input (inside ``<workdir>``):
    chapters.json        — yt-dlp chapter markers
    transcript.json      — from Apple or VTT normalized to the same schema
    subtitles.en.vtt     — VTT fallback if transcript.json missing

Output:
    features_candidates.json — list of:
        {
          "id": "live-translation",
          "title_zh": "实时翻译（AirPods / Messages / FaceTime）",
          "title_en": "Live Translation",
          "presenter": "…",          # optional
          "start_ts": 1234.5,        # seconds
          "end_ts": 1380.0,
          "chapter_source": "youtube-chapters" | "transcript-keywords" | "claude-merge",
          "one_line_summary": "…",
          "keywords": ["translation", "AirPods", …],
        }

Implementation plan (TODO):
    1. Load chapters.json. If present and non-empty, use each chapter as a
       candidate with `chapter_source = "youtube-chapters"`.
    2. Load transcript.json (or parse VTT if transcript.json missing).
    3. Enrich each candidate:
       - `keywords`: most-frequent nouns in the chapter span.
       - `one_line_summary`: first 1-2 transcript lines, trimmed.
       - `title_en`: chapter title verbatim.
       - `title_zh`: left empty — fill via Claude translation / user edit
         OR let the caller (skill) use Claude on the summary.
    4. If chapters are missing / too coarse (e.g. single chapter for 90 min),
       use keyword clustering on transcript to split further.
    5. Write features_candidates.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def slugify(title: str) -> str:
    import re
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug or "unnamed"


def segment(workdir: Path) -> Path:
    chapters_path = workdir / "chapters.json"
    if not chapters_path.exists():
        raise SystemExit(f"Missing {chapters_path}; run fetch_video.sh first.")

    chapters = json.loads(chapters_path.read_text())
    # TODO: merge with transcript for richer candidates; for now, just pass
    # through the yt-dlp chapters so downstream scripts have something to eat.
    candidates = []
    for i, ch in enumerate(chapters):
        title = ch.get("title", f"Chapter {i+1}")
        candidates.append({
            "id": slugify(title),
            "title_en": title,
            "title_zh": "",                 # TODO: translate via Claude
            "presenter": "",
            "start_ts": float(ch.get("start_time", 0.0)),
            "end_ts": float(ch.get("end_time", 0.0)),
            "chapter_source": "youtube-chapters",
            "one_line_summary": "",         # TODO: fill from transcript
            "keywords": [],                 # TODO: extract top nouns
        })

    out = workdir / "features_candidates.json"
    out.write_text(json.dumps(candidates, ensure_ascii=False, indent=2))
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <workdir>", file=sys.stderr)
        return 2
    out = segment(Path(argv[1]))
    print(f"==> Wrote {out} ({len(json.loads(out.read_text()))} candidates)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
