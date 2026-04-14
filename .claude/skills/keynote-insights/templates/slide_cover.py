"""Cover slide — crimson gradient background with big white title."""
from __future__ import annotations

from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches

from . import theme as T


def render_cover(prs, *, title: str, subtitle: str, footer: str = ""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, T.SLIDE_W, T.SLIDE_H)
    # python-pptx has limited gradient support; use flat crimson_dark for now.
    bg.fill.solid()
    bg.fill.fore_color.rgb = T.CRIMSON_DARK
    bg.line.fill.background()

    # Accent bar: thin crimson slightly above center
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                    Inches(0.8), Inches(3.0),
                                    Inches(2.0), Inches(0.08))
    accent.fill.solid()
    accent.fill.fore_color.rgb = T.CRIMSON
    accent.line.fill.background()

    # Title
    tb = slide.shapes.add_textbox(Inches(0.8), Inches(3.2), Inches(12.0), Inches(1.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    T.apply_text(p.add_run(), title,
                 font_name=T.FONT_CN, size=T.FONT_SIZE["cover_main"],
                 bold=True, color=T.WHITE)

    # Subtitle
    sb = slide.shapes.add_textbox(Inches(0.8), Inches(5.1), Inches(12.0), Inches(0.8))
    sp = sb.text_frame.paragraphs[0]
    T.apply_text(sp.add_run(), subtitle,
                 font_name=T.FONT_CN, size=T.FONT_SIZE["cover_sub"],
                 color=T.LIGHT_GRAY)

    # Footer (small)
    if footer:
        fb = slide.shapes.add_textbox(Inches(0.8), Inches(6.9), Inches(12.0), Inches(0.4))
        fp = fb.text_frame.paragraphs[0]
        T.apply_text(fp.add_run(), footer,
                     font_name=T.FONT_EN, size=T.FONT_SIZE["pageno"],
                     color=T.LIGHT_GRAY)
    return slide
