"""Builds the downloadable PDF report (ReportLab, pure Python)."""
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DISCLAIMER = ("The highlighted region shows areas that contributed to the model's prediction. "
              "It is not a confirmed tumor boundary or medical diagnosis.")

_styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=_styles["Title"], fontSize=18, textColor=colors.HexColor("#1e3a8a"), spaceAfter=6)
H2 = ParagraphStyle("H2", parent=_styles["Heading2"], fontSize=12, textColor=colors.HexColor("#1e40af"), spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle("Body", parent=_styles["BodyText"], fontSize=9.5, leading=13)
SMALL = ParagraphStyle("Small", parent=BODY, fontSize=8, leading=10, textColor=colors.HexColor("#64748b"))
CELL = ParagraphStyle("Cell", parent=BODY, fontSize=8.5, leading=11)
BANNER = ParagraphStyle("Banner", parent=BODY, backColor=colors.HexColor("#fffbeb"),
                        borderColor=colors.HexColor("#fde68a"), borderWidth=0.8, borderPadding=6,
                        textColor=colors.HexColor("#92400e"))
REPORT = ParagraphStyle("Report", parent=BODY, fontSize=8.5, leading=11.5,
                        backColor=colors.HexColor("#f8fafc"), borderPadding=6)


def _p(text, style=BODY):
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), style)


def _img(path, max_w, max_h):
    try:
        with PILImage.open(path) as im:
            w, h = im.size
        scale = min(max_w / w, max_h / h)
        return Image(path, width=w * scale, height=h * scale)
    except Exception:
        return _p("(image unavailable)", SMALL)


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(2 * cm, 1.2 * cm, "Research and educational decision-support output. Not a medical diagnosis.")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build_report_pdf(*, case_code, patient_ref, predicted_class, confidence, probabilities,
                     model_version, is_placeholder, report_text, review_status, assessment,
                     next_steps, doctors, overlay_path, original_path) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.8 * cm, bottomMargin=2 * cm,
                            title=f"{case_code} report", author="NeuroScan XAI")
    s = []
    s.append(Paragraph("Brain MRI Decision-Support Report", H1))
    s.append(_p("AI-generated draft — requires professional review. Research and educational use only.", BANNER))
    s.append(Spacer(1, 8))

    info = [["Case", case_code], ["Patient reference", patient_ref],
            ["Model version", model_version], ["Review status", review_status.replace("_", " ")],
            ["Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")]]
    t = Table([[_p(a, CELL), _p(b, CELL)] for a, b in info], colWidths=[4 * cm, 12.5 * cm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                           ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9"))]))
    s.append(t)

    if assessment:
        s.append(Paragraph("Symptom questionnaire", H2))
        txt = (f"Symptom indicator: {assessment['level'].upper()} "
               f"(score {assessment['score']} of {assessment['max_score']}). "
               "This is a simple rule-based indicator, not a diagnosis.")
        s.append(_p(txt))
        if assessment["red_flags"]:
            s.append(_p("Warning-sign symptoms reported: " +
                        ", ".join(f.replace("_", " ") for f in assessment["red_flags"]) + ".", BODY))

    s.append(Paragraph("Model result", H2))
    if is_placeholder:
        s.append(_p("*** Untrained demo/placeholder model - this result has NO clinical meaning. ***", BANNER))
        s.append(Spacer(1, 4))
    s.append(_p(f"Predicted class: {predicted_class}    Confidence: {confidence * 100:.1f}%"))
    rows = [[_p("Class", CELL), _p("Probability", CELL)]] + [
        [_p(k, CELL), _p(f"{v * 100:.1f}%", CELL)]
        for k, v in sorted(probabilities.items(), key=lambda kv: -kv[1])]
    pt = Table(rows, colWidths=[6 * cm, 3 * cm], hAlign="LEFT")
    pt.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9"))]))
    s.append(Spacer(1, 4))
    s.append(pt)

    s.append(Paragraph("Explainability (Grad-CAM)", H2))
    imgs = Table([[_img(original_path, 7.5 * cm, 7.5 * cm), _img(overlay_path, 7.5 * cm, 7.5 * cm)],
                  [_p("Original MRI", SMALL), _p("Grad-CAM overlay", SMALL)]],
                 colWidths=[8.2 * cm, 8.2 * cm])
    s.append(imgs)
    s.append(_p(DISCLAIMER, BANNER))

    s.append(Paragraph("Report text", H2))
    s.append(_p(report_text, REPORT))

    s.append(Paragraph("Suggested next steps", H2))
    for step in next_steps:
        s.append(_p("• " + step["text"]))

    if doctors:
        s.append(Paragraph("Suggested specialists", H2))
        head = [_p(h, CELL) for h in ("Name", "Degree", "Speciality", "Phone", "Location")]
        rows = [head] + [[
            _p(d["full_name"], CELL), _p(d["degree"], CELL), _p(d["specialization"], CELL),
            _p(d["phone"], CELL), _p(", ".join(x for x in (d["hospital"], d["city"]) if x), CELL),
        ] for d in doctors]
        dt = Table(rows, colWidths=[3.2 * cm, 4.6 * cm, 2.6 * cm, 2.8 * cm, 3.4 * cm], repeatRows=1)
        dt.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                                ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        s.append(dt)
        if any(d.get("is_demo") for d in doctors):
            s.append(_p("Specialist entries are sample/demo data for demonstration only.", SMALL))

    doc.build(s, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
