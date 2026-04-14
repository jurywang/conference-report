"""Theme constants for the keynote-insights PPT.

All values mirror ``references/ppt_layout_spec.md`` — keep them in sync.
"""
from __future__ import annotations

from dataclasses import dataclass

from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
CRIMSON = RGBColor(0x8B, 0x1A, 0x1A)        # 主色 深红
CRIMSON_DARK = RGBColor(0x5E, 0x11, 0x11)   # 主色 深红·深
LIGHT_GRAY = RGBColor(0xF4, 0xF4, 0xF4)     # 辅色 浅灰（页背景）
BODY_GRAY = RGBColor(0x4A, 0x4A, 0x4A)      # 正文灰
MUTED_GRAY = RGBColor(0x8A, 0x8A, 0x8A)     # 次级灰
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------
FONT_CN = "PingFang SC"            # 回落由 PowerPoint / Keynote 自行处理
FONT_EN = "SF Pro Display"

FONT_SIZE = {
    "thesis": Pt(28),       # 观点标题
    "subtitle": Pt(14),     # 英文副标题
    "bullet": Pt(14),       # 行业影响
    "quote": Pt(10),        # 媒体引述正文
    "quote_src": Pt(8),     # 媒体来源
    "topbar": Pt(10),       # 顶部导航条
    "pageno": Pt(9),        # 页码
    "cover_main": Pt(80),
    "cover_sub": Pt(24),
    "toc_item": Pt(16),
    "closing_title": Pt(36),
}


# ---------------------------------------------------------------------------
# Slide dimensions (16:9 widescreen default: 13.333" x 7.5")
# ---------------------------------------------------------------------------
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


@dataclass(frozen=True)
class Box:
    """Inch-based bounding box, convenient for python-pptx ``add_*(left, top, w, h)``."""
    left: float
    top: float
    width: float
    height: float

    def as_emu(self):
        return (Inches(self.left), Inches(self.top), Inches(self.width), Inches(self.height))


# Feature slide regions (percentages from ppt_layout_spec.md, materialized in inches).
# SLIDE_H == 7.5"
FEATURE_LAYOUT = {
    "topbar":    Box(left=0.0,  top=0.00, width=13.333, height=0.30),   # 4%
    "hero":      Box(left=0.40, top=0.40, width=12.533, height=4.125),  # 55%, centered horizontally
    "thesis":    Box(left=0.60, top=4.65, width=12.133, height=0.90),   # 12%
    "impact":    Box(left=0.60, top=5.60, width=12.133, height=1.20),   # 16%
    "quotes":    Box(left=0.60, top=6.85, width=12.133, height=0.60),   # 13%; use 0.60 to leave margin
    "pageno":    Box(left=12.6, top=7.20, width=0.6,    height=0.25),
}

# Cover / TOC / Closing boxes left to their template modules.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def apply_text(run, text: str, *, font_name=FONT_CN, size=None, bold=False, color=BODY_GRAY):
    """Set a run's text + font + size + color in one call."""
    run.text = text
    run.font.name = font_name
    if size is not None:
        run.font.size = size
    run.font.bold = bold
    run.font.color.rgb = color
    return run
