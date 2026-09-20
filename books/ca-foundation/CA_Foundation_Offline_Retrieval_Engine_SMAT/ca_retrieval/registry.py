from __future__ import annotations
import json
from pathlib import Path
from .models import Block, DocumentMeta


def _source_marker(rec: dict, start: int, end: int) -> str:
    ps = rec.get('printed_page_start') or ''
    pe = rec.get('printed_page_end') or ps
    if start == end:
        return f'<!-- ICAI_SOURCE_PAGE pdf_page={start} printed_page="{ps}" -->'
    return f'<!-- ICAI_SOURCE_PAGE_RANGE pdf_pages={start}-{end} printed_pages="{ps}-{pe}" -->'


def load_example_registry(registry_path: Path, documents: list[DocumentMeta]) -> tuple[list[Block], dict]:
    if not registry_path.exists():
        return [], {'loaded': False, 'count': 0}
    payload = json.loads(registry_path.read_text(encoding='utf-8'))
    records = payload.get('records', [])
    by_name = {d.path.name: d for d in documents}
    out: list[Block] = []
    missing_docs = []
    for idx, rec in enumerate(records):
        doc = by_name.get(rec.get('source_md', ''))
        if doc is None:
            missing_docs.append(rec.get('source_md'))
            continue
        base_meta = {
            'paper': rec.get('paper'), 'module': rec.get('module'), 'chapter': rec.get('chapter'), 'unit': rec.get('unit'),
            'source_pdf': rec.get('source_pdf'), 'page_start': rec.get('page_start'), 'page_end': rec.get('page_end'),
            'printed_page_start': rec.get('printed_page_start'), 'printed_page_end': rec.get('printed_page_end'),
            'topic_number': rec.get('topic_number'), 'topic_title': rec.get('topic_title'),
            'sequence': rec.get('sequence'), 'source_number': rec.get('source_number'),
            'source_emphasis': rec.get('source_emphasis'), 'registry_role': rec.get('registry_role'),
            'representation': rec.get('representation'), 'source_verified_registry': True,
        }
        # One authoritative source item per Example. This is the exhaustive 53-item registry.
        m = dict(base_meta)
        m.update({
            'id': f"EXAMPLE-SOURCE::{rec.get('source_pdf')}::SEQ-{int(rec.get('sequence') or idx+1):02d}",
            'type': 'example', 'retrieval_type': 'example', 'number': rec.get('number'),
            'separable_question_solution': bool(rec.get('separable')),
        })
        out.append(Block(meta=m, content=rec.get('full_content', '').strip(), document=doc, ordinal=1_000_000 + idx * 3))

        # Derivative Q/S blocks are created only when the PDF provides a safely separable boundary.
        if rec.get('separable') and rec.get('question_text') and rec.get('solution_text'):
            pair = f"example-registry:{rec.get('source_pdf')}:{int(rec.get('sequence') or idx+1):02d}"
            qm = dict(base_meta)
            qm.update({
                'id': m['id'] + '::QUESTION', 'type': 'example_question', 'retrieval_type': 'example_question',
                'pair_key': pair, 'number': rec.get('number'), 'registry_derivative': True,
            })
            sm = dict(base_meta)
            sm.update({
                'id': m['id'] + '::SOLUTION', 'type': 'example_solution', 'retrieval_type': 'example_solution',
                'pair_key': pair, 'number': rec.get('number'), 'registry_derivative': True,
            })
            marker = _source_marker(rec, int(rec.get('page_start') or 0), int(rec.get('page_end') or rec.get('page_start') or 0))
            qcontent = marker + '\n```text\n' + rec['question_text'].strip() + '\n```'
            scontent = marker + '\n```text\n' + rec['solution_text'].strip() + '\n```'
            out.append(Block(meta=qm, content=qcontent, document=doc, ordinal=1_000_001 + idx * 3))
            out.append(Block(meta=sm, content=scontent, document=doc, ordinal=1_000_002 + idx * 3))
    meta = {
        'loaded': True, 'version': payload.get('version'), 'count': len(records),
        'virtual_blocks': len(out), 'missing_documents': sorted(set(x for x in missing_docs if x)),
        'separable_examples': sum(1 for r in records if r.get('separable')),
    }
    return out, meta
