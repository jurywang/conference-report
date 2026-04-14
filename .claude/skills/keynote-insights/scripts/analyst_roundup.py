#!/usr/bin/env python3
"""analyst_roundup.py — Collect external commentary for one feature.

This script is **driven by Claude** (which owns the WebSearch tool). The
Python side just:

    1. Reads the feature entry (title_en, keywords).
    2. Prints a machine-readable plan to stdout: search queries + domain
       whitelist (from references/analyst_sources.md).
    3. Once Claude has done the searches and drafted summaries, it writes
       <workdir>/commentary/<feature_id>.md with the structure below, and
       subsequent slide-build steps read from there.

Expected commentary markdown structure:

    # {title_zh} — 外部观点

    ## 要点汇总
    - {bullet 1}
    - {bullet 2}

    ## 分析师 / 自媒体引述
    > "…" — {source}, [{outlet}]({url}), {date}

    > "…" — {source}, [{outlet}]({url}), {date}

    ## 反方 / 风险视角
    > "…" — …

Usage:
    analyst_roundup.py plan    <workdir> <feature_id>
    analyst_roundup.py inspect <workdir> <feature_id>   # validate commentary.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


WHITELIST_PATH_NOTE = "references/analyst_sources.md"


def load_feature(workdir: Path, feature_id: str) -> dict:
    for name in ("features_selected.json", "features_candidates.json"):
        p = workdir / name
        if p.exists():
            for feat in json.loads(p.read_text()):
                if feat["id"] == feature_id:
                    return feat
    raise SystemExit(f"Feature '{feature_id}' not found.")


def plan(workdir: Path, feature_id: str) -> dict:
    feat = load_feature(workdir, feature_id)
    title_en = feat.get("title_en") or feature_id
    title_zh = feat.get("title_zh") or ""
    queries = [
        f"{title_en} WWDC review impact",
        f"{title_en} analyst opinion",
        f"{title_en} vs competitors",
    ]
    if title_zh:
        queries.append(f"{title_zh} 分析 影响 行业")
    return {
        "feature_id": feature_id,
        "title_en": title_en,
        "title_zh": title_zh,
        "queries": queries,
        "allowed_domains_source": WHITELIST_PATH_NOTE,
        "target_quotes": {"min": 3, "max": 6, "at_least_one_cn": True, "at_least_one_en": True},
        "output_path": str(workdir / "commentary" / f"{feature_id}.md"),
    }


def inspect(workdir: Path, feature_id: str) -> dict:
    md = workdir / "commentary" / f"{feature_id}.md"
    if not md.exists():
        return {"ok": False, "reason": f"missing {md}"}
    text = md.read_text()
    quote_count = text.count("\n> ")
    url_count = len(re.findall(r"\]\(https?://", text))
    return {
        "ok": quote_count >= 3 and url_count >= quote_count - 1,
        "quote_count": quote_count,
        "url_count": url_count,
        "path": str(md),
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, _ in (("plan", plan), ("inspect", inspect)):
        spx = sub.add_parser(name)
        spx.add_argument("workdir", type=Path)
        spx.add_argument("feature_id")
    args = ap.parse_args(argv[1:])
    fn = plan if args.cmd == "plan" else inspect
    result = fn(args.workdir, args.feature_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
