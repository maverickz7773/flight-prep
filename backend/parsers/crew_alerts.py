from __future__ import annotations
import re
from models.briefing import CrewAlert


def parse_crew_alerts(pages: list[str]) -> list[CrewAlert]:
    alerts_text = None
    for page in pages:
        if "QR ALERT/BULLETIN" in page or "CREW ALERT" in page:
            alerts_text = page
            break

    if not alerts_text:
        return []

    alerts: list[CrewAlert] = []

    for m in re.finditer(
        r"(CO\d+/\d{2})\s+(?:SUBJECT[:\s]*)?(.+?)(?=\nCO\d+/\d{2}|={5,}|CB\d+|Page\s+\d+|\Z)",
        alerts_text,
        re.DOTALL,
    ):
        ref = m.group(1)
        body = m.group(2).strip()
        lines = body.split("\n")
        subject = lines[0].strip() if lines else ref
        text = "\n".join(lines[1:]).strip() if len(lines) > 1 else subject

        alerts.append(CrewAlert(
            reference=ref,
            subject=subject,
            text=text,
        ))

    for m in re.finditer(
        r"(CB\d+(?:/\d{2})?)\s+[-–]\s*(.+?)(?=\n={5,}|\nCB\d+|\Z)",
        alerts_text,
        re.DOTALL,
    ):
        ref = m.group(1)
        body = m.group(2).strip()
        lines = body.split("\n")
        subject = lines[0].strip()
        text = "\n".join(lines[1:]).strip() if len(lines) > 1 else subject

        alerts.append(CrewAlert(
            reference=ref,
            subject=subject,
            text=text,
        ))

    return alerts
