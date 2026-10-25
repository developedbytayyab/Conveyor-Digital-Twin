"""PDF and CSV report export helpers."""
from io import BytesIO, StringIO
from datetime import datetime, timezone
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def csv_bytes(data: pd.DataFrame) -> bytes:
    return data.to_csv(index=False).encode("utf-8")


def pdf_report(data: pd.DataFrame) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="Conveyor Digital Twin Report")
    styles = getSampleStyleSheet()
    anomalies = int(data["is_anomaly"].sum()) if "is_anomaly" in data else 0
    critical = int((data["severity"] == "Critical").sum()) if "severity" in data else 0
    story = [Paragraph("Conveyor Digital Twin — Simulation Report", styles["Title"]),
             Paragraph("Generated: " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), styles["Normal"]), Spacer(1, 12),
             Paragraph(f"Samples: {len(data)} | Detected anomalies: {anomalies} | Critical events: {critical}", styles["Heading2"]), Spacer(1, 10)]
    cols = [c for c in ["timestamp", "temperature_c", "vibration_mm_s", "motor_current_a", "belt_speed_m_s", "is_anomaly", "severity"] if c in data]
    rows = [[str(c) for c in cols]] + [[str(v)[:22] for v in row] for row in data[cols].tail(18).itertuples(index=False, name=None)]
    table = Table(rows, repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#26384a")), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                               ("GRID", (0,0), (-1,-1), .35, colors.grey), ("FONTSIZE", (0,0), (-1,-1), 7),
                               ("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("Note: This report uses simulated data and is not a safety certification or a real-machine diagnosis.", styles["Italic"]))
    doc.build(story)
    return buf.getvalue()
