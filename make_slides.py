"""Generate the ONE-HOUR workshop deck:
"Reproducible Science in the Age of Vibe Coding".

Cut down from the long version so it actually fits an hour. The budget:

    4 min   welcome and the problem
    8 min   Part 1 - reproducible by construction
   10 min   Part 2 - vibe coding with LLMs
   15 min   HANDS-ON - fix a script that runs but lies
   10 min   Part 3 - risks and guardrails
    4 min   wrap-up
    ~9 min  Q&A

    27 talk slides + 5 hands-on slides + a 14-slide appendix.

Everything cut from the main flow that is still worth having is condensed into
the appendix, which is reference material rather than agenda.

Markers:
    CORE       - the spine of the workshop; do not skip
    DEEP DIVE  - run if the room is quick; otherwise it is a handout
    OPTIONAL   - reference material only

Built on the Netherlands eScience Center master template.
Sources (all CC-BY 4.0; The Carpentries / eScience Center / NLeSC):
- https://carpentries-incubator.github.io/good-practices-lesson/
- https://carpentries-incubator.github.io/gen-ai-coding/
- https://carpentries-incubator.github.io/reproducible-research-through-reusable-code-in-1-day/
- https://carpentries-incubator.github.io/collaborative-git-and-github-lesson/
"""

import re
from math import ceil

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# --------------------------------------------------------------------------
# Netherlands eScience Center palette, taken from the theme of the master
# template ("eScience colors": accent1 009DDD, accent2 380338, accent3 FFB213)
# --------------------------------------------------------------------------
ESI_BLUE = RGBColor(0x00, 0x9D, 0xDD)
ESI_BLUE_DARK = RGBColor(0x00, 0x6B, 0x96)
ESI_PURPLE = RGBColor(0x38, 0x03, 0x38)
ESI_AMBER = RGBColor(0xFF, 0xB2, 0x13)
ESI_AMBER_DARK = RGBColor(0x9A, 0x66, 0x00)

BLUE_TINT = RGBColor(0xE4, 0xF5, 0xFC)
PURPLE_TINT = RGBColor(0xF6, 0xEC, 0xF6)
AMBER_TINT = RGBColor(0xFF, 0xF4, 0xDE)
CARD = RGBColor(0xF4, 0xF8, 0xFB)

# Semantic aliases used by the slide layouts below.
NAVY = ESI_PURPLE           # headings, panel headers, dark backgrounds
NAVY_SOFT = ESI_BLUE_DARK   # table header rows
TEAL = ESI_BLUE             # primary accent
TEAL_DARK = ESI_BLUE_DARK   # small accent labels
GREEN = ESI_BLUE            # the better option in a comparison
RED = ESI_AMBER_DARK        # the problematic option in a comparison
AMBER = ESI_AMBER           # caution, prompts, exercise headers
AMBER_DARK = ESI_AMBER_DARK
LIGHT = RGBColor(0xFF, 0xFF, 0xFF)
BAND = RGBColor(0xEE, 0xF3, 0xF9)   # table row banding and rules
SLATE = RGBColor(0xB4, 0xC0, 0xCB)
CODE_BG = ESI_PURPLE
CODE_INK = RGBColor(0xF2, 0xEC, 0xF2)
CODE_DIM = RGBColor(0xBA, 0xA7, 0xBA)
MUTED = RGBColor(0xD8, 0xE8, 0xF5)
FAINT = RGBColor(0x8C, 0x99, 0xA6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x33, 0x33, 0x33)
GREY = RGBColor(0x5F, 0x6B, 0x76)
GREEN_TINT = BLUE_TINT
RED_TINT = AMBER_TINT

# Fonts from the master template theme (majorFont / minorFont).
FONT = "Assistant"
FONT_H = "Nunito"
MONO = "Consolas"

SW = Inches(13.333)
SH = Inches(7.5)
BODY_L = Inches(0.72)
BODY_W = Inches(11.89)
BODY_TOP = Inches(1.68)

# The eScience logo occupies the top-left corner of the content layout, so
# slide titles start to the right of it.
TITLE_X = Inches(2.62)
TITLE_W = Inches(8.35)

MARKERS = {
    "CORE": (ESI_BLUE, WHITE),
    "DEEP DIVE": (ESI_AMBER, ESI_PURPLE),
    "OPTIONAL": (RGBColor(0xB4, 0xC0, 0xCB), ESI_PURPLE),
}

KEYWORDS = {
    "def", "class", "import", "from", "return", "if", "elif", "else", "for",
    "while", "with", "assert", "in", "not", "and", "or", "print", "raise",
    "try", "except", "as", "lambda", "yield", "pass", "None", "True", "False",
    "git", "pytest", "name", "on", "jobs", "steps", "runs-on",
}


