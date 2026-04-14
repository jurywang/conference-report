#!/usr/bin/env python3
"""segment_features.py — Turn chapters + transcript into a feature candidate list.

Input (inside ``<workdir>``):
    chapters.json        — required; from fetch_apple_transcript.py or yt-dlp
    transcript.json      — optional; [{start, end, text}] cues

Output:
    features_candidates.json — list of:
        {
          "id": "ios",
          "title_en": "iOS",
          "title_zh": "",                 # fill via Claude translation or by hand
          "presenter": "",
          "start_ts": 228.0,
          "end_ts": 2495.0,
          "chapter_source": "apple" | "youtube-chapters" | "transcript-split",
          "one_line_summary": "First two transcript sentences of the chapter…",
          "keywords": ["liquid-glass", "live-translation", ...],
          "needs_subdivision": true,      # chapter > 4 min and no sub-splits
        }

Also prints a pretty summary to stdout so Claude (and the user) can review
the candidate list before Stage B.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title.lower(), flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug or "unnamed"


# Words to ignore when extracting keywords.
_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "of", "in", "on", "at", "to", "for",
    "from", "by", "with", "as", "is", "are", "was", "were", "be", "been",
    "this", "that", "these", "those", "it", "its", "we", "you", "i", "us",
    "our", "your", "my", "he", "she", "they", "them", "their", "his", "her",
    "will", "can", "could", "would", "should", "may", "might", "now", "just",
    "so", "also", "even", "all", "any", "some", "more", "most", "new", "one",
    "two", "three", "four", "five", "very", "really", "much", "like", "get",
    "got", "going", "here", "there", "what", "when", "where", "why", "how",
    "do", "does", "did", "have", "has", "had", "let", "lets",
    # Presenter / WWDC filler
    "apple", "today", "welcome", "everyone", "thank", "thanks", "hello",
    "wwdc", "think", "make", "makes", "see", "look", "introduce",
}

_CAMEL_SPLIT = re.compile(r"[A-Z][a-z]+|[a-z]+")


def extract_keywords(text: str, top_n: int = 6) -> list[str]:
    """Most frequent capitalised / multi-word terms in the segment."""
    # Grab two-word Title-Case phrases (e.g. "Live Translation", "Liquid Glass").
    phrases = re.findall(r"(?:\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b)", text)
    # Filter out common speaker phrases.
    phrases = [p for p in phrases if p.lower() not in {
        "tim cook", "craig federighi", "john ternus", "kate bergeron",
        "good morning", "thank you", "apple intelligence",   # handled below
    }]
    counter = Counter(phrases)

    # Single capitalised words (iOS, macOS, etc.) — deduped against phrases.
    single_caps = re.findall(r"\b(?:i|mac|tv|watch|vision|ipad)OS\b|"
                             r"\b(?:iPhone|iPad|Mac|Watch|AirPods)\b", text)
    counter.update(single_caps)

    # Common Apple Intelligence / WWDC tech terms.
    known = re.findall(
        r"\b(?:Apple Intelligence|Live Translation|Liquid Glass|Visual Intelligence|"
        r"Workout Buddy|Foundation Models|Image Playground|Genmoji|Writing Tools|"
        r"Smart Replies|Call Screening|ChatGPT|App Intents|Siri)\b",
        text, flags=re.IGNORECASE,
    )
    counter.update(k.title() for k in known)

    # Filter: drop stopwords and 1-char noise.
    ranked = [
        (w, c) for (w, c) in counter.most_common()
        if w.strip() and w.lower() not in _STOP_WORDS and len(w) > 2
    ]
    return [w for w, _ in ranked[:top_n]]


_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def first_sentences(text: str, n: int, max_chars: int = 180) -> str:
    parts = _SENTENCE_BOUNDARY.split(text.strip())
    joined = " ".join(parts[:n]).strip()
    if len(joined) > max_chars:
        joined = joined[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    return joined


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_chapters(workdir: Path) -> list[dict]:
    """Accept both Apple-style (`start_ts/end_ts/title`) and yt-dlp-style
    (`start_time/end_time/title`) chapter JSON."""
    p = workdir / "chapters.json"
    if not p.exists():
        raise SystemExit(f"missing {p}; run fetch_apple_transcript.py or fetch_video.sh first.")
    raw = json.loads(p.read_text())
    if not raw:
        raise SystemExit(f"{p} is empty")
    out = []
    for i, ch in enumerate(raw):
        title = ch.get("title") or f"Chapter {i + 1}"
        start = ch.get("start_ts", ch.get("start_time"))
        end = ch.get("end_ts", ch.get("end_time"))
        if start is None or end is None:
            continue
        out.append({
            "title": title,
            "start_ts": float(start),
            "end_ts": float(end),
        })
    return out


def load_transcript(workdir: Path) -> list[dict]:
    p = workdir / "transcript.json"
    if not p.exists():
        return []
    return json.loads(p.read_text())


def segment_text(transcript: list[dict], start: float, end: float) -> str:
    """Concatenate transcript cues that overlap the [start, end] span."""
    return " ".join(
        c["text"] for c in transcript
        if c["start"] < end and (c.get("end") or c["start"]) > start
    )


# ---------------------------------------------------------------------------
# Candidate builder
# ---------------------------------------------------------------------------

LONG_CHAPTER_SEC = 240  # > 4 min → flag for subdivision


def build_candidates(workdir: Path) -> list[dict]:
    chapters = load_chapters(workdir)
    transcript = load_transcript(workdir)

    candidates = []
    for ch in chapters:
        text = segment_text(transcript, ch["start_ts"], ch["end_ts"]) if transcript else ""
        keywords = extract_keywords(text) if text else []
        summary = first_sentences(text, 2) if text else ""

        duration = ch["end_ts"] - ch["start_ts"]
        candidates.append({
            "id": slugify(ch["title"]),
            "title_en": ch["title"],
            "title_zh": "",
            "presenter": "",
            "start_ts": ch["start_ts"],
            "end_ts": ch["end_ts"],
            "chapter_source": "apple" if transcript or (workdir / "apple_raw.html").exists()
                             else "youtube-chapters",
            "one_line_summary": summary,
            "keywords": keywords,
            "needs_subdivision": bool(
                duration > LONG_CHAPTER_SEC and not transcript
            ),
        })
    return candidates


def pretty_print(candidates: list[dict]) -> None:
    print()
    print(f"{'#':>3}  {'ID':<22} {'Duration':>8}  {'Sub?':<5}  Title")
    print("-" * 78)
    for i, c in enumerate(candidates, 1):
        dur = int(c["end_ts"] - c["start_ts"])
        flag = "FLAG" if c.get("needs_subdivision") else ""
        print(f"{i:>3}  {c['id']:<22} {dur:>5}s  {flag:<5}  {c['title_en']}")
    print()
    flagged = [c for c in candidates if c.get("needs_subdivision")]
    if flagged:
        print(f"NOTE: {len(flagged)} chapter(s) > {LONG_CHAPTER_SEC}s and no transcript available.")
        print("      Consider manually subdividing in features_candidates.json before Stage B,")
        print("      or rerun fetch_apple_transcript.py after loading the page in a browser.")
        print()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <workdir>", file=sys.stderr)
        return 2
    workdir = Path(argv[1])
    candidates = build_candidates(workdir)
    out = workdir / "features_candidates.json"
    out.write_text(json.dumps(candidates, ensure_ascii=False, indent=2))
    print(f"==> Wrote {out} ({len(candidates)} candidates)")
    pretty_print(candidates)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
