#!/usr/bin/env python3
"""Build FAQ JSON from FAQ_Sause_eV_Website_Pflege.xlsx.

No external dependencies required.
"""

from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
import xml.etree.ElementTree as ET

NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

ROOT = Path(__file__).resolve().parents[1]
SOURCE_XLSX = ROOT / "FAQ_Sause_eV_Website_Pflege.xlsx"
OUTPUT_JSON = ROOT / "assets" / "data" / "faq.json"


def _get_cell_value(
    cell: ET.Element, shared_strings: List[str], ns: Dict[str, str]
) -> str:
    cell_type = cell.attrib.get("t")
    value_node = cell.find("a:v", ns)

    if value_node is None:
        inline_string = cell.find("a:is", ns)
        if inline_string is None:
            return ""
        return "".join(
            (node.text or "")
            for node in inline_string.iter(
                "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
            )
        )

    raw = value_node.text or ""
    if cell_type == "s" and raw.isdigit():
        idx = int(raw)
        if idx < len(shared_strings):
            return shared_strings[idx]
    return raw


def _load_rows_from_first_sheet(xlsx_path: Path) -> List[Dict[str, str]]:
    with zipfile.ZipFile(xlsx_path) as zf:
        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        first_sheet = workbook.find("a:sheets", NS).find("a:sheet", NS)  # type: ignore[union-attr]
        rel_id = first_sheet.attrib[  # type: ignore[union-attr]
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        ]

        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        target = None
        for rel in rels:
            if rel.attrib.get("Id") == rel_id:
                target = rel.attrib.get("Target")
                break
        if not target:
            raise RuntimeError("Could not resolve first worksheet target.")
        if not target.startswith("xl/"):
            target = f"xl/{target}"

        shared_strings: List[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            sst = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in sst.findall("a:si", NS):
                shared_strings.append(
                    "".join(
                        (node.text or "")
                        for node in si.iter(
                            "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
                        )
                    )
                )

        worksheet = ET.fromstring(zf.read(target))
        rows: List[Dict[str, str]] = []
        for row in worksheet.findall(".//a:sheetData/a:row", NS):
            values: Dict[str, str] = {}
            for cell in row.findall("a:c", NS):
                ref = cell.attrib.get("r", "")
                col = re.sub(r"\d", "", ref)
                values[col] = _get_cell_value(cell, shared_strings, NS)
            rows.append(values)
        return rows


def _as_int(value: str, default: int = 999999) -> int:
    try:
        return int(float((value or "").strip()))
    except Exception:
        return default


def _build_items(rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    if not rows:
        return []

    items: List[Dict[str, object]] = []
    for row in rows[1:]:
        category = (row.get("B") or "").strip()
        question = (row.get("D") or "").strip()
        long_answer = (row.get("F") or "").strip()
        website_relevant = (row.get("J") or "").strip().lower() == "ja"

        if not website_relevant:
            continue
        if not category or not question or not long_answer:
            continue

        items.append(
            {
                "id": _as_int(row.get("A", "")),
                "category": category,
                "order": _as_int(row.get("C", "")),
                "question": question,
                "answer": long_answer,
            }
        )

    items.sort(key=lambda x: (str(x["category"]), int(x["order"])))
    return items


def main() -> None:
    if not SOURCE_XLSX.exists():
        raise FileNotFoundError(f"Source XLSX not found: {SOURCE_XLSX}")

    rows = _load_rows_from_first_sheet(SOURCE_XLSX)
    items = _build_items(rows)

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": SOURCE_XLSX.name,
        "count": len(items),
        "items": items,
    }
    OUTPUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(items)} FAQ entries to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
