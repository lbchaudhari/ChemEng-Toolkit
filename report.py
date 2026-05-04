"""Generate a calculation PDF report using ReportLab."""
from __future__ import annotations
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)


PRIMARY  = colors.HexColor("#0F2C4A")
SECOND   = colors.HexColor("#234A78")
ACCENT   = colors.HexColor("#E7F0F7")
BORDER   = colors.HexColor("#DCE3EB")
MUTED    = colors.HexColor("#6A7480")


def _styles():
    base = getSampleStyleSheet()
    s = {
        "h1":    ParagraphStyle("h1", parent=base["Heading1"],
                                textColor=PRIMARY, fontSize=18, leading=22,
                                spaceAfter=4),
        "h2":    ParagraphStyle("h2", parent=base["Heading2"],
                                textColor=SECOND, fontSize=12, leading=16,
                                spaceBefore=10, spaceAfter=4),
        "body":  ParagraphStyle("body", parent=base["BodyText"],
                                fontSize=10, leading=14),
        "muted": ParagraphStyle("muted", parent=base["BodyText"],
                                fontSize=9, leading=12, textColor=MUTED),
        "small": ParagraphStyle("small", parent=base["BodyText"],
                                fontSize=9, leading=12),
    }
    return s


def _table(data, col_widths=None, header=True):
    style = TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])
    if header:
        style.add("BACKGROUND", (0, 0), (-1, 0), ACCENT)
        style.add("TEXTCOLOR",  (0, 0), (-1, 0), SECOND)
        style.add("FONT",       (0, 0), (-1, 0), "Helvetica-Bold", 9)
    return Table(data, colWidths=col_widths, style=style, hAlign="LEFT")


def build_pdf(spec, calc_id, inputs, results, notes, datasheet=None):
    """Return PDF bytes for one calculation."""
    buf = io.StringIO if False else io.BytesIO()  # noqa
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"ChemEng Report - {spec.get('title', calc_id)}",
        author="ChemEng Toolkit",
    )
    s = _styles()
    story = []

    # Header
    story.append(Paragraph("ChemEng Toolkit – Calculation Report", s["h1"]))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        s["muted"]))
    story.append(Spacer(1, 8))

    # Calculation metadata
    story.append(_table(
        [
            ["Calculator", spec.get("title", calc_id)],
            ["Category",   spec.get("category", "")],
            ["ID",         calc_id],
            ["Description", spec.get("description", "")],
        ],
        col_widths=[35 * mm, 130 * mm], header=False,
    ))

    # Inputs
    story.append(Paragraph("Inputs", s["h2"]))
    rows = [["Parameter", "Symbol", "Value", "Unit"]]
    label_map = {ip["name"]: ip for ip in spec.get("inputs", [])}
    for ip in spec.get("inputs", []):
        v = inputs.get(ip["name"], ip.get("default", ""))
        rows.append([
            ip.get("label", ip["name"]),
            ip["name"],
            str(v),
            ip.get("unit", ""),
        ])
    story.append(_table(rows, col_widths=[70 * mm, 25 * mm, 45 * mm, 25 * mm]))

    # Results
    story.append(Paragraph("Results", s["h2"]))
    if results:
        rows = [["Quantity", "Value", "Unit"]]
        for r in results:
            rows.append([
                str(r.get("label", "")),
                str(r.get("value", "")),
                str(r.get("unit", "")),
            ])
        story.append(_table(rows, col_widths=[90 * mm, 50 * mm, 25 * mm]))
    else:
        story.append(Paragraph("(no results)", s["muted"]))

    # Datasheet
    if datasheet:
        for section in datasheet:
            title = section.get("title", "Datasheet")
            story.append(Paragraph(title, s["h2"]))
            rows = section.get("rows", [])
            if rows:
                ncols = max(len(r) for r in rows)
                norm = [list(r) + [""] * (ncols - len(r)) for r in rows]
                if ncols == 2:
                    widths = [80 * mm, 85 * mm]
                elif ncols == 3:
                    widths = [70 * mm, 50 * mm, 45 * mm]
                else:
                    widths = None
                story.append(_table(norm, col_widths=widths, header=False))

    # Notes / formulas
    if notes:
        story.append(Paragraph("Formulas & Notes", s["h2"]))
        for n in notes:
            story.append(Paragraph(f"• {n}", s["body"]))

    # Footer note
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        "This report is generated by ChemEng Toolkit. Verify values "
        "against authoritative references before use in design.",
        s["muted"],
    ))

    doc.build(story)
    return buf.getvalue()
