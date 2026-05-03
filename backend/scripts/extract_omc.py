"""Extract all aerodrome briefings from OM C.pdf into omc_briefings.json.

Usage:
    cd backend && source venv/bin/activate
    python3 scripts/extract_omc.py "../OM C.pdf"

Re-run whenever OM C is updated (new revision).
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

import pdfplumber


SECTIONS = [
    "GENERAL",
    "COMPANY POLICY",
    "AIR TRAFFIC CONTROL",
    "ARRIVAL PROCEDURES",
    "GROUND MANEUVERING",
    "DEPARTURE PROCEDURES",
    "MISCELLANEOUS",
    "DESTINATION ALTERNATES",
]

SECTION_KEYS = {
    "GENERAL": "general",
    "COMPANY POLICY": "company_policy",
    "AIR TRAFFIC CONTROL": "atc",
    "ARRIVAL PROCEDURES": "arrival_procedures",
    "GROUND MANEUVERING": "ground_maneuvering",
    "DEPARTURE PROCEDURES": "departure_procedures",
    "MISCELLANEOUS": "miscellaneous",
    "DESTINATION ALTERNATES": "destination_alternates",
}

HEADER_RE = re.compile(
    r"^\d+\.\d+\.\d+\.\d+\.\d+\s+.+?\((\w{4})/\w{3}\)\s*[-–—]\s*(?:.*?[-–—]\s*)?CATEGORY\s*[-–—]?\s*([A-Z])",
    re.MULTILINE,
)

END_OF_GROUP_RE = re.compile(r"^End of group\b", re.MULTILINE)

PAGE_HEADER_RE = re.compile(
    r"^6 Aerodrome and Route Briefings\nOperations Manual Part C\n.*\n",
    re.MULTILINE,
)

PAGE_FOOTER_RE = re.compile(r"^\d+\s+\w+\s+\d{4}\s+\d+\.\d+\s+P\s+\d+\s*$", re.MULTILINE)

APPLICABLE_SECTION_RE = re.compile(
    r"Applicable to:.*?\n(" + "|".join(re.escape(s) for s in SECTIONS) + r")\n",
    re.DOTALL,
)


def extract_pages(pdf_path: str) -> str:
    """Extract all pages and concatenate, stripping page headers/footers."""
    pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            if i % 200 == 0:
                print(f"  Reading page {i+1}/{total}...", file=sys.stderr)
            text = page.extract_text() or ""
            text = PAGE_HEADER_RE.sub("", text)
            text = PAGE_FOOTER_RE.sub("", text)
            pages.append(text.strip())
    return "\n".join(pages)


def extract_name_from_general(general_text: str) -> str | None:
    """Extract aerodrome name from GENERAL section."""
    m = re.search(r"Name of Aerodrome:\s*(.+)", general_text)
    if m:
        return m.group(1).strip().rstrip(".")
    return None


def parse_aerodrome_block(block: str) -> dict[str, str | None]:
    """Parse a single aerodrome block into sections."""
    result: dict[str, str | None] = {}

    splits = APPLICABLE_SECTION_RE.split(block)

    current_section = None
    for i, part in enumerate(splits):
        part_stripped = part.strip()
        if part_stripped in SECTIONS:
            current_section = part_stripped
        elif current_section:
            content = part_stripped
            content = re.sub(r"Applicable to:.*$", "", content, flags=re.MULTILINE).strip()
            content = END_OF_GROUP_RE.sub("", content).strip()
            content = re.sub(
                r"^\d+\.\d+\.\d+\.\d+\.\d+\s+.+?\(\w{4}/\w{3}\).*$",
                "",
                content,
                flags=re.MULTILINE,
            ).strip()

            if content.upper() == "NIL" or not content:
                result[SECTION_KEYS[current_section]] = None
            else:
                result[SECTION_KEYS[current_section]] = content

            current_section = None

    return result


def extract_all(pdf_path: str) -> dict:
    """Extract all aerodrome briefings from OM C PDF."""
    print("Extracting text from PDF...", file=sys.stderr)
    full_text = extract_pages(pdf_path)
    print(f"Total text length: {len(full_text):,} characters", file=sys.stderr)

    briefings: dict[str, dict] = {}

    headers = list(HEADER_RE.finditer(full_text))
    print(f"Found {len(headers)} aerodrome headers", file=sys.stderr)

    for i, match in enumerate(headers):
        icao = match.group(1)
        category = match.group(2)

        start = match.start()
        if i + 1 < len(headers):
            end = headers[i + 1].start()
        else:
            end = len(full_text)

        block = full_text[start:end]

        end_marker = END_OF_GROUP_RE.search(block)
        if end_marker:
            block = block[: end_marker.start()]

        sections = parse_aerodrome_block(block)

        name = extract_name_from_general(sections.get("general") or "")

        entry = {
            "name": name or icao,
            "category": category,
            **{k: sections.get(k) for k in SECTION_KEYS.values()},
        }

        has_content = any(v for k, v in sections.items())
        if icao not in briefings or (has_content and not any(
            v for k, v in briefings[icao].items() if k not in ("name", "category")
        )):
            briefings[icao] = entry

    return briefings


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/extract_omc.py <path-to-OM-C.pdf>", file=sys.stderr)
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"Error: {pdf_path} not found", file=sys.stderr)
        sys.exit(1)

    briefings = extract_all(pdf_path)
    print(f"\nExtracted {len(briefings)} aerodromes", file=sys.stderr)

    output_path = Path(__file__).parent.parent / "data" / "omc_briefings.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(briefings, f, indent=2, ensure_ascii=False)

    print(f"Written to {output_path}", file=sys.stderr)

    sample = list(briefings.keys())[:10]
    print(f"Sample airports: {', '.join(sample)}", file=sys.stderr)


if __name__ == "__main__":
    main()
