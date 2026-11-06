#!/usr/bin/env python3
"""Check that outline/SPEAKER-NOTES.md matches the built deck.

For every slide in slides-manifest.json the notes must have a heading
    ### [slide-id] Title — N steps
with the same id order and the same N, and the "Step n" / "Steps a – b"
markers inside that section must cover 1..N with nothing beyond N.
Exit code 1 on any mismatch.  Run:  python3 deck/check_notes_sync.py
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
manifest = json.load(open(os.path.join(HERE, "slides-manifest.json"), encoding="utf-8"))
notes = open(os.path.join(HERE, "..", "outline", "SPEAKER-NOTES.md"), encoding="utf-8").read()

sections = re.split(r"(?m)^### \[(\w+)\] (.*?) — (\d+) steps?\s*$", notes)
# split yields: pre, id, title, n, body, id, title, n, body ...
found = []
for i in range(1, len(sections), 4):
    found.append((sections[i], sections[i + 1], int(sections[i + 2]), sections[i + 3]))

errors = []
if [f[0] for f in found] != [m["id"] for m in manifest]:
    errors.append(f"slide id order differs.\n  deck : {[m['id'] for m in manifest]}\n  notes: {[f[0] for f in found]}")
by_id = {f[0]: f for f in found}
for m in manifest:
    f = by_id.get(m["id"])
    if not f:
        errors.append(f"[{m['id']}] missing in notes"); continue
    _, title, n, body = f
    if n != m["steps"]:
        errors.append(f"[{m['id']}] notes say {n} steps, deck has {m['steps']}")
    covered = set()
    for a, b in re.findall(r"\*\*Steps? (\d+)(?: [–-] (\d+))?", body):
        lo, hi = int(a), int(b or a)
        covered.update(range(lo, hi + 1))
    missing = [k for k in range(1, m["steps"] + 1) if k not in covered]
    extra = [k for k in covered if k > m["steps"]]
    if missing: errors.append(f"[{m['id']}] steps not described in notes: {missing}")
    if extra: errors.append(f"[{m['id']}] notes describe steps beyond the deck: {extra}")
if errors:
    print("NOTES OUT OF SYNC:"); [print(" -", e) for e in errors]; sys.exit(1)
print(f"OK: {len(manifest)} slides, notes and deck agree on ids and step counts.")
