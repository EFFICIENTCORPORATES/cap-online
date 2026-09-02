#!/usr/bin/env python3
"""Build the public notes catalogue from the supplied shared Google Drive folders."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


SOURCE_MAP = {
    "1fHgz8ktYI8_kF5oQaUKVHcP43KE9bTNb": ("Layer 1", "Class Annotated Notes"),
    "1PiA4naDk1l_C10XsuQ5R3mYiuBGBXEPV": ("Layer 1", "ICAI Study Material"),
    "1xmSOYMmtv8HehJNOwtQ6_WYO2WIKlHxH": ("Layer 1", "ICAI SMAT Annotated"),
    "1qig42dPLhCVid_Zy-M3SULwWGrGwwWUv": ("Layer 1", "Question Bank"),
    "1r_lM2vLEVNMr2vdEQ7OJcQzMrGoZXuZT": ("Layer 2", "Revision Materials"),
    "1H4vmFnwW-RrKGHQm4Hwpc7cv1nkn7WP2": ("Layer 2", "Newton of Accounts Notes"),
    "1uOiHAtOXHl7ra5bV_x3xWpvcEdWvF3Yl": ("Extra", "Bare Accounting Standards"),
    "1BJIdl2J0j9e3UeC5lv76ypxP4oAkL-8V": ("Extra", "Practical References"),
}

FOLDER_LINKS = [
    {
        "layer": "Layer 1",
        "title": "Base Materials",
        "url": "https://drive.google.com/drive/folders/1vkXftVomfQtkdoLoc25Emde64RcSTEWh?usp=sharing",
    },
    {
        "layer": "Layer 2",
        "title": "Revision Materials",
        "url": "https://drive.google.com/drive/folders/1r_lM2vLEVNMr2vdEQ7OJcQzMrGoZXuZT?usp=sharing",
    },
    {
        "layer": "Layer 3",
        "title": "Sanjeevani Bootis",
        "url": "https://drive.google.com/drive/folders/1rJZcjkP1qq-jp2YvBGPfMSaUpCehYwT9?usp=sharing",
    },
    {
        "layer": "Extra",
        "title": "Extra Materials",
        "url": "https://drive.google.com/drive/folders/19H106HQLeVgpFhni1_qRjj7cjr4fj_zx?usp=sharing",
    },
]

ROOT_FOLDER = "https://drive.google.com/drive/folders/1h6Vf5gJzi4CkrUjFAZ9PBMfVLsBukglm?usp=sharing"


def decode_drive_payload(html: str) -> list:
    match = re.search(r"window\['_DRIVE_ivd'\] = '(.*?)';if", html, re.S)
    if not match:
        return []
    decoded = bytes(match.group(1), "utf-8").decode("unicode_escape")
    return json.loads(decoded)


def extract_entries(node: object) -> list[tuple[str, str, str]]:
    results: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    def walk(value: object) -> None:
        if not isinstance(value, list):
            return
        if (
            len(value) >= 4
            and isinstance(value[0], str)
            and isinstance(value[1], list)
            and isinstance(value[2], str)
            and isinstance(value[3], str)
        ):
            entry = (value[0], value[2], value[3])
            if entry not in seen:
                seen.add(entry)
                results.append(entry)
        for child in value:
            walk(child)

    walk(node)
    return results


def clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip()


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: build_notes_catalog.py INPUT_DIRECTORY OUTPUT_JS")

    input_dir = Path(sys.argv[1]).resolve()
    output_file = Path(sys.argv[2]).resolve()
    notes: list[dict[str, str]] = []

    for folder_id, (layer, category) in SOURCE_MAP.items():
        source = input_dir / f"drive_{folder_id}.html"
        if not source.exists():
            continue
        payload = decode_drive_payload(source.read_text(encoding="utf-8"))
        for file_id, title, mime_type in extract_entries(payload):
            if mime_type != "application/pdf":
                continue
            notes.append(
                {
                    "id": file_id,
                    "title": clean_title(title),
                    "layer": layer,
                    "category": category,
                    "preview": f"https://drive.google.com/file/d/{file_id}/view",
                    "download": f"https://drive.google.com/uc?export=download&id={file_id}",
                }
            )

    notes.sort(key=lambda item: (item["layer"], item["category"], item["title"].casefold()))
    payload = {
        "updated": "27 July 2026",
        "rootFolder": ROOT_FOLDER,
        "folderLinks": FOLDER_LINKS,
        "notes": notes,
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        "window.CAPRANAV_NOTES = "
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )
    print(f"Created {output_file} with {len(notes)} PDF records")


if __name__ == "__main__":
    main()
