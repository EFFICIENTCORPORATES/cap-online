#!/usr/bin/env python3
"""Validate the versioned topic-master values and planning calendar; stdlib only."""
import csv
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re


def validate():
    root = Path(__file__).resolve().parent
    snap = json.loads((root / 'workbook-snapshot.json').read_text(encoding='utf-8'))
    records = {}
    for tab in snap['tabs']:
        with (root / tab['csv']).open(encoding='utf-8', newline='') as stream:
            rows = list(csv.reader(stream))
        expected = [tab['columns']] + tab['rows']
        assert rows == [[str(v) for v in r] for r in expected], tab['name']
        assert all(len(r) == len(tab['columns']) for r in rows), tab['name']
        records[tab['name']] = [dict(zip(tab['columns'], r)) for r in tab['rows']]
    topics = records['ICAI-SMAT-TOPIC_WISE']
    units = records['Unit Index']
    chapters = records['Chapter Summary']
    assert len(topics) == 229 and len(units) == 33 and len(chapters) == 11
    assert len(records['Resource Index']) == 132
    assert len({t['unique_topic_id'] for t in topics}) == len(topics)
    unit_ids = {u['unit_id'] for u in units}
    assert len(unit_ids) == len(units)
    for t in topics:
        assert isinstance(t['topic_no'], str) and isinstance(t['page_number'], str)
        assert re.fullmatch(r'\d+(?:\.\d+)*', t['topic_no'])
        assert re.fullmatch(r'\d+\.\d+', t['page_number'])
        assert t['unit_id'] in unit_ids
        assert t['unique_topic_id'] == t['unit_id'] + '_T' + t['topic_no']
        assert t['importance_status'] == 'Not assessed' and t['importance_evidence'] == ''
    counts = Counter(t['chapter_no'] for t in topics)
    assert set(counts) == set(range(1, 12))
    for ch in chapters:
        assert counts[ch['chapter_no']] == ch['numbered_topic_count']
    for u in units:
        section = [t for t in topics if t['unit_id'] == u['unit_id']]
        assert len(section) == u['numbered_topic_count']
        assert [int(t['topic_no'].split('.')[-1]) for t in section] == list(range(1, len(section)+1))
    assert all(r['unit_id'] in unit_ids for r in records['Resource Index'])
    assert any(t['topic_no'] == '1.10' for t in topics)
    assert any(t['page_number'] == '1.10' for t in topics)
    with (root.parent / 'teaching-plan.csv').open(encoding='utf-8', newline='') as stream:
        plan = list(csv.DictReader(stream))
    assert len(plan) == 49
    assert len({r['date'] for r in plan}) == 49
    assert sum(float(r['hours']) for r in plan) == 61.5
    lessons = [r for r in plan if r['lecture_no']]
    assert [int(r['lecture_no']) for r in lessons] == list(range(1, 42))
    for r in plan:
        assert date.fromisoformat(r['date']).strftime('%A') == r['day']
    assert all(next(r for r in plan if r['date'] == d)['hours'] == '1.5'
               for d in ['2026-12-06', '2026-12-13'])
    print('PASS: all five CSV tabs match JSON; 229 unique topic IDs; 33 sections; '
          '11 chapter counts reconcile; text pages preserved; 132 resources; '
          '49 calendar dates / 41 lectures / 61.5 hours.')


if __name__ == '__main__':
    validate()
