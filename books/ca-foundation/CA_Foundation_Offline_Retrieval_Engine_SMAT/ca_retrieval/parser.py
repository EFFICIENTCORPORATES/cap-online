from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Iterable
from .models import Block, DocumentMeta

BLOCK_RE = re.compile(r"<!--\s*ICAI_BLOCK\s+(\{.*?\})\s*-->")
FRONT_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


def parse_scalar(text: str):
    v = text.strip()
    if not v:
        return ""
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    if v.lower() == "null":
        return None
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def parse_frontmatter(text: str) -> dict:
    m = FRONT_RE.search(text)
    if not m:
        return {}
    out = {}
    lines = m.group(1).splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            i += 1
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if val in {">-", ">", "|-", "|"}:
            buf = []
            i += 1
            while i < len(lines) and (lines[i].startswith(" ") or not lines[i].strip()):
                buf.append(lines[i].strip())
                i += 1
            out[key] = " ".join(x for x in buf if x)
            continue
        out[key] = parse_scalar(val)
        i += 1
    return out


def parse_markdown(path: Path) -> tuple[DocumentMeta, list[Block]]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    doc = DocumentMeta(path=path, raw=parse_frontmatter(text))
    matches = list(BLOCK_RE.finditer(text))
    blocks: list[Block] = []
    for i, m in enumerate(matches):
        try:
            meta = json.loads(m.group(1))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid ICAI_BLOCK JSON in {path.name} near offset {m.start()}: {exc}") from exc
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[m.end():end].strip("\n")
        blocks.append(Block(meta=meta, content=content, document=doc, ordinal=i))
    return doc, blocks


def discover_markdown(folder: Path, recursive: bool = True) -> list[Path]:
    pattern = "**/*_PARSED*.md" if recursive else "*_PARSED*.md"
    files = sorted(folder.glob(pattern))
    if not files:
        # Accept any md folder for schema-compatible custom data.
        pattern = "**/*.md" if recursive else "*.md"
        files = sorted(folder.glob(pattern))
    return [p for p in files if p.is_file()]


def load_corpus(folder: Path) -> tuple[list[DocumentMeta], list[Block]]:
    docs: list[DocumentMeta] = []
    blocks: list[Block] = []
    for path in discover_markdown(folder):
        doc, bs = parse_markdown(path)
        if bs:
            docs.append(doc)
            blocks.extend(bs)
    blocks.sort(key=lambda b: b.sort_key())
    return docs, blocks
