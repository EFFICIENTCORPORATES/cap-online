from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .models import Block, QuerySpec
from .parser import load_corpus
from .query import parse_natural_query, select
from .registry import load_example_registry
from .renderer import render


EXPECTED_SOURCE_COUNTS = {
    "examples": 53,
    "illustrations": 235,
    "illustration_solutions": 235,
    "mcqs": 269,
    "theory_retrieval_blocks": 79,
    "practical_questions": 79,
    "true_false_statements": 307,
    "scenario_questions": 0,
    "safely_separable_example_questions": 18,
}


class RetrievalEngine:
    """Load, filter, validate, and render the bundled offline CA corpus."""

    def __init__(self, data_folder):
        self.data_folder = Path(data_folder).resolve()
        if not self.data_folder.is_dir():
            raise FileNotFoundError(f"Data folder not found: {self.data_folder}")

        self.documents, parsed_blocks = load_corpus(self.data_folder)
        registry_path = self.data_folder.parent / "semantic_registry" / "example_registry.json"
        registry_blocks, self.example_registry = load_example_registry(
            registry_path, self.documents
        )

        # The corrected release replaces legacy Example classifications with the
        # source-verified registry. Other block types remain exactly as parsed.
        self.blocks = [
            block
            for block in parsed_blocks
            if block.type not in {"example", "example_question", "example_solution"}
        ]
        self.blocks.extend(registry_blocks)
        self.blocks.sort(key=lambda block: block.sort_key())

    def query(self, spec: QuerySpec) -> list[Block]:
        return select(self.blocks, spec)

    def query_text(self, text: str) -> tuple[QuerySpec, list[Block]]:
        spec = parse_natural_query(text)
        return spec, self.query(spec)

    def compile(self, spec: QuerySpec, keep_internal_comments: bool = False) -> str:
        return render(
            self.query(spec),
            spec,
            keep_internal_comments=keep_internal_comments,
        )

    def source_item_counts(self) -> dict[str, int]:
        counts = Counter(block.type for block in self.blocks)
        return {
            "examples": counts["example"],
            "illustrations": counts["illustration_question"],
            "illustration_solutions": counts["illustration_solution"],
            "mcqs": counts["tyk_mcq_question"],
            "theory_retrieval_blocks": counts["tyk_theory_question"],
            "practical_questions": counts["tyk_practical_question"],
            "true_false_statements": counts["tyk_true_false_question"],
            "scenario_questions": counts["tyk_scenario_question"],
            "safely_separable_example_questions": counts["example_question"],
        }

    def stats(self) -> dict:
        type_counts = Counter(block.type for block in self.blocks)
        return {
            "documents": len(self.documents),
            "blocks": len(self.blocks),
            "types": dict(type_counts),
            "source_item_counts": self.source_item_counts(),
            "example_registry": self.example_registry,
            "papers": sorted({b.paper for b in self.blocks if b.paper is not None}),
            "modules": sorted({b.module for b in self.blocks if b.module is not None}),
            "chapters": sorted({b.chapter for b in self.blocks if b.chapter is not None}),
        }

    def result_counts(self, blocks: list[Block], spec: QuerySpec) -> dict[str, int]:
        from .query import ANSWER_TYPES

        return {
            "source_items": sum(1 for block in blocks if block.type not in ANSWER_TYPES),
            "returned_blocks": len(blocks),
        }

    def validate(self) -> dict:
        issues: list[dict[str, str]] = []

        if not self.documents:
            issues.append({"level": "error", "message": "No classified Markdown documents loaded."})

        registry = self.example_registry
        if not registry.get("loaded"):
            issues.append({"level": "error", "message": "Example registry was not found."})
        for name in registry.get("missing_documents", []):
            issues.append({"level": "error", "message": f"Registry source document missing: {name}"})

        ids = Counter(block.id for block in self.blocks if block.id)
        for block_id, count in ids.items():
            if count > 1:
                issues.append({"level": "error", "message": f"Duplicate block id: {block_id}"})

        actual = self.source_item_counts()
        is_bundled_corpus = self.data_folder.name == "parsed_md" and len(self.documents) == 37
        if is_bundled_corpus:
            for key, expected in EXPECTED_SOURCE_COUNTS.items():
                if actual.get(key) != expected:
                    issues.append(
                        {
                            "level": "error",
                            "message": f"{key}: expected {expected}, found {actual.get(key)}",
                        }
                    )

        errors = sum(item["level"] == "error" for item in issues)
        warnings = sum(item["level"] == "warning" for item in issues)
        return {
            "ok": errors == 0,
            "documents": len(self.documents),
            "blocks": len(self.blocks),
            "errors": errors,
            "warnings": warnings,
            "issues": issues,
            "source_item_counts": actual,
        }

    def write_index(self, output_path) -> Path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "id": block.id,
                "type": block.type,
                "paper": block.paper,
                "module": block.module,
                "chapter": block.chapter,
                "unit": block.unit,
                "number": block.number,
                "pair_key": block.pair_key,
                "source_pdf": block.source_pdf,
                "page_start": block.page_start,
                "page_end": block.page_end,
            }
            for block in self.blocks
        ]
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return out
