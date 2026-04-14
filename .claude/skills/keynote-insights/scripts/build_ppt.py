#!/usr/bin/env python3
"""build_ppt.py — Assemble the final .pptx from workspace artifacts.

Expected workspace layout:
    <workdir>/
        info.json
        features_selected.json    # user-curated subset of candidates
        frames/<feature_id>/best_0.png
        gifs/<feature_id>.gif                (optional)
        commentary/<feature_id>.md           (optional but recommended)
        slides.json                          # per-feature analysis payload

``slides.json`` is the "final assembly input", authored by Claude after research:

    {
      "keynote_tag": "WWDC 2025",
      "cover_title": "WWDC 2025 Keynote 洞察",
      "cover_subtitle": "12 个关键特性 × 行业冲击分析",
      "source_url": "https://…",
      "features": [
        {
          "id": "live-translation",
          "title_en": "Live Translation",
          "section_tag": "Apple Intelligence",
          "thesis_zh": "实时翻译：苹果正式吞并翻译机品类",
          "hero": "frames/live-translation/best_0.png",   # or gifs/live-translation.gif
          "impact_bullets": ["…", "…", "…"],
          "quotes": [
              {"text": "…", "source": "Mark Gurman, Bloomberg", "url": "https://…"},
              ...
          ]
        },
        ...
      ],
      "closing": {
          "title": "本届 Keynote · 三大主题",
          "themes": [
              ["AI 下沉到系统", "端侧 LLM 免费给开发者",
               ["中小 App 拿到免费推理", "云端 LLM 调用量被挤压", "插件生态回暖"]],
              ...
          ]
      }
    }

Usage:
    build_ppt.py <workdir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Make sibling `templates` package importable when invoked as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pptx import Presentation  # noqa: E402
from pptx.util import Inches   # noqa: E402

from templates import theme as T             # noqa: E402
from templates.slide_cover import render_cover     # noqa: E402
from templates.slide_toc import render_toc         # noqa: E402
from templates.slide_feature import render_feature_slide  # noqa: E402
from templates.slide_closing import render_closing       # noqa: E402


def build(workdir: Path) -> Path:
    payload = json.loads((workdir / "slides.json").read_text())
    features = payload["features"]

    prs = Presentation()
    prs.slide_width = T.SLIDE_W
    prs.slide_height = T.SLIDE_H

    # 1. Cover
    render_cover(
        prs,
        title=payload.get("cover_title", payload["keynote_tag"] + " 洞察"),
        subtitle=payload.get("cover_subtitle", ""),
        footer=payload.get("source_url", ""),
    )

    # 2. TOC: pages are: cover(1) + toc(2) + feature_i (3..3+N-1) + closing
    toc_items = [(f.get("title_zh") or f["title_en"], 3 + i) for i, f in enumerate(features)]
    render_toc(prs, title="目录 · Contents", items=toc_items)

    # 3. Feature pages
    for i, f in enumerate(features, start=1):
        hero = workdir / f["hero"]
        if not hero.exists():
            raise FileNotFoundError(f"hero asset missing: {hero}")
        render_feature_slide(
            prs,
            index=i,
            total=len(features),
            keynote_tag=payload["keynote_tag"],
            section_tag=f.get("section_tag", ""),
            hero_image=hero,
            thesis_zh=f["thesis_zh"],
            title_en=f["title_en"],
            impact_bullets=f.get("impact_bullets", []),
            quotes=[(q["text"], q["source"], q.get("url", "")) for q in f.get("quotes", [])],
        )

    # 4. Closing
    closing = payload.get("closing")
    if closing:
        render_closing(
            prs,
            title=closing.get("title", "总结"),
            themes=closing.get("themes", []),
            footer=payload.get("source_url", ""),
        )

    keynote_id = workdir.name
    out = workdir / f"{keynote_id}_insights.pptx"
    prs.save(out)
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <workdir>", file=sys.stderr)
        return 2
    out = build(Path(argv[1]))
    print(f"==> Wrote {out} ({out.stat().st_size//1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
