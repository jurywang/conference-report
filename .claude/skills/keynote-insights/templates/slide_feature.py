"""Feature slide: hero image on top, thesis mid, industry bullets & quotes bottom.

Layout is driven by ``theme.FEATURE_LAYOUT``; edit the layout spec, not this file.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

from . import theme as T


def _add_rect(slide, left, top, width, height, fill_rgb, line=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_rgb
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
    shape.shadow.inherit = False
    return shape


def _add_text(slide, box: T.Box, text: str, *, size=Pt(14), color=T.BODY_GRAY,
              bold=False, font=T.FONT_CN, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    left, top, w, h = box.as_emu()
    tb = slide.shapes.add_textbox(left, top, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0)
    tf.margin_right = Inches(0)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    T.apply_text(p.add_run(), text, font_name=font, size=size, bold=bold, color=color)
    return tb


def _fit_image(img_path: Path, max_w_in: float, max_h_in: float):
    """Compute (left, top, width, height) in inches to center-fit image in hero box."""
    with Image.open(img_path) as img:
        iw, ih = img.size
    ar = iw / ih
    # Try width-first
    w, h = max_w_in, max_w_in / ar
    if h > max_h_in:
        h = max_h_in
        w = max_h_in * ar
    return w, h


def render_feature_slide(
    prs,
    *,
    index: int,
    total: int,
    keynote_tag: str,               # e.g. "WWDC 2025"
    section_tag: str,               # e.g. "Apple Intelligence"
    hero_image: Path,               # .png or .gif (PPT supports static gif)
    thesis_zh: str,
    title_en: str,
    impact_bullets: Iterable[str],  # 3 strings
    quotes: Iterable[tuple[str, str, str]],  # (quote_text, source_label, url)
):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    # Background: light gray
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, T.SLIDE_W, T.SLIDE_H)
    bg.fill.solid()
    bg.fill.fore_color.rgb = T.LIGHT_GRAY
    bg.line.fill.background()

    L = T.FEATURE_LAYOUT

    # ---- Top bar: crimson ribbon with "WWDC 2025 · NN/NN" and section tag ----
    _add_rect(slide, *L["topbar"].as_emu(), fill_rgb=T.CRIMSON)
    _add_text(slide, T.Box(0.4, 0.02, 6.0, 0.30),
              f"{keynote_tag} · 特性 {index:02d}/{total:02d}",
              size=T.FONT_SIZE["topbar"], color=T.WHITE, bold=True)
    _add_text(slide, T.Box(7.0, 0.02, 5.9, 0.30),
              section_tag,
              size=T.FONT_SIZE["topbar"], color=T.WHITE, align=PP_ALIGN.RIGHT)

    # ---- Hero image ----
    hero_box = L["hero"]
    img_w, img_h = _fit_image(hero_image, hero_box.width, hero_box.height)
    img_left = hero_box.left + (hero_box.width - img_w) / 2
    img_top = hero_box.top + (hero_box.height - img_h) / 2
    slide.shapes.add_picture(
        str(hero_image),
        Inches(img_left), Inches(img_top),
        width=Inches(img_w), height=Inches(img_h),
    )

    # ---- Thesis (big crimson headline) + EN subtitle ----
    thesis_box = L["thesis"]
    _add_text(slide,
              T.Box(thesis_box.left, thesis_box.top, thesis_box.width, 0.55),
              thesis_zh,
              size=T.FONT_SIZE["thesis"], color=T.CRIMSON, bold=True)
    _add_text(slide,
              T.Box(thesis_box.left, thesis_box.top + 0.55, thesis_box.width, 0.30),
              title_en,
              size=T.FONT_SIZE["subtitle"], color=T.MUTED_GRAY, font=T.FONT_EN)

    # ---- Industry impact: 3 bullets with crimson square markers ----
    impact_box = L["impact"]
    bullets = list(impact_bullets)[:3]
    row_h = impact_box.height / max(len(bullets), 1)
    for i, b in enumerate(bullets):
        top_i = impact_box.top + i * row_h + 0.08
        # Marker
        _add_rect(slide,
                  Inches(impact_box.left), Inches(top_i + 0.05),
                  Inches(0.18), Inches(0.18),
                  fill_rgb=T.CRIMSON)
        _add_text(slide,
                  T.Box(impact_box.left + 0.30, top_i, impact_box.width - 0.30, row_h),
                  b,
                  size=T.FONT_SIZE["bullet"], color=T.BODY_GRAY)

    # ---- Quotes: 2-3 lines, small font, with source ----
    q_box = L["quotes"]
    quotes = list(quotes)[:3]
    if quotes:
        row_h = q_box.height / len(quotes)
        for i, (text, label, _url) in enumerate(quotes):
            top_i = q_box.top + i * row_h
            snippet = text if len(text) <= 80 else text[:78] + "…"
            _add_text(slide,
                      T.Box(q_box.left, top_i, q_box.width * 0.75, row_h),
                      f"“{snippet}”",
                      size=T.FONT_SIZE["quote"], color=T.BODY_GRAY)
            _add_text(slide,
                      T.Box(q_box.left + q_box.width * 0.76, top_i,
                            q_box.width * 0.24, row_h),
                      f"— {label}",
                      size=T.FONT_SIZE["quote_src"], color=T.MUTED_GRAY,
                      align=PP_ALIGN.RIGHT)

    # ---- Page number ----
    _add_text(slide, L["pageno"], f"{index:02d}",
              size=T.FONT_SIZE["pageno"], color=T.MUTED_GRAY,
              align=PP_ALIGN.RIGHT)
    return slide