# --------------------------------------------------------------------------
# Primitives
# --------------------------------------------------------------------------
def _rect(slide, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE, radius=None):
    shp = slide.shapes.add_shape(shape, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.fill.background()
    shp.shadow.inherit = False
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        shp.adjustments[0] = radius
    return shp


def _tb(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return tf


def _text(slide, x, y, w, h, text, size=16, color=INK, bold=False,
          font=FONT, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
          italic=False, spacing=None):
    tf = _tb(slide, x, y, w, h, anchor)
    first = True
    for line in str(text).split("\n"):
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        if spacing:
            p.line_spacing = spacing
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.name = font
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
    return tf


def add_bullets(slide, items, x=BODY_L, y=BODY_TOP, w=BODY_W, h=Inches(4.6),
                size=16, space=9, dark=False):
    """items: str | (str, level) | (str, level, lead_in)."""
    tf = _tb(slide, x, y, w, h)
    first = True
    for item in items:
        lead = None
        if isinstance(item, tuple):
            text, level = item[0], item[1]
            if len(item) == 3:
                lead = item[2]
        else:
            text, level = item, 0
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = level
        p.space_after = Pt(space)
        p.line_spacing = 0.97
        m = p.add_run()
        m.text = "\u25CF  " if level == 0 else "\u2013  "
        m.font.size = Pt(size - 5 if level == 0 else size - 4)
        m.font.name = FONT
        m.font.color.rgb = TEAL if level == 0 else AMBER
        if lead:
            lr = p.add_run()
            lr.text = lead + " "
            lr.font.size = Pt(size if level == 0 else size - 2)
            lr.font.name = FONT
            lr.font.bold = True
            lr.font.color.rgb = MUTED if dark else NAVY
        r = p.add_run()
        r.text = text
        r.font.size = Pt(size if level == 0 else size - 2)
        r.font.name = FONT
        r.font.color.rgb = (CODE_INK if dark else INK) if level == 0 else (
            CODE_DIM if dark else GREY)
    return tf


# --------------------------------------------------------------------------
# Chrome
# --------------------------------------------------------------------------
_FOOTERS = []


def footer(slide, dark=False):
    """Draw the footer. The page total is filled in by finalize_footers()."""
    col = MUTED if dark else GREY
    _text(slide, Inches(1.15), Inches(7.06), Inches(8.0), Inches(0.28),
          "Reproducible Science in the Age of Vibe Coding", size=9, color=col)
    n = len(prs.slides._sldIdLst)
    tf = _text(slide, Inches(11.1), Inches(7.06), Inches(1.51), Inches(0.28),
               "", size=9, color=col, align=PP_ALIGN.RIGHT)
    _FOOTERS.append((tf, n))


def finalize_footers():
    total = len(prs.slides._sldIdLst)
    for tf, n in _FOOTERS:
        tf.paragraphs[0].runs[0].text = f"{n:02d} / {total:02d}"


def marker_pill(slide, label, on_dark=False):
    """Small badge telling the presenter whether to run, skim or skip a slide."""
    if not label:
        return
    if on_dark:
        fill, txt = WHITE, ESI_PURPLE
    else:
        fill, txt = MARKERS.get(label, MARKERS["CORE"])
    w = Inches(1.45)
    h = Inches(0.29)
    x = BODY_L + BODY_W - w
    y = Inches(0.22)
    _rect(slide, x, y, w, h, fill, MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    _text(slide, x, y + Inches(0.052), w, Inches(0.22), label, size=9,
          bold=True, color=txt, align=PP_ALIGN.CENTER)


def _band(slide, title, kicker=None, mark=None):
    """Title block on the branded canvas, clear of the logo in the top-left."""
    if kicker:
        _text(slide, TITLE_X, Inches(0.20), TITLE_W, Inches(0.26),
              kicker.upper(), size=10, color=TEAL_DARK, bold=True)
        ty = Inches(0.46)
    else:
        ty = Inches(0.40)
    _text(slide, TITLE_X, ty, TITLE_W, Inches(0.85), title, size=22,
          color=NAVY, font=FONT_H, spacing=1.0)
    _rect(slide, BODY_L, Inches(1.42), BODY_W, Inches(0.03), BAND)
    marker_pill(slide, mark)


LAYOUT_CONTENT = 1   # white canvas, eScience logo in the top-left
LAYOUT_HERO = 0      # blue hero, eScience logo in the bottom-left


def _base(prs, kind="content"):
    """New slide on the branded layout, with the layout placeholders removed."""
    layout = prs.slide_layouts[LAYOUT_HERO if kind == "hero" else LAYOUT_CONTENT]
    slide = prs.slides.add_slide(layout)
    for ph in list(slide.placeholders):
        ph._element.getparent().remove(ph._element)
    return slide


def ask_pill(slide, text, label="ASK THE ROOM"):
    y = Inches(6.28)
    _rect(slide, BODY_L, y, BODY_W, Inches(0.54), AMBER_TINT,
          MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    _text(slide, BODY_L + Inches(0.26), y + Inches(0.15), Inches(1.35),
          Inches(0.28), label, size=9.5, bold=True, color=AMBER_DARK)
    _text(slide, BODY_L + Inches(1.72), y + Inches(0.11),
          BODY_W - Inches(2.1), Inches(0.34), text, size=12.5, color=INK)


# --------------------------------------------------------------------------
# Code rendering
# --------------------------------------------------------------------------
def code_panel(slide, x, y, w, h, lines, size=11.5):
    _rect(slide, x, y, w, h, CODE_BG, MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.025)
    for i, c in enumerate([ESI_BLUE, ESI_AMBER, RGBColor(0xE8, 0xDD, 0xE8)]):
        d = slide.shapes.add_shape(MSO_SHAPE.OVAL, x + Inches(0.22 + i * 0.21),
                                   y + Inches(0.19), Inches(0.105), Inches(0.105))
        d.fill.solid()
        d.fill.fore_color.rgb = c
        d.line.fill.background()
        d.shadow.inherit = False
    tf = _tb(slide, x + Inches(0.26), y + Inches(0.46),
             w - Inches(0.5), h - Inches(0.62))
    first = True
    for ln in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.line_spacing = 1.0
        p.space_after = Pt(0)
        _code_runs(p, ln, size)
    return tf


def _code_runs(p, line, size):
    cut = line.find("#")
    code_part, comment = (line, "") if cut < 0 else (line[:cut], line[cut:])
    if not code_part.strip() and comment:
        r = p.add_run()
        r.text = comment
        r.font.size = Pt(size)
        r.font.name = MONO
        r.font.italic = True
        r.font.color.rgb = CODE_DIM
        return
    lead = code_part[:len(code_part) - len(code_part.lstrip())]
    rest = code_part.strip()
    if lead:
        r0 = p.add_run()
        r0.text = lead
        r0.font.size = Pt(size)
        r0.font.name = MONO
        r0.font.color.rgb = CODE_INK
    if rest:
        m = re.match(r"([A-Za-z_][\w\.\-]*)(.*)", rest, re.S)
        token, tail = (m.group(1), m.group(2)) if m else (rest, "")
        r1 = p.add_run()
        r1.text = token
        r1.font.size = Pt(size)
        r1.font.name = MONO
        r1.font.bold = token in KEYWORDS
        r1.font.color.rgb = TEAL if token in KEYWORDS else CODE_INK
        if tail:
            r2 = p.add_run()
            r2.text = tail
            r2.font.size = Pt(size)
            r2.font.name = MONO
            r2.font.color.rgb = CODE_INK
    if comment:
        r3 = p.add_run()
        r3.text = comment
        r3.font.size = Pt(size)
        r3.font.name = MONO
        r3.font.italic = True
        r3.font.color.rgb = CODE_DIM


# --------------------------------------------------------------------------
# Slide archetypes
# --------------------------------------------------------------------------
def content_slide(prs, title, items, notes="", kicker=None, size=16,
                  space=9, ask=None, mark="CORE", body_h=Inches(4.5)):
    slide = _base(prs)
    _band(slide, title, kicker, mark=mark)
    add_bullets(slide, items, h=body_h, size=size, space=space)
    if ask:
        ask_pill(slide, ask)
    footer(slide)
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide


def statement_slide(prs, kicker, text, sub=None, notes="", mark="CORE"):
    slide = _base(prs)
    _rect(slide, 0, 0, SW, SH, ESI_PURPLE)
    _rect(slide, 0, 0, Inches(0.24), SH, ESI_AMBER)
    _text(slide, Inches(1.05), Inches(1.9), Inches(10.6), Inches(0.32),
          kicker.upper(), size=11, color=ESI_AMBER, bold=True)
    _text(slide, Inches(1.05), Inches(2.38), Inches(11.2), Inches(2.4), text,
          size=36, color=WHITE, font=FONT_H, spacing=1.06)
    if sub:
        _text(slide, Inches(1.07), Inches(4.62), Inches(10.7), Inches(1.8), sub,
              size=15, color=MUTED, spacing=1.16)
    marker_pill(slide, mark, on_dark=True)
    footer(slide, dark=True)
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide


def stat_slide(prs, kicker, number, caption, detail=None, notes="", mark="CORE"):
    slide = _base(prs)
    _rect(slide, 0, 0, SW, SH, ESI_PURPLE)
    _rect(slide, 0, 0, SW, Inches(0.06), ESI_AMBER)
    _text(slide, Inches(1.05), Inches(1.2), Inches(10.6), Inches(0.32),
          kicker.upper(), size=11, color=ESI_AMBER, bold=True)
    _text(slide, Inches(1.0), Inches(1.7), Inches(11.3), Inches(2.1), number,
          size=100, color=WHITE, font=FONT_H)
    _text(slide, Inches(1.07), Inches(3.9), Inches(10.7), Inches(1.0), caption,
          size=19, color=ESI_AMBER, spacing=1.12)
    if detail:
        _text(slide, Inches(1.07), Inches(5.25), Inches(10.7), Inches(1.3),
              detail, size=14, color=MUTED, spacing=1.18)
    marker_pill(slide, mark, on_dark=True)
    footer(slide, dark=True)
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide


def divider_slide(prs, label, title, subtitle, notes="", mark="CORE"):
    """Hero divider. The artwork leaves a clear blue column on the left-middle."""
    slide = _base(prs, kind="hero")
    _text(slide, Inches(2.50), Inches(1.55), Inches(6.3), Inches(0.4),
          label.upper(), size=12, color=ESI_AMBER, bold=True)
    _rect(slide, Inches(2.52), Inches(1.95), Inches(1.3), Inches(0.075),
          ESI_AMBER)
    _text(slide, Inches(2.50), Inches(2.20), Inches(6.3), Inches(1.4), title,
          size=32, color=WHITE, font=FONT_H, spacing=1.02)
    _text(slide, Inches(2.52), Inches(3.65), Inches(6.2), Inches(1.2),
          subtitle, size=14.5, color=MUTED, spacing=1.16)
    marker_pill(slide, mark, on_dark=True)
    footer(slide, dark=True)
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide


def code_slide(prs, title, kicker, code, side_lines, notes="",
               side_title="Read this", caption=None, size=11.5, mark="CORE",
               code_w=Inches(7.55)):
    slide = _base(prs)
    _band(slide, title, kicker, mark=mark)
    code_panel(slide, BODY_L, BODY_TOP, code_w, Inches(4.62), code, size)
    sx = BODY_L + code_w + Inches(0.32)
    sw = BODY_W - code_w - Inches(0.32)
    _text(slide, sx, BODY_TOP + Inches(0.02), sw, Inches(0.3),
          side_title.upper(), size=10.5, color=TEAL_DARK, bold=True)
    add_bullets(slide, side_lines, x=sx, y=BODY_TOP + Inches(0.42), w=sw,
                h=Inches(3.7), size=12.5, space=8)
    if caption:
        _text(slide, sx, Inches(5.55), sw, Inches(0.95), caption, size=11.5,
              color=GREY, italic=True, spacing=1.12)
    footer(slide)
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide


def compare_slide(prs, title, kicker, left, right, notes="",
                  left_title="Before", right_title="After", verdict=None,
                  code_size=11.5, mark="CORE", mono=True):
    slide = _base(prs)
    _band(slide, title, kicker, mark=mark)
    panel_w = Inches(5.75)
    gap = Inches(0.4)
    code_h = Inches(3.1) if verdict else Inches(4.4)
    for i, (ttl, body, accent) in enumerate([
            (left_title, left, RED), (right_title, right, GREEN)]):
        x = BODY_L + i * (panel_w + gap)
        _text(slide, x + Inches(0.04), BODY_TOP, panel_w, Inches(0.3),
              ttl.upper(), size=11, bold=True, color=accent)
        if mono:
            code_panel(slide, x, BODY_TOP + Inches(0.38), panel_w, code_h, body,
                       code_size)
        else:
            _rect(slide, x, BODY_TOP + Inches(0.38), panel_w, code_h, CARD,
                  MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.03)
            add_bullets(slide, body, x=x + Inches(0.3),
                        y=BODY_TOP + Inches(0.62), w=panel_w - Inches(0.6),
                        h=code_h - Inches(0.4), size=13, space=8)
    if verdict:
        y = BODY_TOP + Inches(3.68)
        _rect(slide, BODY_L, y, BODY_W, Inches(0.86), AMBER_TINT,
              MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.13)
        _text(slide, BODY_L + Inches(0.28), y + Inches(0.17),
              BODY_W - Inches(0.56), Inches(0.56), verdict, size=13.5,
              color=INK, bold=True, spacing=1.08)
    footer(slide)
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide


def cards_slide(prs, title, kicker, cards, cols=3, notes="", ask=None,
                accent=TEAL, head_size=13, body_size=12, mark="CORE",
                row_gap=Inches(0.22), col_gap=Inches(0.24)):
    """cards: list of (heading, body) where body is str or list[str]."""
    slide = _base(prs)
    _band(slide, title, kicker, mark=mark)
    rows = ceil(len(cards) / cols)
    card_w = int((BODY_W - col_gap * (cols - 1)) / cols)
    top = BODY_TOP
    bottom = Inches(6.14) if ask else Inches(6.9)
    card_h = int((bottom - top - row_gap * (rows - 1)) / rows)
    for i, (heading, body) in enumerate(cards):
        r, c = divmod(i, cols)
        x = BODY_L + c * (card_w + col_gap)
        y = top + r * (card_h + row_gap)
        _rect(slide, x, y, card_w, card_h, CARD,
              MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
        _rect(slide, x, y, card_w, Inches(0.055), accent)
        _text(slide, x + Inches(0.22), y + Inches(0.2), card_w - Inches(0.44),
              Inches(0.36), heading, size=head_size, bold=True, color=NAVY)
        lines = [body] if isinstance(body, str) else list(body)
        tf = _tb(slide, x + Inches(0.22), y + Inches(0.6),
                 card_w - Inches(0.44), card_h - Inches(0.76))
        firstp = True
        for ln in lines:
            p = tf.paragraphs[0] if firstp else tf.add_paragraph()
            firstp = False
            p.space_after = Pt(4)
            p.line_spacing = 0.96
            mk = p.add_run()
            mk.text = "\u2013  "
            mk.font.size = Pt(body_size - 3)
            mk.font.color.rgb = accent
            mk.font.name = FONT
            rr = p.add_run()
            rr.text = ln
            rr.font.size = Pt(body_size)
            rr.font.name = FONT
            rr.font.color.rgb = GREY
    if ask:
        ask_pill(slide, ask)
    footer(slide)
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide


def table_slide(prs, title, kicker, data, col_widths, notes="", size=11.5,
                header=12, ask=None, height=Inches(4.4), mark="CORE"):
    slide = _base(prs)
    _band(slide, title, kicker, mark=mark)
    total = sum(col_widths)
    table_w = BODY_W - Inches(0.7)
    scaled = [int(w / total * table_w) for w in col_widths]
    gf = slide.shapes.add_table(len(data), len(data[0]), BODY_L + Inches(0.35),
                                BODY_TOP + Inches(0.15), table_w, height)
    table = gf.table
    for i, cw in enumerate(scaled):
        table.columns[i].width = cw
    for r, row in enumerate(data):
        for c, val in enumerate(row):
            cell = table.cell(r, c)
            cell.margin_left = cell.margin_right = Inches(0.1)
            cell.margin_top = cell.margin_bottom = Inches(0.05)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.line_spacing = 0.95
            run = p.add_run()
            run.text = str(val)
            run.font.size = Pt(header if r == 0 else size)
            run.font.name = FONT
            cell.fill.solid()
            if r == 0:
                run.font.bold = True
                run.font.color.rgb = WHITE
                cell.fill.fore_color.rgb = NAVY_SOFT
            else:
                run.font.color.rgb = INK
                cell.fill.fore_color.rgb = WHITE if r % 2 else BAND
    if ask:
        ask_pill(slide, ask)
    footer(slide)
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide


def hands_on_slide(prs, title_, duration, goal, steps, done, tooling, stretch,
                   notes="", mark="CORE"):
    slide = _base(prs)
    _band(slide, title_, "Hands-on \u00B7 your code, not a toy problem", mark=mark)
    _rect(slide, BODY_L, Inches(1.42), BODY_W, Inches(0.03), AMBER)
    _text(slide, Inches(8.55), Inches(0.24), Inches(2.45), Inches(0.3),
          duration, size=12, color=TEAL_DARK, bold=True,
          align=PP_ALIGN.RIGHT)

    left_w = Inches(7.0)
    right_x = BODY_L + left_w + Inches(0.35)
    right_w = BODY_W - left_w - Inches(0.35)

    _rect(slide, BODY_L, BODY_TOP, left_w, Inches(4.62), CARD,
          MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.035)
    _text(slide, BODY_L + Inches(0.32), BODY_TOP + Inches(0.24),
          left_w - Inches(0.64), Inches(0.95), goal, size=13, color=INK,
          spacing=1.12)
    add_bullets(slide, [(s, 0) for s in steps], x=BODY_L + Inches(0.32),
                y=BODY_TOP + Inches(1.28), w=left_w - Inches(0.64),
                h=Inches(3.15), size=12.5, space=8)

    _rect(slide, right_x, BODY_TOP, right_w, Inches(4.62), BLUE_TINT,
          MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.035)
    _text(slide, right_x + Inches(0.28), BODY_TOP + Inches(0.24),
          right_w - Inches(0.56), Inches(0.3), "DEFINITION OF DONE", size=10.5,
          bold=True, color=TEAL_DARK)
    add_bullets(slide, [(d, 0) for d in done], x=right_x + Inches(0.28),
                y=BODY_TOP + Inches(0.62), w=right_w - Inches(0.56),
                h=Inches(2.3), size=12, space=6)
    _text(slide, right_x + Inches(0.28), BODY_TOP + Inches(3.05),
          right_w - Inches(0.56), Inches(0.3), "TOOLING", size=10.5,
          bold=True, color=TEAL_DARK)
    _text(slide, right_x + Inches(0.28), BODY_TOP + Inches(3.36),
          right_w - Inches(0.56), Inches(1.05), tooling, size=11.5, color=GREY,
          spacing=1.06)
    footer(slide)
    if notes:
        slide.notes_slide.notes_text_frame.text = notes + f"\n\nSTRETCH: {stretch}"
    return slide


def title_slide(prs, title, subtitle, meta, notes="", mark="CORE"):
    # Branded blue hero background. The artwork leaves a clear blue column
    # roughly 2.5in-8.8in wide and above 5.2in, which is where all text goes.
    slide = _base(prs, kind="hero")
    _text(slide, Inches(2.50), Inches(1.55), Inches(6.2), Inches(0.34),
          "ONE-HOUR WORKSHOP  \u00B7  TALK + A 15-MINUTE HANDS-ON", size=11.5,
          color=ESI_AMBER, bold=True)
    _text(slide, Inches(2.48), Inches(1.88), Inches(6.3), Inches(1.5), title,
          size=32, color=WHITE, font=FONT_H, spacing=1.04)
    _rect(slide, Inches(2.52), Inches(3.35), Inches(1.35), Inches(0.07),
          ESI_AMBER)
    _text(slide, Inches(2.50), Inches(3.58), Inches(6.2), Inches(0.9),
          subtitle, size=15, color=MUTED, spacing=1.14)
    _text(slide, Inches(2.50), Inches(4.62), Inches(6.3), Inches(0.75), meta,
          size=10.5, color=RGBColor(0xC9, 0xDC, 0xEA), spacing=1.14)
    marker_pill(slide, mark, on_dark=True)
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide


# ==========================================================================
# DECK
# ==========================================================================
TEMPLATE = ("/home/simone/good_coding_pract/"
            "Master PowerPoint Template - Netherlands eScience Center.pptx")
prs = Presentation(TEMPLATE)

# Start from the branded master, without the template's sample slides.
for _sld in list(prs.slides._sldIdLst):
    _rid = _sld.get("{http://schemas.openxmlformats.org/officeDocument/2006/"
                    "relationships}id")
    prs.part.drop_rel(_rid)
    prs.slides._sldIdLst.remove(_sld)

# ==========================================================================
# FRONT MATTER (3 slides, ~4 minutes)
# ==========================================================================
title_slide(
    prs,
    "Reproducible Science in the Age of Vibe Coding",
    "LLMs have made writing code almost free. What is still expensive is being "
    "wrong \u2014 and not being able to tell.",
    "Facilitator: [Your name]  \u00B7  [Institution]  \u00B7  [Date]\n"
    "Built on four Carpentries Incubator lessons, all CC-BY 4.0: Good Practices "
    "in Research Software Development \u00B7 Generative AI for Coding \u00B7 "
    "Reproducible Research through Reusable Code \u00B7 Collaborative Git and GitHub",
    mark="CORE",
    notes="Shown while people arrive. One minute of the four-minute opener.\n"
          "Take a quick show of hands: who codes daily, who already uses an "
          "assistant, who has been bitten by a script that stopped working. That "
          "tells you how much of Part 1 to compress.\n"
          "Say the shape out loud now, including the hands-on: 'there is a "
          "fifteen-minute exercise in the middle where you will fix a script that "
          "runs but lies'. People concentrate better when they know when they get "
          "to type.\n"
          "Housekeeping: every [placeholder] in this deck needs replacing with "
          "your own domain, dataset and institutional policy.",
)

statement_slide(
    prs,
    "Minute 1",
    "It worked on my laptop.",
    "Two years after the paper, a reviewer asks for the same analysis with a "
    "different threshold. The script is 400 lines, with no functions and no "
    "tests, and the data path points at a folder you deleted.\n\n"
    "Nothing here is a coding problem. It is a reproducibility problem \u2014 and "
    "assistants changed the cost of writing code, not the cost of being wrong.",
    mark="CORE",
    notes="Two minutes. This slide is the hook and the thesis at once, so do not "
          "rush it. Tell it as a story, ideally a real one of your own; specific "
          "details land harder than generalities.\n"
          "Do not resolve it. Let the discomfort sit, then say: 'keep this person "
          "in mind \u2014 by the end you will know exactly what they should have done "
          "differently.'\n"
          "If someone argues that models keep improving, agree: a better model "
          "raises the base rate of correct output, but it does not remove the need "
          "to verify.",
)

table_slide(
    prs,
    "The hour at a glance",
    "What we will do, and when you get to type",
    [
        ["Time", "Block", "What happens"],
        ["0:00\u20130:04", "Welcome and the problem",
         "Why reproducibility and AI assistants collide"],
        ["0:04\u20130:12", "Part 1 \u2014 Reproducible by construction",
         "Modules, documentation, one test, version control and CI"],
        ["0:12\u20130:22", "Part 2 \u2014 Vibe coding with LLMs",
         "How assistants work, the three modes, prompting, and the bug that looks fine"],
        ["0:22\u20130:37", "HANDS-ON \u2014 fix a script that runs but lies",
         "Everyone types: diagnose it, prompt an assistant, fix it, then break the fix"],
        ["0:37\u20130:47", "Part 3 \u2014 Risks and guardrails",
         "Analytical reproducibility, ethics, security, and the review checklist"],
        ["0:47\u20130:51", "Wrap-up",
         "The checklist, and what to do on Monday"],
        ["0:51\u20131:00", "Q&A",
         "Anything you want to raise, plus the appendix as reference"],
    ],
    col_widths=[1.2, 3.8, 6.9],
    height=Inches(4.5),
    size=11.5,
    mark="CORE",
    notes="One minute. Point at the hands-on row explicitly and say what they will "
          "produce: a script that prints the right number and a test that proves "
          "it.\n"
          "The badge in the top-right of each slide is for you rather than for the "
          "room: blue is core to the hour, amber means it can be cut if we run "
          "late, grey means it is appendix reference. Say that in one sentence and "
          "carry on.\n"
          "Also say what this hour is NOT: it is not a Git course, not a "
          "tour of every assistant feature, and not a statistics lecture. Those "
          "are in the appendix and in the source lessons.\n"
          "The timings are honest: 51 minutes of programme and nine of Q&A. If you "
          "run late, the wrap-up is the part to compress, not the exercise.",
)

# ==========================================================================
# PART 1 - REPRODUCIBLE BY CONSTRUCTION (5 slides, ~8 minutes)
# ==========================================================================
content_slide(
    prs,
    "What \u201Creproducible\u201D actually means",
    [
        ("Repeat: the same person, on the same machine, gets the same result. "
         "The weakest standard, and the most common thing people mean when they "
         "say \u201Cit works\u201D.", 0),
        ("Reproduce: a different person, on a different machine, gets the same "
         "result. This is what a reviewer is actually asking for.", 0),
        ("Reuse: a stranger extends your analysis without emailing you first. "
         "This is what turns software into a research output.", 0),
        ("The test is concrete: can someone clone your repository, follow the "
         "README, and obtain the numbers in your paper?", 0),
        ("Most published code sits at \u201Crepeat\u201D. Getting to \u201Creproduce\u201D is "
         "mostly structure, not talent \u2014 and structure is what the next three "
         "slides are about.", 0),
    ],
    kicker="Part 1 \u00B7 the standard we are aiming at",
    size=15,
    space=11,
    mark="CORE",
    notes="Ninety seconds. Ask for a show of hands: whose last project would pass "
          "the clone-and-run test? The silence is useful and it is not a "
          "criticism.\n"
          "Plant the phrase 'it runs for me' versus 'it runs for them' \u2014 you will "
          "use it again after the hands-on.\n"
          "This is the only slide in Part 1 that is about principles; the rest are "
          "about the three things that make the test pass.",
)

compare_slide(
    prs,
    "Modular code: the same analysis, ten minutes of work",
    "Part 1 \u00B7 the change that makes everything else possible",
    left=[
        "f = open(\"data/trajectory.csv\")",
        "rows = []",
        "for line in f:",
        "    p = line.strip().split(\",\")",
        "    if len(p) == 4 and p[2] != \"\":",
        "        rows.append(float(p[2]))",
        "total = 0",
        "for r in rows:",
        "    total = total + r",
        "print(total / len(rows))",
        "# ... 90 more lines, and a second",
        "# copy of this loop to get the MSD",
    ],
    right=[
        "DATA = Path(\"data\")",
        "",
        "def read_trajectory(path: Path) -> pd.DataFrame:",
        "    \"\"\"Read the positions; drop missed frames.\"\"\"",
        "    df = pd.read_csv(path)",
        "    return df.dropna(subset=[\"X (\u00b5m)\", \"Y (\u00b5m)\"])",
        "",
        "def diffusion_coefficient(df: pd.DataFrame) -> float:",
        "    \"\"\"Self-diffusion coefficient in \u00b5m\u00b2/s.\"\"\"",
        "    msd = mean_squared_displacement(df)",
        "    slope = np.polyfit(lag_times(df), msd, 1)[0]",
        "    return float(slope / 4.0)",
    ],
    left_title="One script, four jobs",
    right_title="Two functions, two sentences",
    verdict="Limited tasks, descriptive names, one job per function. The payoff is "
            "not elegance \u2014 it is that diffusion_coefficient can now be checked "
            "against a stored value without opening a file.",
    mark="CORE",
    notes="Two minutes. Do not read the code aloud. Point at the shape of the "
          "left panel: one long script, a hard-coded path, two copies of the same "
          "loop.\n"
          "The point to say out loud is the cost: ten minutes. The room assumes a "
          "weekend refactor, and that assumption is why they never start.\n"
          "This slide sets up the hands-on directly: the function you are looking "
          "at is the kind of thing a test can hold on to.",
)

content_slide(
    prs,
    "Documentation: the README answers four questions",
    [
        ("What does it do? Two sentences, no jargon.", 0),
        ("How do I install it? Copy-pasteable, with versions pinned.", 0),
        ("How do I run it? The exact command, including arguments.", 0),
        ("How do I know it worked? The number they should expect.", 0),
        ("That fourth question is the one almost everybody omits, and the one a "
         "reviewer actually needs.", 0),
        ("Comments explain the why, not the what; docstrings describe the "
         "interface. Neither should narrate syntax the code already shows.", 0),
        ("If you write nothing else for a project, write this page.", 0),
    ],
    kicker="Part 1 \u00B7 the landing page",
    size=14.5,
    space=9,
    mark="DEEP DIVE",
    notes="Ninety seconds. Deliver the four questions as four questions, not as "
          "four bullets \u2014 it is a checklist they can remember.\n"
          "The 'expected output' heading is the load-bearing one. It is also the "
          "bridge to the next slide: a test with a stored expected value is that "
          "fourth question, made executable.\n"
          "Cut here first if Part 1 is running long: the last three bullets can "
          "become one sentence.",
)

code_slide(
    prs,
    "The test that makes the rest possible",
    "Part 1 \u00B7 a reproducibility check with a compiler attached",
    code=[
        "# tests/test_analysis.py",
        "import pytest",
        "",
        "from analysis import DATA, diffusion_coefficient, read_trajectory",
        "",
        "# [placeholder] the value your published analysis produced",
        "EXPECTED = 0.49",
        "",
        "def test_d_matches_recorded_value():",
        "    df = read_trajectory(DATA / \"bead_trajectory.csv\")",
        "    assert diffusion_coefficient(df) == pytest.approx(",
        "        EXPECTED, abs=0.05)",
        "",
        "def test_no_missing_frames_survive_loading():",
        "    df = read_trajectory(DATA / \"bead_trajectory.csv\")",
        "    assert not df[\"X (\u00b5m)\"].isna().any()",
    ],
    side_lines=[
        ("Tests catch new errors early \u2014 before a reviewer does.", 0, "\u25B8"),
        ("They let a stranger verify that your install works.", 0, "\u25B8"),
        ("They make refactoring safe \u2014 including AI-assisted refactoring.", 0, "\u25B8"),
        ("TDD is optional. Tests are not.", 0, "\u25B8"),
        ("One stored expected value is worth twenty structural tests.", 0, "\u25B8"),
    ],
    side_title="Why this one matters most",
    caption="Remember this slide. In twenty minutes you will watch a test exactly "
            "like this catch a bug that no reviewer, linter or assistant noticed.",
    mark="CORE",
    size=11,
    notes="Two minutes. This is the single most important slide in the deck and "
          "you will point back to it twice: once after the spot-the-bug slide, "
          "and once during the hands-on debrief.\n"
          "Say the sentence slowly: a test that asserts a recorded value is a "
          "reproducibility check with a compiler attached.\n"
          "EXPECTED is a placeholder on purpose \u2014 every project has its own 'the "
          "number we published'. Ask the room what theirs is.",
)

content_slide(
    prs,
    "Version control and CI: the safety net",
    [
        ("Version control is an unlimited undo button, and it lets many people "
         "work in parallel.", 0),
        ("If it is not in Git, it does not exist. Commit in small, meaningful "
         "steps \u2014 the history is your lab notebook for code.", 0),
        ("Use .gitignore for data, environments, credentials and generated "
         "files. Never commit secrets, and rotate anything that leaks.", 0),
        ("Continuous integration runs your tests on a machine that is not yours, "
         "from a clean checkout, on every push.", 0),
        ("It turns \u201CI ran it on my machine\u201D into a timestamped, linkable "
         "result \u2014 and it is where pinned dependencies get enforced.", 0),
        ("For this workshop it does one more job: it is the reason a bad "
         "assistant edit is recoverable. You can always see the diff, and you "
         "can always revert it.", 0),
    ],
    kicker="Part 1 \u00B7 the last piece of the safety net",
    size=14,
    space=10,
    mark="CORE",
    notes="Ninety seconds. Do not teach Git here \u2014 the audience for this hour "
          "either has it or needs the appendix; the source lesson covers it.\n"
          "The last bullet is the one to land: version control is what makes it "
          "safe to accept an assistant's suggestion, because the change is "
          "visible and reversible.\n"
          "If Part 1 is running long, this slide and the documentation slide are "
          "the two to compress; keep the test slide intact.",
)

# ==========================================================================
# PART 2 - VIBE CODING WITH LLMS (5 slides, ~10 minutes)
# ==========================================================================
content_slide(
    prs,
    "What assistants are, and what they are not",
    [
        ("They combine machine learning, contextual code understanding and "
         "natural language processing. Most are fine-tuned from foundation "
         "models trained on public code and documentation.", 0),
        ("They are context-aware: the current file, other open files, and a "
         "local index of your repository, pulled in on demand (retrieval-"
         "augmented generation).", 0),
        ("They predict the most likely continuation. They optimise for "
         "plausible \u2014 not for correct.", 0),
        ("They learn from your accept and reject decisions, so they adapt to "
         "your style, including your bad habits.", 0),
        ("What they never do: run your code, see your data, or know whether the "
         "result means anything.", 0),
        ("That last line is the whole risk section in one sentence.", 0),
    ],
    kicker="Part 2 \u00B7 a fast, confident, unaccountable co-author",
    size=14,
    space=10,
    mark="CORE",
    notes="Two minutes. Keep the fine-tuning detail to one sentence; the "
          "interesting part for a research audience is 'optimises for plausible, "
          "not for correct'.\n"
          "Draw out the accept/reject feedback loop: it explains why your naming "
          "and comments change the quality of what you get back, and why a sloppy "
          "codebase gets sloppier suggestions.\n"
          "The fourth bullet is why the assistant will fix the obvious bug in the "
          "hands-on and miss the interesting one.",
)

stat_slide(
    prs,
    "Part 2 \u00B7 the number to remember",
    "46.3%",
    "GitHub Copilot produced correct code in 46.3% of cases in one study "
    "(researchers at Bilkent University).",
    "Slightly worse odds than a coin toss. You would not publish a coin toss "
    "without checking it, and you would not merge that code without reading it.\n\n"
    "Newer models have improved the base rate. That changes how often you have "
    "to check \u2014 not whether the check is your job.",
    mark="CORE",
    notes="One minute. Let the number sit on screen for a beat before you speak.\n"
          "Expect the objection 'that study is old'. Agree with the premise, then "
          "make the base-rate point: a better model means you catch less, not that "
          "you stop looking.\n"
          "The line to leave them with: 'the AI wrote it' is not an answer a "
          "reviewer will accept.",
)

table_slide(
    prs,
    "Three modes, three different jobs",
    "Part 2 \u00B7 know which one you are reaching for",
    [
        ["Mode", "Reach for it when\u2026", "The catch"],
        ["Autocomplete",
         "You know roughly what you want and need the typing done: boilerplate, "
         "repetitive patterns, formatting. Fill-in-the-Middle reads the code above "
         "and below the cursor.",
         "Runs passively all day. Only as good as your names and comments \u2014 and it "
         "will happily complete a bad pattern."],
        ["Chat",
         "You want to understand, plan or generate in bulk: explain this function, "
         "write tests, brainstorm edge cases. @-mention functions and files to pin "
         "context.",
         "Conversational confidence is not evidence. It will fluently explain code "
         "it has misread."],
        ["Command",
         "You want a surgical edit on a selection: refactor this loop, add a "
         "docstring, fix this bug. Highlight first, then invoke (Ctrl+I).",
         "A stronger, slower model. Without a selection it writes at the cursor, "
         "and it can change more than you asked for."],
    ],
    col_widths=[1.4, 5.1, 4.9],
    height=Inches(4.5),
    size=11.5,
    mark="CORE",
    notes="Two minutes. This table is reference material \u2014 do not read it aloud. "
          "Demo one cell if the room is warm.\n"
          "The practical rule: autocomplete for volume, chat for understanding, "
          "Command for precision on a selection.\n"
          "In the hands-on most people will use chat, because it is the mode you "
          "can point at a problem. Say that; it saves them fumbling.",
)

compare_slide(
    prs,
    "Prompting: the difference between a diff and a rewrite",
    "Part 2 \u00B7 objective + context + constraints",
    left=[
        "Refactor rawDataTransform",
        "",
        "",
        "# no method specified",
        "# no output contract",
        "# no constraints at all",
        "# so the assistant guesses",
    ],
    right=[
        "Refactor @func:rawDataTransform by turning",
        "the while loop into a for loop, and use the",
        "same output structure as",
        "@func:otherDataTransformer",
        "",
        "# target: which function",
        "# method: while -> for",
        "# contract: match the existing shape",
    ],
    left_title="Bad \u2014 the assistant invents",
    right_title="Good \u2014 the assistant complies",
    verdict="Objective, context, constraints. The same three parts work in every "
            "assistant you will use \u2014 and you will use them in the exercise in a "
            "few minutes.",
    mark="CORE",
    notes="Two minutes. This is the source lesson's own example \u2014 keep it "
          "verbatim so learners recognise it in the material.\n"
          "Name the three missing parts in the bad prompt one at a time, then show "
          "how the good prompt supplies each.\n"
          "Tell them explicitly: the three-part prompt is printed on a slide "
          "during the hands-on, so they do not have to remember it.",
)

code_slide(
    prs,
    "Spot the bug: it runs, the number is wrong",
    "Part 2 \u00B7 sixty seconds, discuss with the person next to you",
    code=[
        "# the assistant \"tidies up\" your conversion",
        "def diffusion_coefficient(df):",
        "    msd = mean_squared_displacement(df)",
        "    slope = np.polyfit(lag_times(df), msd, 1)[0]",
        "    return float(slope / 2)",
        "",
        "",
        "# It runs. It returns a number. It plots fine.",
        "# Nothing raises. Nothing warns.",
    ],
    side_lines=[
        ("The bead moves in the plane, so in 2D, MSD = 4 D t, not 2 D t.", 0, "\u25B8"),
        ("D comes out exactly twice too large, and the curve still looks perfect.", 0, "\u25B8"),
        ("The test from Part 1 catches it: the stored value fails loudly.", 0, "\u25B8"),
        ("Quietly wrong does more damage than loudly broken.", 0, "\u25B8"),
    ],
    side_title="Answer \u2014 after they have guessed",
    caption="Adapted from the lesson's bug-fixing exercise. In the next fifteen "
            "minutes you will meet this same failure mode in your own terminal.",
    mark="CORE",
    size=11,
    notes="Three minutes, and it is the pivot of the whole hour. Do not reveal the "
          "answer for at least 45 seconds \u2014 the argument between neighbours is the "
          "learning.\n"
          "Then generalise: the characteristic failure mode of AI-assisted work is "
          "not the crash, it is the plausible wrong answer.\n"
          "Close the loop explicitly, then hand over: the test from Part 1 is what "
          "catches this, and you are about to see it do exactly that.",
)

# ==========================================================================
# HANDS-ON (5 slides, 15 minutes)
# ==========================================================================
hands_on_slide(
    prs,
    "Fix a script that runs but lies",
    "15 min",
    "You are handed a script that measures how fast a bead diffuses in water. "
    "It crashes. Once it runs, it reports a diffusion coefficient that is wrong "
    "by a factor of twenty. Find out why, with an assistant's help, and prove "
    "the fix with a test.",
    steps=[
        "Run it. Read the error before you touch anything \u2014 and notice that it "
        "is the easy problem.",
        "Look at the data first: the fit uses Frame. Is a frame a time axis, and "
        "is it the one the units claim?",
        "Run the test. Its failure is the most useful information in the room.",
        "Now use the assistant. Ask it to explain before it edits, and read the "
        "whole diff.",
        "Re-run the test, then put the bug back on purpose and check it fails "
        "again.",
    ],
    done=[
        "analysis.py prints about 0.49 \u00b5m\u00b2/s",
        "pytest passes",
        "You can say aloud what the bug was and why the wrong number looked fine",
        "Your prompt is saved beside the code",
    ],
    tooling="The hands-on/ folder: analysis.py, bead_trajectory.csv, "
            "test_analysis.py and README.md. Python with pandas, numpy and "
            "pytest, plus a chat box with an assistant. Work in pairs if you like.",
    stretch="Recover the bead radius from your fitted D with Stokes-Einstein, "
            "r = kT / (6 pi eta D). You should get 0.5 \u00b5m \u2014 say out loud why "
            "that is not a coincidence.",
    mark="CORE",
    notes="The heart of the hour. Fifteen minutes, and three of those are "
          "protected diagnosis time before anyone touches an assistant \u2014 do not "
          "let this become a prompting exercise before people have looked at the "
          "data.\n"
          "Circulate, but do not solve it for anyone. The most common facilitator "
          "error is answering the question instead of asking what the test said.\n"
          "Stop at 13 minutes to run the debrief even if some people have not "
          "finished. The debrief is where the lesson lands; finishing is not the "
          "point.\n"
          "Facilitator notes, timings and fallbacks are in hands-on/FACILITATOR.md.",
)

code_slide(
    prs,
    "Step 1 and 2: run it, then look at the data",
    "Hands-on \u00B7 three minutes before you ask for help",
    code=[
        "# Step 1 - run it, and read the error",
        "$ python analysis.py",
        "FileNotFoundError: [Errno 2] No such file or directory:",
        "  '/Users/yourname/Downloads/bead_trajectory.csv'",
        "# One line to fix. And it teaches you nothing.",
        "",
        "# Step 2 - look at the data before you ask an assistant",
        ">>> import pandas as pd",
        ">>> d = pd.read_csv(\"bead_trajectory.csv\")",
        ">>> d.head()",
        "   Frame  Time (s)  X (\u00b5m)  Y (\u00b5m)",
        "0      0      0.00  31.585  23.723",
        "1      1      0.05  31.645  23.493",
        "2      2      0.10  31.750  23.580",
        "",
        "# Two questions to answer yourself:",
        "#   1. which column is the time axis?",
        "#   2. does analysis.py use that column?",
    ],
    side_lines=[
        ("The crash is a decoy. Fixing it takes one line and teaches nothing.", 0, "\u25B8"),
        ("The real defect survives the fix: the script then runs and reports a "
         "plausible wrong number.", 0, "\u25B8"),
        ("Which column is the time axis? Time (s) \u2014 a frame is not a second.", 0, "\u25B8"),
        ("Does analysis.py use it? Look at the two lines inside "
         "diffusion_coefficient.", 0, "\u25B8"),
        ("Reading the data first is what makes the assistant's answer "
         "checkable rather than persuasive.", 0, "\u25B8"),
    ],
    side_title="Why this order matters",
    caption="Spend three minutes here. The people who inspect the data first get "
            "far more out of the next step.",
    mark="CORE",
    size=10,
    notes="Do not skip this slide. The whole exercise depends on the audience "
          "meeting the real defect themselves, or at least trying to.\n"
          "If you jump straight to prompting you teach them that the assistant is "
          "the oracle, which is the opposite of the hour's thesis.",
)

code_slide(
    prs,
    "The prompt",
    "Hands-on \u00B7 objective, context, constraints",
    code=[
        "Fix analysis.py so that it reports the diffusion",
        "coefficient in \u00b5m\u00b2/s, using the Time (s) column",
        "as the time axis.",
        "",
        "Context: bead_trajectory.csv has columns Frame,",
        "Time (s), X (\u00b5m), Y (\u00b5m). Frames are 0.05 s",
        "apart; Time (s) is the same thing in seconds.",
        "",
        "Constraints: keep the function signatures, keep it",
        "readable, and explain what was wrong. Do not change",
        "test_analysis.py.",
    ],
    side_lines=[
        ("Objective: what to fix, and the unit you want the answer in.", 0, "\u25B8"),
        ("Context: the columns and what they mean. Two sentences is enough.", 0, "\u25B8"),
        ("Constraints: signatures, readability, an explanation, and the test "
         "left alone.", 0, "\u25B8"),
        ("\u201CDo not change the test\u201D is the important one \u2014 it stops the "
         "assistant making the test agree with the bug.", 0, "\u25B8"),
        ("Write your own version first, then compare with this one. The "
         "differences are worth discussing.", 0, "\u25B8"),
    ],
    side_title="The three parts",
    caption="This is the Part 2 recipe, applied to a real task with a real "
            "failing test. Nothing here is special to this exercise.",
    mark="CORE",
    size=11.5,
    notes="Leave this on screen while people work. The objective / context / "
          "constraints split is the same one from the prompting slide, which is "
          "the point: it is a habit, not a trick.\n"
          "If the room is fast, ask them to write the prompt themselves first and "
          "compare with yours afterwards.",
)

content_slide(
    prs,
    "Step 3: verify, then break it",
    [
        ("Run pytest. The fixed version reports 0.4905 \u00b5m\u00b2/s: Stokes-Einstein "
         "for a 1 \u00b5m bead, and inside the test's 0.49 \u00B1 0.05.", 0),
        ("Now put the bug back \u2014 fit against the frame number again. The test "
         "must fail. If it does not, your test is decoration.", 0),
        ("Ask for the diff, not the new file, and read every line before you "
         "accept it.", 0),
        ("Commit the test and the code together. That 0.49 is now your stored "
         "expected value, and it will guard this result for years.", 0),
        ("Two traps: multiplying the frame slope by 20 is right for the wrong "
         "reason, and dividing by 2 instead of 4 is the 1D formula.", 0),
        ("Keep the prompt beside the code. Future you will want to know how that "
         "number was produced.", 0),
    ],
    kicker="Hands-on \u00B7 the part that makes it science",
    size=14,
    space=10,
    mark="CORE",
    notes="Two minutes. This slide is the transferable part. The bug is specific "
          "to this dataset; 'break the fix on purpose' is a habit that applies to "
          "every result they will ever produce. Say that sentence out loud.\n"
          "The 0.4905 is the payoff: it is Stokes-Einstein for a 1 um bead in "
          "water, so the stored value is a physical result rather than a magic "
          "number. Say that before you move on.\n"
          "The commit line matters: it is how today's fifteen minutes turns into a "
          "permanent guard rail rather than an anecdote.",
)

cards_slide(
    prs,
    "Debrief: what did the assistant get wrong?",
    "Hands-on \u00B7 two minutes, out loud",
    [
        ("The decoy",
         ["Most assistants fix the path immediately and stop.",
          "Did it ever mention the time axis unprompted?"]),
        ("The explanation",
         ["Did it explain before editing?",
          "If it did, was the explanation actually correct?"]),
        ("Frames or seconds",
         ["Fitting against Frame gives 0.0245 \u00b5m\u00b2/s.",
          "The unit is \u00b5m\u00b2 per frame, and nothing complains."]),
        ("Right answer, wrong reason",
         ["Multiplying that slope by 20 passes this test.",
          "It breaks the moment someone drops a frame."]),
        ("The test that mattered",
         ["The linearity test passes either way. Only the",
          "stored value could catch a unit error."]),
        ("Next week",
         ["What is the one thing you will do differently?",
          "Take one answer, out loud, before you move on."]),
    ],
    cols=3,
    body_size=12,
    mark="CORE",
    notes="Do not skip the debrief to let people finish. The exercise is the "
          "vehicle; this conversation is the payload.\n"
          "Ask for hands, take three or four answers, and land on the 'the test "
          "that mattered' card \u2014 that is the sentence the whole hour exists to "
          "deliver.\n"
          "Then transition: 'so what do you do about it?' That is Part 3.",
)

# ==========================================================================
# PART 3 - RISKS AND GUARDRAILS (5 slides, ~10 minutes)
# ==========================================================================
content_slide(
    prs,
    "The risk that is not in the code",
    [
        ("Everything so far keeps the code honest. None of it keeps the "
         "analysis honest.", 0),
        ("Software reproducibility asks: does it run, and does it give the same "
         "numbers?", 0),
        ("Analytical reproducibility asks: is this the analysis you said you "
         "would do?", 0),
        ("Generating a hundred model specifications used to cost a week. With an "
         "assistant it costs an afternoon.", 0),
        ("So the failure mode changes. It is rarely a wrong line of code. It is a "
         "defensible-looking choice, made because it produced the result you "
         "wanted.", 0),
        ("Your test suite cannot catch it: every specification you tried passed "
         "its tests.", 0),
        ("The fix is procedural, not technical: decide the analysis before you "
         "look, and keep a log of every specification you tried \u2014 including the "
         "ones you rejected.", 0),
    ],
    kicker="Part 3 \u00B7 the risk that tests cannot catch",
    size=13.5,
    space=9,
    mark="CORE",
    notes="Three minutes. This is the most important slide in Part 3 for a "
          "research audience, and the one they will not have heard before. Do not "
          "compress it away.\n"
          "The framing to use: everything until now was about whether the code "
          "does what you think. This slide is about whether the analysis does what "
          "you said.\n"
          "The garden of forking paths is not new; what is new is that the "
          "assistant makes walking it cheap. If you have a story from your own "
          "field about a defensible analysis choice that changed a conclusion, "
          "tell it here.",
)

cards_slide(
    prs,
    "Six ethical failure modes, and the practical version of each",
    "Part 3 \u00B7 ethics",
    [
        ("Bias",
         ["Training data encodes who is missing",
          "Practical: compare output against the population you actually study"]),
        ("Error rates",
         ["Random and systematic errors, at scale",
          "Practical: assume the base rate applies to your next suggestion"]),
        ("Transparency",
         ["The rationale is a black box",
          "Practical: you cannot defend a line you cannot explain"]),
        ("Privacy",
         ["Many assistants retain your input",
          "Practical: know the retention policy before you paste"]),
        ("Authorship",
         ["Ownership of generated code is unsettled",
          "Practical: check your journal and funder policy"]),
        ("Accountability",
         ["No assistant signs your paper",
          "Practical: you are the author of record for every committed line"]),
    ],
    cols=3,
    body_size=12,
    mark="CORE",
    notes="Two minutes. One breath per card; read only the right-hand line, which "
          "is the actionable half.\n"
          "If you are behind schedule, keep the six headings and the "
          "accountability line and drop the rest.\n"
          "On authorship: the copyright status of AI-generated content is "
          "genuinely unsettled. Say that rather than inventing a rule.",
)

content_slide(
    prs,
    "Security and protecting your data",
    [
        ("A Stanford study found that users relying on assistants wrote less "
         "secure code \u2014 while being more confident that it was secure.", 0),
        ("Insecure suggestions: the models learn from insecure code too. "
         "Unsanitised input becomes injection; a missing check becomes an "
         "exploit.", 0),
        ("Data exposure: your proprietary code or participant data, processed on "
         "someone else's servers. Many assistants retain what you send them.", 0),
        ("Hallucinated and outdated APIs, and suggested dependencies that may be "
         "unmaintained or vulnerable next week.", 0),
        ("Classify before you choose the tool: what may leave your machine, and "
         "what may never leave it?", 0),
        ("Never paste credentials, API keys, participant data or anything under "
         "an ethics agreement. For sensitive work, prefer a local or offline "
         "model.", 0),
        ("Guardrails: review every diff, run scanners (Snyk, SonarQube) in CI, "
         "encrypt, restrict access, and check your tool's retention policy.", 0),
    ],
    kicker="Part 3 \u00B7 security",
    size=13,
    space=8,
    mark="DEEP DIVE",
    body_h=Inches(4.4),
    ask="Which of these could your project absorb without anyone noticing? That "
        "one is your priority.",
    notes="Two minutes. Lead with the Stanford finding \u2014 the confidence gap is "
          "the interesting part, not the insecurity.\n"
          "The data-classification question is the one with immediate practical "
          "value for most groups. Have your institution's approved-tool list "
          "ready; people will ask.\n"
          "Note the division of labour: tests protect you against behaviour you "
          "thought to check; scanners protect you against classes of issue you did "
          "not think of. You need both.",
)

table_slide(
    prs,
    "Every risk has a practice behind it",
    "Part 3 \u00B7 the bridge back to Part 1",
    [
        ["Risk", "How it bites you", "The practice that fixes it"],
        ["Non-deterministic output",
         "You cannot regenerate last month's analysis",
         "Commit the code; record the model, version and prompt"],
        ["Silent behavioural drift",
         "A tidy refactor quietly changes the numbers",
         "Tests with stored expected values, plus an equivalence assert"],
        ["Environment drift",
         "It works today, but not on the reviewer's machine",
         "Pinned dependencies, a lock file, and CI on every push"],
        ["Lost provenance",
         "Nobody can tell what was generated versus written",
         "Small commits with meaningful messages; prompts kept in-repo"],
        ["Over-trust",
         "Less secure, less understood code, held more confidently",
         "Read every diff, run scanners, keep a second pair of eyes"],
        ["Analytical drift",
         "A defensible choice made because it gave the answer you wanted",
         "Decide the analysis before you look, and log what you tried"],
    ],
    col_widths=[2.4, 4.4, 4.7],
    height=Inches(4.5),
    size=11.5,
    mark="CORE",
    notes="Two minutes. Do not read the table. Walk it as pairs and make the "
          "point that the right-hand column is entirely from Part 1 \u2014 plus the "
          "procedural one you added in the analytical slide.\n"
          "This is the argument of the hour in one image. If you cut anything "
          "else from Part 3, do not cut this.\n"
          "If the room is senior, ask which row they disagree with. That "
          "discussion is worth more than the next slide.",
)

table_slide(
    prs,
    "A review checklist for AI-assisted changes",
    "Part 3 \u00B7 use this in the pull request",
    [
        ["Question to ask of the diff", "Why it matters"],
        ["Does it do exactly what I asked, and nothing else?",
         "Scope creep is the most common assistant failure mode"],
        ["Do I understand every line?",
         "You cannot defend code you cannot explain"],
        ["Do the tests still pass, and did I add one for the new behaviour?",
         "A green suite that never covered the change proves nothing"],
        ["Is there an obvious security issue \u2014 input validation, secrets, SQL, shell?",
         "Models are trained on insecure code as well as secure code"],
        ["Are new dependencies pinned, current, and appropriately licensed?",
         "A suggested package can be unmaintained, vulnerable, or badly licensed"],
        ["Did I decide the analysis before I looked at the result?",
         "Otherwise the result chose the analysis"],
        ["Have I recorded the model, version and prompt?",
         "Without it, the change is not reproducible"],
        ["Would I be comfortable if this diff were shown in review?",
         "The simplest and most reliable test there is"],
    ],
    col_widths=[6.2, 5.3],
    height=Inches(4.7),
    size=11,
    mark="CORE",
    notes="Two minutes. Present it as a pull-request checklist people can paste "
          "into a template \u2014 it is the most likely slide to be used on Monday.\n"
          "Cut here if short: keep questions 1, 2, 3 and 8.\n"
          "The final question compresses everything else into a single instinct, "
          "so say it out loud.",
)

# ==========================================================================
# WRAP-UP (4 slides, ~4 minutes)
# ==========================================================================
table_slide(
    prs,
    "The reproducible vibe-coding checklist",
    "Wrap-up \u00B7 the one slide to hand out",
    [
        ["Before you prompt", "While you code", "Before you commit"],
        ["Git repository with a README",
         "Prompt with objective, context and constraints",
         "Run the full test suite"],
        ["Pinned environment and lock file",
         "Generate tests and docstrings, not just code",
         "Read every diff line by line"],
        ["Function and module boundaries decided",
         "Prove refactors equivalent before accepting them",
         "Record model, version and prompt used"],
        ["A decision on data sensitivity and tool choice",
         "Never paste secrets or sensitive data",
         "Commit in small, meaningful steps"],
        ["The expected result written down",
         "Ask the assistant to explain what you did not write",
         "Push, and let CI verify it independently"],
        ["One test that would fail if the result changed",
         "Keep the prompt beside the code",
         "Open a pull request, however small"],
    ],
    col_widths=[3.8, 3.8, 3.8],
    height=Inches(4.65),
    size=11,
    mark="CORE",
    ask="Pick one row and say it out loud. That is the row you are committing to "
        "this week \u2014 one is enough.",
    notes="Ninety seconds. Walk it as a workflow, left to right, not as a list of "
          "rules.\n"
          "Tell them explicitly that this is the slide to photograph, and that it "
          "is available as a checklist file in the hands-on folder.\n"
          "The ask pill is the point of the whole hour: a public commitment to one "
          "concrete habit. Give them thirty seconds of silence to choose, then "
          "take three or four answers.",
)

cards_slide(
    prs,
    "An adoption plan that survives a real workload",
    "Wrap-up \u00B7 do not try all of this on Monday",
    [
        ("Day one",
         ["git init and a README, even if it is four lines.",
          "Split your current script into two named functions.",
          "Write one test with a stored expected value.",
          "Add a .gitignore and commit the lock file."]),
        ("Week one",
         ["Add the CI workflow from Part 1.",
          "Do further work on branches, and open one pull request.",
          "Write down your group's rule for what may be pasted",
          "into an AI tool, and what may not."]),
        ("Month one",
         ["Decide one analysis before you look at the result, and log it.",
          "Add the review checklist to your pull-request template.",
          "Run the reusability check: ask a colleague to clone and run it.",
          "Teach one colleague the test-with-a-stored-value trick."]),
    ],
    cols=3,
    body_size=12,
    mark="DEEP DIVE",
    notes="Ninety seconds. This slide answers the unspoken question, 'what do I do "
          "on Monday?'\n"
          "Emphasise sequencing: the day-one items are tiny on purpose. Teams fail "
          "at this by trying to adopt everything at once.\n"
          "Cut here if you are behind: keep the day-one column and say the rest is "
          "in the appendix.",
)

statement_slide(
    prs,
    "Minute 51",
    "You can have both.",
    "Speed and reproducibility are not in tension. Speed without verification is "
    "just a faster way to be wrong \u2014 and the practices in Part 1 are what let "
    "you accept an assistant's help, hand the work to a stranger, and still sign "
    "your name to the result.",
    mark="CORE",
    notes="Thirty seconds, then hand over to questions. Return to the researcher "
          "from the opening slide: what separates them from the person who "
          "survives the reviewer's email is not talent. It is ten minutes of "
          "structure, one honest test, and a recorded prompt.",
)

content_slide(
    prs,
    "Resources, and where all of this came from",
    [
        ("Good Practices in Research Software Development \u2014 eScience Center / "
         "The Carpentries", 0, "\u25B8"),
        ("carpentries-incubator.github.io/good-practices-lesson", 1),
        ("Generative AI for Coding \u2014 The Carpentries Incubator", 0, "\u25B8"),
        ("carpentries-incubator.github.io/gen-ai-coding", 1),
        ("Reproducible Research through Reusable Code \u2014 dependencies, licensing, "
         "FAIR, citation and DOIs", 0, "\u25B8"),
        ("carpentries-incubator.github.io/reproducible-research-through-reusable-code-in-1-day",
         1),
        ("Collaborative Version Control with Git and GitHub \u2014 branches, pull "
         "requests, code review, forks", 0, "\u25B8"),
        ("carpentries-incubator.github.io/collaborative-git-and-github-lesson", 1),
        ("The hands-on materials, the project checklist and the facilitator notes "
         "are in the hands-on/ folder. All four lessons are CC-BY 4.0.", 0, "\u25B8"),
        ("Next step: one row of the checklist, one real project, this week.", 0, "\u25B8"),
    ],
    kicker="Thank you \u00B7 questions",
    size=13,
    space=8,
    body_h=Inches(4.5),
    mark="CORE",
)
prs.slides[-1].notes_slide.notes_text_frame.text = (
    "Put the four URLs in the chat before you start taking questions.\n"
    "Keep answers short and land each one on a practice rather than an opinion. "
    "If someone asks 'should we use AI at all?', redirect to the risk table: the "
    "answer is a practice, not a verdict.\n"
    "If nobody asks anything, use the discussion questions in the appendix: "
    "'which row of the checklist will be hardest in your team, and why?' That "
    "always gets a response.\n"
    "Anything you cannot answer goes in the appendix slides \u2014 point at them "
    "rather than improvising."
)

# ==========================================================================
# APPENDIX (14 slides) - the material we cut, condensed
# ==========================================================================
divider_slide(
    prs,
    "Appendix",
    "The material we cut",
    "Fourteen slides covering everything that did not fit the hour. Nothing here "
    "needs to be presented \u2014 hand it out, or point people at it afterwards.",
    mark="OPTIONAL",
    notes="Signal clearly that the talk is over. If you continue past this slide "
          "you are in office-hours mode, and people should feel free to leave.\n"
          "Tell them what is in here and why: the collaboration material, the "
          "dependency and data practices, the assistant deep dives, and the "
          "troubleshooting guide. It is reference, not agenda.",
)

table_slide(
    prs,
    "The 60-minute run sheet",
    "Appendix \u00B7 for whoever runs this next",
    [
        ["Time", "Block", "Slides"],
        ["0:00\u20130:04", "Welcome, the problem, the hour at a glance",
         "The three front-matter slides"],
        ["0:04\u20130:12", "Part 1 \u2014 Reproducible by construction",
         "What reproducible means, modular code, the README, the stored-value "
         "test, version control and CI"],
        ["0:12\u20130:22", "Part 2 \u2014 Vibe coding with LLMs",
         "What assistants are, 46.3%, the three modes, prompting, spot the bug"],
        ["0:22\u20130:37", "HANDS-ON",
         "Brief, run it and inspect the data, the prompt, verify and break it, "
         "debrief"],
        ["0:37\u20130:47", "Part 3 \u2014 Risks and guardrails",
         "Analytical reproducibility, ethics, security and data, the risk table, "
         "the review checklist"],
        ["0:47\u20130:51", "Wrap-up",
         "Checklist, adoption plan, closing"],
        ["0:51\u20131:00", "Q&A", "The appendix as reference"],
        ["Cut first", "If you are running late",
         "The three DEEP DIVE slides: documentation, security, and the adoption "
         "plan \u2014 in that order"],
        ["Never cut", "If you are running very late",
         "The stored-value test, spot the bug, and the hands-on"],
    ],
    col_widths=[1.4, 4.4, 6.0],
    height=Inches(4.8),
    size=11,
    mark="OPTIONAL",
    notes="This slide exists so the session can be run by someone else. Print it "
          "with FACILITATOR.md.\n"
          "The 'cut first' row is the useful one. The pattern: cut the slides that "
          "describe practices, never the ones that demonstrate them. The test "
          "slide, the bug slide and the exercise are what people remember.",
)

table_slide(
    prs,
    "Dependencies: three students, three repositories",
    "Appendix \u00B7 we travel three years into the future and re-run their code",
    [
        ["Repository", "What you find", "Will it re-run in three years?"],
        ["Student A \u2014 README only",
         "The README lists some of the main libraries that were used, with no "
         "versions anywhere.",
         "Almost certainly not. You will get whatever version is current today, "
         "and the API will have moved."],
        ["Student B \u2014 unpinned",
         "A requirements.txt listing scipy, numpy, sympy, click \u2014 and two "
         "dependencies pulled straight from a repository at @main.",
         "No. Unpinned names drift, and @main is a moving target: the code you "
         "get is today's, not theirs."],
        ["Student C \u2014 the time capsule",
         "A requirements.txt with exact versions (scipy==1.3.1, numpy==1.16.4, "
         "\u2026) and git dependencies pinned to a tag.",
         "Most likely yes. This is what a time capsule of dependencies looks "
         "like."],
    ],
    col_widths=[2.5, 5.2, 4.3],
    height=Inches(4.3),
    size=11.5,
    mark="OPTIONAL",
    ask="The difference between repository B and repository C is about ten "
        "characters per line. Which one is yours?",
    notes="Cut from Part 1 for time, and the best exercise in the whole deck for "
          "a longer session. Run it as a discussion: read the three repositories "
          "out loud and ask which they would bet on, and why. Do not reveal C "
          "immediately.\n"
          "The deeper point: B is the trap. It looks like good practice \u2014 there "
          "is a requirements.txt! \u2014 but it records nothing reproducible.\n"
          "From the 'Reproducible research through reusable code' lesson.",
)

content_slide(
    prs,
    "Data and workflow reproducibility",
    [
        ("Treat raw data as read-only. Never edit it in place, and never in "
         "Excel \u2014 it silently reformats dates and gene names.", 0),
        ("Have one command that goes from raw data to every figure and number in "
         "the paper.", 0),
        ("Set your random seeds explicitly, and record them with the result.", 0),
        ("Prefer scripts for the final pipeline; notebooks are excellent for "
         "exploration and poor as a pipeline.", 0),
        ("Use a workflow tool (Make, Snakemake, targets) when the order of steps "
         "matters \u2014 which is always.", 0),
        ("Version your data: a DOI, a checksum, or at least a file recording "
         "where it came from and when.", 0),
        ("Publish the data in a repository rather than in the code repository, "
         "and link to it. If you cannot share it, ship dummy data with the same "
         "structure so the code still runs.", 0),
    ],
    kicker="Appendix \u00B7 cut from Part 1",
    size=13.5,
    space=9,
    mark="OPTIONAL",
    notes="Handout slide. The two bullets that matter most are 'raw data is "
          "read-only' and 'one command reproduces every number'.\n"
          "The Excel warning is worth a sentence in the live session if you have "
          "a spare minute: it is the most common accidental data corruption in "
          "research, and it is invisible in the diff.",
)

content_slide(
    prs,
    "Collaborating: branches, pull requests and code review",
    [
        ("A branch is an independent line of development. Create one for each "
         "piece of work: git switch -c add-tests. Keep main always working.", 0),
        ("The centralized workflow, for internal collaborators: open an issue, "
         "branch, commit and push, open a pull request that says \u201CCloses #1\u201D, "
         "get a review, address the comments, merge.", 0),
        ("For anyone outside your group, use the fork flow instead: fork, clone "
         "your fork, branch, push to the fork, and open a pull request upstream.", 0),
        ("Code review: review the diff, not the person. Ask questions rather than "
         "issuing verdicts, be specific, and say what is good as well as what is "
         "wrong.", 0),
        ("Review small changes. A thousand-line pull request gets a rubber stamp, "
         "which is what small commits and branches buy you.", 0),
        ("For AI-assisted changes the same checklist applies, with extra "
         "attention to scope creep and security.", 0),
        ("This is the practice that makes the review checklist from Part 3 "
         "enforceable rather than aspirational.", 0),
    ],
    kicker="Appendix \u00B7 the whole of the collaboration act, condensed",
    size=13,
    space=8,
    mark="OPTIONAL",
    body_h=Inches(4.4),
    notes="Cut from the one-hour version as a whole act. It is the strongest "
          "argument for a longer session, and the easiest thing to hand out.\n"
          "The line to keep if you only say one thing: do code reviews, and be "
          "constructive in them. The source Git lesson is explicit about that.\n"
          "If the room is a research group rather than individuals, this is the "
          "material they most need and least have.",
)

content_slide(
    prs,
    "Licence it, cite it, get a DOI",
    [
        ("A licence is essential so that others can reuse and adapt your work. "
         "Without one, the default is all rights reserved and nobody may legally "
         "use it \u2014 not even your own field.", 0),
        ("choosealicense.com helps you pick. A common permissive choice is the "
         "Apache License 2.0; check what your institution recommends.", 0),
        ("Add a CITATION.cff so people can cite the software, and link your "
         "repository to Zenodo so each release gets its own DOI.", 0),
        ("A DOI prevents link rot and makes the exact version you used "
         "retrievable \u2014 which is what reproducibility actually requires. A "
         "repository URL is not a citation.", 0),
        ("Data needs a licence too, usually CC-BY or CC0, and it needs a "
         "repository: that is what gives it a DOI and keeps it findable.", 0),
        ("FAIR software (fair-software.eu, fairsoftwarechecklist.net) is a "
         "checklist of the things above, not a standard you pass or fail.", 0),
        ("Check your dependencies' licences as well: they constrain what you may "
         "do with your own project.", 0),
    ],
    kicker="Appendix \u00B7 cut from Part 1",
    size=13,
    space=8,
    mark="OPTIONAL",
    body_h=Inches(4.4),
    notes="Handout slide. Non-technical audiences find this genuinely new, so "
          "expect questions if you do present it.\n"
          "The strongest argument: a repository URL is not a citation. URLs rot, "
          "repositories get renamed, and main moves.\n"
          "Copyright and licensing of AI-generated content is a separate and "
          "genuinely unsettled question \u2014 say that rather than guessing.",
)

content_slide(
    prs,
    "Context awareness: what the assistant actually sees",
    [
        ("Rather than fine-tuning a model on your codebase, assistants use "
         "retrieval-augmented generation to fetch relevant snippets on demand.", 0),
        ("Default context: the current file, other open files, and an index of "
         "your local repository, including files you do not have open.", 0),
        ("Context pinning lets you attach files, directories or specific "
         "functions for persistent reference. Pin sparingly \u2014 too much dilutes "
         "relevance and slows the tool down.", 0),
        ("Sensible things to pin: module definitions, internal framework "
         "examples, interface files, and the test file for the class you are "
         "testing.", 0),
        ("The reproducibility consequence: what you get back depends on what was "
         "open and pinned at the time, and that state is invisible in the "
         "committed code.", 0),
        ("Which is why provenance matters: record the model, the version and the "
         "prompt alongside the result.", 0),
    ],
    kicker="Appendix \u00B7 cut from Part 2",
    size=13.5,
    space=9,
    mark="OPTIONAL",
    notes="Cut from Part 2 for time, but it is the mechanism that explains the "
          "provenance risk, so mention it in one sentence if you can.\n"
          "It also explains why assistants are better on popular libraries than "
          "on your in-house code \u2014 unless you pin it.",
)

compare_slide(
    prs,
    "Optimise, then prove equivalence",
    "Appendix \u00B7 cut from Part 2",
    left=[
        "avg_int = []",
        "for i in range(df.shape[0]):",
        "    avg_int.append(",
        "        df.iloc[i][\"Average\"]",
        "        - df.iloc[i][\"Interpolated\"]",
        "    )",
        "",
        "df[\"Avg-Int\"] = avg_int",
    ],
    right=[
        "df[\"Avg-Int_opt\"] = (",
        "    df[\"Average\"] - df[\"Interpolated\"]",
        ")",
        "",
        "# prove it, do not assume it",
        "assert df[\"Avg-Int\"].equals(",
        "    df[\"Avg-Int_opt\"]",
        ")",
    ],
    left_title="Row-wise loop",
    right_title="Vectorised \u2014 same numbers",
    verdict="Ask for the optimisation, then ask for the proof. An assistant that "
            "cannot produce a passing assertion has not finished the job.",
    mark="OPTIONAL",
    notes="Cut from Part 2. The lesson's own worked example: the vectorised "
          "version is faster and more memory-efficient because it uses pandas' "
          "vectorised operations.\n"
          "The load-bearing habit is the assert. Without it you have a "
          "nicer-looking function and no evidence that the numbers are unchanged.",
)

content_slide(
    prs,
    "The tool is non-deterministic. The result must not be.",
    [
        ("Same prompt, different code. The model version changes under you. Your "
         "context changes with whichever files happen to be open. Nothing in the "
         "committed code records any of it.", 0),
        ("Reproducibility is not a property of the assistant. It is a property of "
         "what you commit.", 0),
        ("So record provenance for anything that matters: the model, its version, "
         "the date, and the prompt that produced it.", 0),
        ("Keep the prompts in the repository, beside the code they produced. "
         "Commit the code, not the conversation \u2014 chat history is not "
         "documentation.", 0),
        ("Re-run and re-verify. Do not trust a green result from a session you no "
         "longer have.", 0),
        ("For publications, describe the tool and version in the methods section, "
         "just as you would describe any other instrument.", 0),
        ("If your institution has a disclosure policy, follow it \u2014 and if it does "
         "not have one, that is a good reason to write it.", 0),
    ],
    kicker="Appendix \u00B7 cut from Part 3",
    size=13,
    space=8,
    mark="OPTIONAL",
    body_h=Inches(4.4),
    notes="The intellectual centre of the risk material, cut only for time. If "
          "you have two spare minutes in Part 3, this is the slide to add back "
          "instead of the ethics cards.\n"
          "Question to put to the room if you do present it: 'your methods "
          "section says the analysis was performed in Python. What else does it "
          "need to say?'",
)

cards_slide(
    prs,
    "The guardrails, in the order they pay off",
    "Appendix \u00B7 cut from Part 3",
    [
        ("Validate before you trust",
         ["Rigorous tests, CI, and scanners in the pipeline.",
          "Break a test once to prove it has teeth."]),
        ("Review collectively",
         ["One reviewer catches what one author misses.",
          "Open a pull request, even in a team of two."]),
        ("Protect the data",
         ["Classify first; never paste secrets or participant data;",
          "use offline or local models for sensitive work."]),
        ("Document the provenance",
         ["Commit history, prompt logs, model name and version,",
          "so the analysis can still be described in five years."]),
        ("Make it reusable",
         ["A licence, a README, a citation file and a DOI.",
          "That is what turns your code into a citable output."]),
        ("Write the policy down",
         ["Team rules, plus frameworks such as the ACM Code of Ethics",
          "and the European Commission's trustworthy-AI guidelines."]),
    ],
    cols=3,
    body_size=12,
    mark="OPTIONAL",
    notes="Cut from the wrap-up for time. Ordered by return on effort: testing "
          "and review first, policy last.\n"
          "If the room is a group that needs to agree a policy, present this one "
          "and ask them to name the guardrail they will adopt first.",
)

cards_slide(
    prs,
    "When it goes wrong: a troubleshooting guide",
    "Appendix \u00B7 the six problems people actually hit",
    [
        ("\u201CIt keeps inventing our internal functions\u201D",
         ["The model has never seen your private code.",
          "Pin the module or a stub file, add type hints",
          "and docstrings, and refer to it with @-mentions."]),
        ("\u201CIt rewrote my whole file\u201D",
         ["git restore, then work on a branch.",
          "Select the block before you invoke Command,",
          "and re-prompt with a narrower scope."]),
        ("\u201CThe tests pass but the number is wrong\u201D",
         ["Passing tests only prove what you asserted.",
          "You need a stored expected value \u2014 exactly what",
          "you wrote in the hands-on."]),
        ("\u201CIt suggests APIs that no longer exist\u201D",
         ["Its training data has a cutoff. Pin the version",
          "in your context and state it in the prompt:",
          "\u201Cusing pandas 2.2\u201D."]),
        ("\u201CMy colleague gets different output\u201D",
         ["Same prompt, different model version or context.",
          "Record model, version and pinned context \u2014 that",
          "missing state is the variable."]),
        ("\u201CIt is slow and suggests irrelevant code\u201D",
         ["Too much pinned context dilutes relevance.",
          "Unpin, close unrelated files, and reduce the",
          "indexed scope."]),
    ],
    cols=3,
    body_size=11.5,
    mark="OPTIONAL",
    notes="The practical slide people photograph. Keep it in the appendix and "
          "tell them it is there \u2014 it answers the 'but what do I do when' "
          "questions you will not have time for in the hour.",
)

cards_slide(
    prs,
    "The prompt cookbook",
    "Appendix \u00B7 patterns worth stealing",
    [
        ("Specify the contract",
         ["\u201CReturn a DataFrame with columns",
          "date, mean, n \u2014 sorted by date.\u201D",
          "Ambiguity is what it fills with guesses."]),
        ("Give one example",
         ["\u201CFor input [1, 2, 3] it should return 6.\u201D",
          "One concrete example removes",
          "most of the ambiguity."]),
        ("Ask for the test too",
         ["\u201CWrite the function and a pytest test",
          "covering empty input and duplicates.\u201D",
          "You get both artefacts at once."]),
        ("Ask it to explain first",
         ["\u201CExplain what this function does and list",
          "the assumptions it makes, before editing.\u201D",
          "This is the prompt from the hands-on."]),
        ("Iterate in small steps",
         ["One change per prompt, run the tests,",
          "then ask for the next change.",
          "Big prompts produce big unreadable diffs."]),
        ("Re-prompt, do not patch",
         ["If the output is wrong, say what was wrong",
          "and ask again \u2014 do not hand-edit and move on.",
          "You will learn what the tool needs."]),
    ],
    cols=3,
    body_size=12,
    mark="OPTIONAL",
    notes="Cut from Part 2 for time; the prompting slide in the main flow carries "
          "the essential idea.\n"
          "Hand this out rather than presenting it. Point at 'ask it to explain "
          "first', because that is the prompt they used in the exercise.",
)

code_slide(
    prs,
    "The reproducible project checklist",
    "Appendix \u00B7 copy this into your repository",
    code=[
        "# Reproducible project checklist",
        "",
        "- [ ] Git repository, with a readable commit history",
        "- [ ] README: what it does, install, run, expected output",
        "- [ ] LICENSE, and a CITATION.cff",
        "- [ ] Dependencies recorded with versions (lock file)",
        "- [ ] Environment rebuilds from the lock file, in CI",
        "- [ ] No credentials anywhere in the history",
        "- [ ] Functions with descriptive names and docstrings",
        "- [ ] Raw data treated as read-only",
        "- [ ] One command reproduces every number in the paper",
        "- [ ] A test with a stored expected value",
        "- [ ] CI runs the tests on every push",
        "- [ ] The analysis decided before the result was seen",
        "- [ ] Model, version and prompt recorded for AI-assisted steps",
        "- [ ] A DOI for the release you cite",
    ],
    side_lines=[
        ("Save it as CHECKLIST.md and tick as you go.", 0, "\u25B8"),
        ("Not every box applies to every project. Skip one with a reason rather "
         "than silently.", 0, "\u25B8"),
        ("The last four boxes are the ones that would not have appeared on a "
         "checklist written five years ago.", 0, "\u25B8"),
        ("It also works as a pull-request template: put the relevant lines in "
         "the description.", 0, "\u25B8"),
    ],
    side_title="How to use it",
    caption="The whole hour in one file. If you only take one artefact away, take "
            "this one.",
    mark="OPTIONAL",
    size=10.5,
    notes="Handout slide, and the most likely thing to be actually used after the "
          "session.\n"
          "The source lessons' project checklist is the basis; the last four "
          "lines are the additions that come from the AI-assisted workflow.",
)

content_slide(
    prs,
    "Discussion questions, and where to read more",
    [
        ("Which of your current projects would fail the \u201Ca stranger clones it "
         "and gets your numbers\u201D test \u2014 and why?", 0),
        ("What is the single practice you would have to add first to change that "
         "answer?", 0),
        ("Who reviews your code today? If nobody does, who could?", 0),
        ("What would your institution's policy need to say about data, disclosure "
         "and review?", 0),
        ("Where in your workflow is an assistant genuinely most useful, and where "
         "is it least useful?", 0),
        ("If a reviewer asked you to justify one line an assistant wrote, could "
         "you do it?", 0),
        ("Further reading: the four Carpentries lessons named on the resources "
         "slide, plus the Turing Way's licensing chapter, the ACM Code of Ethics, "
         "and the European Commission's guidelines on trustworthy AI.", 0),
    ],
    kicker="Appendix \u00B7 for the room",
    size=13.5,
    space=9,
    mark="OPTIONAL",
    notes="Use as much time here as you have left. These work as a whole-room "
          "discussion, as a think-pair-share, or as a written exit ticket.\n"
          "If nobody speaks first, answer question 3 yourself with a real example "
          "from your own team. It always unlocks the room.",
)

out = "/home/simone/good_coding_pract/reproducible_science_vibe_coding.pptx"
finalize_footers()
prs.save(out)
print(f"Saved {out} with {len(prs.slides._sldIdLst)} slides")
