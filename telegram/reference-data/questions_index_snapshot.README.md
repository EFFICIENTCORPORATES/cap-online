# `questions_index_snapshot.json` — provenance

This is a **snapshot**, copied byte-for-byte on **2026-08-18** from the canonical file at
`first_run/output/generated-from-script/questions_index.json` (the Question Bank Book
pipeline's own output — Pillar 4, owned by `first_run/`, **not** by `telegram/`).

It exists so `telegram/tools/build_exam_bot_mcq_export.py` can still run when `telegram/` is
copied into a repo that doesn't have `first_run/` alongside it. That script always prefers the
**live** `first_run/` source when it's present — this snapshot is only ever used as a fallback,
and the script prints a loud warning to stdout whenever it falls back to it.

**This snapshot does not auto-update.** If the canonical `first_run/` file changes (new sittings
tagged, corpus corrections) and you need `build_exam_bot_mcq_export.py` to reflect that from a
detached `telegram/` copy, re-copy it by hand:

```
cp first_run/output/generated-from-script/questions_index.json \
   telegram/reference-data/questions_index_snapshot.json
```

See `telegram/FIRST_PROMPT.md` for the wider portability pass this was part of, and
`build_exam_bot_mcq_export.py`'s own docstring for exactly how the two sources are chosen
between.
