#!/usr/bin/env python3
"""smoke_test.py — Build a throwaway PPT with synthetic data to verify theme.

Run:
    python3 scripts/smoke_test.py
Outputs:
    workspace/_smoke/_smoke_insights.pptx
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent.parent  # skill dir
WORKDIR = HERE / "workspace" / "_smoke"


def make_fake_hero(path: Path, label: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1920, 1080), (30, 30, 35))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype("DejaVuSans-Bold.ttf", 96)
    except OSError:
        f = ImageFont.load_default()
    d.text((80, 80), label, fill=(255, 220, 220), font=f)
    d.rectangle([80, 920, 1840, 1000], fill=(139, 26, 26))
    img.save(path)


def main() -> int:
    WORKDIR.mkdir(parents=True, exist_ok=True)

    features = [
        {
            "id": "live-translation",
            "title_en": "Live Translation",
            "title_zh": "实时翻译（AirPods / Messages / FaceTime）",
            "section_tag": "Apple Intelligence",
            "thesis_zh": "实时翻译：苹果正式吞并翻译机品类",
            "hero": "frames/live-translation/best_0.png",
            "impact_bullets": [
                "翻译 App 从独立品类降为系统能力，使用频次大幅下滑",
                "AirPods 成为随身翻译机，讯飞 / Pocketalk 核心场景被吞",
                "开发者可调用 Translation API，为旅行类 App 开新入口",
            ],
            "quotes": [
                {"text": "Apple just made pocket translators obsolete overnight.",
                 "source": "The Verge", "url": "https://theverge.com/"},
                {"text": "翻译机品类的生存空间被进一步压缩。",
                 "source": "36Kr", "url": "https://36kr.com/"},
                {"text": "Real-time translation in AirPods is the sleeper hit of WWDC.",
                 "source": "Bloomberg", "url": "https://bloomberg.com/"},
            ],
        },
        {
            "id": "liquid-glass",
            "title_en": "Liquid Glass",
            "title_zh": "Liquid Glass 设计语言",
            "section_tag": "iOS / macOS",
            "thesis_zh": "Liquid Glass：把'主题美化'拉回系统默认",
            "hero": "frames/liquid-glass/best_0.png",
            "impact_bullets": [
                "第三方主题 / 图标包 App 差异化价值被抹平",
                "iPad / Mac 跨端一致性显著提升，用户迁移成本下降",
                "开发者需要重新适配材质与透明度，UI 升级潮来袭",
            ],
            "quotes": [
                {"text": "It's the boldest design refresh since iOS 7.",
                 "source": "Daring Fireball", "url": "https://daringfireball.net/"},
                {"text": "Liquid Glass 把'苹果味'的辨识度再拉高了一档。",
                 "source": "少数派", "url": "https://sspai.com/"},
            ],
        },
    ]

    for f in features:
        make_fake_hero(WORKDIR / f["hero"], f["title_en"])

    payload = {
        "keynote_tag": "WWDC 2025",
        "cover_title": "WWDC 2025 Keynote 洞察",
        "cover_subtitle": "12 个关键特性 × 行业冲击分析",
        "source_url": "生成自 smoke test · https://developer.apple.com/",
        "features": features,
        "closing": {
            "title": "本届 Keynote · 三大主题",
            "themes": [
                ["AI 系统化", "端侧 LLM 下沉到每一个 App",
                 ["中小 App 拿到免费推理", "云端 LLM 调用被挤压", "插件生态回暖"]],
                ["设计语言升级", "Liquid Glass 统一体验",
                 ["主题美化类 App 价值降低", "跨端一致性提升", "UI 升级潮"]],
                ["硬件 × 系统协同", "AirPods / Watch 成系统入口",
                 ["翻译机 / 健身设备品类承压", "配件使用频次上升", "换机周期缩短"]],
            ],
        },
    }
    (WORKDIR / "slides.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    # Run build
    sys.path.insert(0, str(HERE / "scripts"))
    from build_ppt import build
    out = build(WORKDIR)
    size_kb = out.stat().st_size // 1024
    print(f"==> Smoke PPT: {out} ({size_kb} KB)")
    if size_kb < 10:
        print("‼️  Smoke PPT too small; something likely failed silently.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
