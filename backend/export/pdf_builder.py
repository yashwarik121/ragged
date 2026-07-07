"""
export/pdf_builder.py — Generate a styled PDF report using ReportLab.

The PDF has three sections:
  1. CHEAT SHEET — abstract, key insights, flashcards, entities, timeline
  2. REFERENCE — claims, statistics, evidence passages
  3. OPINION REPORT — executive brief, analysis, so-what, counterpoint
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import EXPORT_DIR
from database import crud

log = logging.getLogger(__name__)

# ── Colour palette ───────────────────────────────────────────────────
_BLACK = colors.HexColor("#1a1a1a")
_ACCENT = colors.HexColor("#2d5f8a")
_LIGHT_GREY = colors.HexColor("#f2f2f2")
_WHITE = colors.white

# ── Base styles ──────────────────────────────────────────────────────
_styles = getSampleStyleSheet()


def _style(name: str, **kw) -> ParagraphStyle:
    """Create a named ParagraphStyle with sensible defaults."""
    defaults = {
        "fontName": "Courier",
        "fontSize": 10,
        "leading": 14,
        "textColor": _BLACK,
        "alignment": TA_LEFT,
    }
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)


TITLE_STYLE = _style("RTitle", fontName="Courier-Bold", fontSize=28, alignment=TA_CENTER, leading=36)
SUBTITLE_STYLE = _style("RSub", fontName="Courier", fontSize=12, alignment=TA_CENTER, textColor=_ACCENT)
HEADING_STYLE = _style("RH1", fontName="Courier-Bold", fontSize=16, leading=22, textColor=_ACCENT, spaceAfter=10)
SUBHEADING_STYLE = _style("RH2", fontName="Courier-Bold", fontSize=12, leading=16, spaceAfter=6)
BODY_STYLE = _style("RBody", alignment=TA_JUSTIFY, spaceAfter=6)
SMALL_STYLE = _style("RSmall", fontSize=8, leading=10, textColor=colors.grey)
LABEL_STYLE = _style("RLabel", fontName="Courier-Bold", fontSize=10, textColor=_ACCENT)


# ──────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────

def _safe(text) -> str:
    """Escape XML-sensitive characters for ReportLab paragraphs."""
    if text is None:
        return ""
    s = str(text)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return s


def _section_header(story: list, title: str) -> None:
    story.append(Spacer(1, 12))
    story.append(Paragraph(title, HEADING_STYLE))
    story.append(Spacer(1, 4))


def _sub_header(story: list, title: str) -> None:
    story.append(Spacer(1, 8))
    story.append(Paragraph(title, SUBHEADING_STYLE))


def _body(story: list, text: str) -> None:
    if text:
        story.append(Paragraph(_safe(text), BODY_STYLE))


def _ensure_list(val) -> list:
    """Coerce a value that might be a JSON string into a list."""
    if isinstance(val, str):
        try:
            val = json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return []
    return val if isinstance(val, list) else []


def _ensure_dict(val) -> dict:
    if isinstance(val, str):
        try:
            val = json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return {}
    return val if isinstance(val, dict) else {}


# ──────────────────────────────────────────────────────────────────────
# Title page
# ──────────────────────────────────────────────────────────────────────

def _title_page(story: list, doc_name: str) -> None:
    story.append(Spacer(1, 2.5 * inch))
    story.append(Paragraph("R A G G E D", TITLE_STYLE))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Document Intelligence Engine", SUBTITLE_STYLE))
    story.append(Spacer(1, 0.6 * inch))
    story.append(Paragraph(_safe(doc_name), _style("DocName", fontName="Courier-Bold", fontSize=14, alignment=TA_CENTER)))
    story.append(Spacer(1, 0.3 * inch))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(now, _style("Date", fontSize=10, alignment=TA_CENTER, textColor=colors.grey)))
    story.append(PageBreak())


# ──────────────────────────────────────────────────────────────────────
# Section 1: Cheat sheet
# ──────────────────────────────────────────────────────────────────────

def _cheatsheet_section(story: list, data: dict) -> None:
    _section_header(story, "1 &mdash; CHEAT SHEET")

    # Abstract
    _sub_header(story, "Abstract")
    _body(story, data.get("abstract", "N/A"))

    # Key insights
    insights = _ensure_list(data.get("key_insights", []))
    if insights:
        _sub_header(story, "Key Insights")
        for i, item in enumerate(insights, 1):
            sent = item.get("sentence", item) if isinstance(item, dict) else str(item)
            story.append(Paragraph(f"{i}. {_safe(sent)}", BODY_STYLE))

    # Flashcards (table)
    flashcards = _ensure_list(data.get("flashcards", []))
    if flashcards:
        _sub_header(story, "Flashcards")
        table_data = [["Term", "Definition"]]
        for fc in flashcards:
            term = fc.get("term", "") if isinstance(fc, dict) else str(fc)
            defn = fc.get("definition", "") if isinstance(fc, dict) else ""
            # Truncate long definitions
            if len(defn) > 200:
                defn = defn[:200] + "…"
            table_data.append([_safe(term), _safe(defn)])

        t = Table(table_data, colWidths=[1.5 * inch, 4.5 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), _ACCENT),
                    ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
                    ("FONTNAME", (0, 0), (-1, 0), "Courier-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("LEADING", (0, 0), (-1, -1), 11),
                    ("BACKGROUND", (0, 1), (-1, -1), _LIGHT_GREY),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(t)

    # Entities
    entities = _ensure_dict(data.get("entities", {}))
    if entities:
        _sub_header(story, "Entities")
        for label, ents in entities.items():
            ents_list = _ensure_list(ents)
            if ents_list:
                story.append(
                    Paragraph(
                        f"<b>{_safe(label)}:</b> {_safe(', '.join(str(e) for e in ents_list[:20]))}",
                        BODY_STYLE,
                    )
                )

    # Timeline
    timeline = _ensure_list(data.get("timeline", []))
    if timeline:
        _sub_header(story, "Timeline")
        story.append(Paragraph(_safe(" → ".join(str(t) for t in timeline[:30])), BODY_STYLE))

    story.append(PageBreak())


# ──────────────────────────────────────────────────────────────────────
# Section 2: Reference
# ──────────────────────────────────────────────────────────────────────

def _reference_section(story: list, data: dict) -> None:
    _section_header(story, "2 &mdash; REFERENCE")

    # Claims
    claims = _ensure_list(data.get("claims", []))
    if claims:
        _sub_header(story, f"Claims ({len(claims)})")
        for c in claims[:30]:  # cap for PDF length
            sent = c.get("sentence", c) if isinstance(c, dict) else str(c)
            page = c.get("page", "?") if isinstance(c, dict) else "?"
            story.append(Paragraph(f"&bull; {_safe(sent)} <i>[p.{page}]</i>", BODY_STYLE))

    # Statistics
    stats = _ensure_list(data.get("statistics", []))
    if stats:
        _sub_header(story, f"Statistics ({len(stats)})")
        for s in stats[:30]:
            sent = s.get("sentence", s) if isinstance(s, dict) else str(s)
            page = s.get("page", "?") if isinstance(s, dict) else "?"
            story.append(Paragraph(f"&bull; {_safe(sent)} <i>[p.{page}]</i>", BODY_STYLE))

    # Evidence passages
    passages = _ensure_list(data.get("evidence_passages", []))
    if passages:
        _sub_header(story, f"Evidence Passages ({len(passages)})")
        for ep in passages[:15]:
            text = ep.get("text", ep) if isinstance(ep, dict) else str(ep)
            page = ep.get("page", "?") if isinstance(ep, dict) else "?"
            # Truncate very long passages
            if len(text) > 400:
                text = text[:400] + "…"
            story.append(
                Paragraph(
                    f"<i>[p.{page}]</i> {_safe(text)}",
                    _style("Evidence", fontSize=9, leading=12, spaceAfter=6),
                )
            )

    story.append(PageBreak())


# ──────────────────────────────────────────────────────────────────────
# Section 3: Opinion report
# ──────────────────────────────────────────────────────────────────────

def _report_section(story: list, data: dict) -> None:
    _section_header(story, "3 &mdash; OPINION REPORT")

    _sub_header(story, "Executive Brief")
    _body(story, data.get("executive_brief", "Not generated."))

    _sub_header(story, "Critical Analysis")
    analysis = data.get("critical_analysis", {})
    if isinstance(analysis, str):
        _body(story, analysis)
    elif isinstance(analysis, dict):
        _body(story, analysis.get("text", str(analysis)))
    else:
        _body(story, str(analysis))

    _sub_header(story, "So What")
    _body(story, data.get("so_what", "N/A"))

    _sub_header(story, "Counterpoint")
    _body(story, data.get("dissenting_opinion", "N/A"))

    score = data.get("confidence_score", 0.0)
    story.append(Spacer(1, 16))
    story.append(
        Paragraph(
            f"<b>Confidence Score:</b> {score:.0%}",
            _style("Conf", fontName="Courier-Bold", fontSize=12, textColor=_ACCENT),
        )
    )


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────

def build_pdf(doc_id: int) -> str:
    """
    Build a styled PDF for *doc_id* and return its absolute file path.
    """
    doc = crud.get_document(doc_id)
    doc_name = doc.filename if doc else f"Document {doc_id}"

    cheatsheet = crud.get_cheatsheet(doc_id) or {}
    reference = crud.get_reference(doc_id) or {}
    report = crud.get_report(doc_id) or {}

    filename = f"ragged_report_{doc_id}.pdf"
    filepath = os.path.join(EXPORT_DIR, filename)

    pdf = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    story: list = []

    _title_page(story, doc_name)
    _cheatsheet_section(story, cheatsheet)
    _reference_section(story, reference)
    _report_section(story, report)

    pdf.build(story)
    log.info("PDF built: %s", filepath)
    return filepath
