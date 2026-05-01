from __future__ import annotations
import re
import pdfplumber
from models.briefing import MELItem


def parse_mel(pages: list[str], pdf_path: str | None = None) -> list[MELItem]:
    mel_page_idx: int | None = None
    for i, page in enumerate(pages[:10]):
        if "MEL/CDL INFORMATION" in page:
            mel_page_idx = i
            break

    if mel_page_idx is None or pdf_path is None:
        return []

    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[mel_page_idx].extract_text(layout=True) or ""

    if "MEL/CDL INFORMATION" not in text:
        return []

    section = text[text.index("MEL/CDL INFORMATION"):]
    end = re.search(r"\*{5,}", section[20:])
    if end:
        section = section[:20 + end.start()]

    lines = section.split("\n")

    desc_col = 0
    remark_col = 0
    header_idx = -1
    for i, line in enumerate(lines):
        dm = re.search(r"DESCRIPTION", line)
        rm = re.search(r"REMARK", line)
        if dm and rm:
            desc_col = dm.start()
            remark_col = rm.start()
            header_idx = i
            break

    if not desc_col:
        return []

    body_lines: list[str] = []
    for i, line in enumerate(lines):
        if i <= header_idx + 1:
            continue
        if line.strip():
            body_lines.append(line)

    ref_pattern = re.compile(r"(\d{2}-\d{2}-\d{2}[A-Z]?)")
    blocks: list[tuple[str, list[str], list[str]]] = []

    for line in body_lines:
        padded = line.ljust(remark_col + 40)
        desc_part = padded[desc_col:remark_col].strip()
        remark_part = padded[remark_col:].strip()

        if remark_part.startswith("REF-"):
            continue

        ref_area = line[:desc_col]
        m = ref_pattern.search(ref_area)
        if m:
            blocks.append((m.group(1), [], []))

        if blocks:
            if desc_part:
                blocks[-1][1].append(desc_part)
            if remark_part:
                blocks[-1][2].append(remark_part)

    items: list[MELItem] = []
    for ref, desc_parts, remark_parts in blocks:
        items.append(MELItem(
            reference=ref,
            description=" ".join(desc_parts),
            remark=" ".join(remark_parts) if remark_parts else None,
        ))

    return items
