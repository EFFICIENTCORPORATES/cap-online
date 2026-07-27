# SKILL — Question Bank: Recurring Question Detection (OP/PP)

> **What this is:** how to identify and label questions that ICAI recycles across
> multiple MTP/RTP/PYQ sittings — extremely common in this exam's question banks — so a
> student sees "this is the same question you already saw in the Jan 2025 MTP" rather than
> encountering it as if new each time, and so the Question Bank Book can cross-reference
> matching answer keys for confidence.
>
> This is a **cross-sitting** concern — it can't be resolved while tagging a single
> sitting HTML file in isolation. It runs once enough sittings exist to compare, most
> naturally as part of the `questions.json` build step described in
> `SKILL-question-bank-pipeline-overview.md` §2.

---

## 1. The rule (Pranav)

Strip numbers from question text, compare pairwise across the corpus. **≥90% textual
similarity ⇒ same recurring group.** Within a group, the occurrence from the
**chronologically earliest sitting** is the **OP** ("Original concept-testing Question");
every later occurrence is a **PP** ("Practice-Practice Question" / "For Practice
Question").

**All occurrences still appear in full in the eventual chapter book** — this rule is for
cross-referencing and confidence-checking (e.g. spotting a case where two occurrences'
answer keys actually disagree, which is worth flagging), not for de-duplication. A student
benefits from seeing "you've solved a version of this before" and from the answer-key
cross-check, not from having repeats silently removed.

## 2. What counts as a match

- **Same numbers, renamed company** — still a match. ICAI frequently reuses a problem's
  structure with a different fictional entity name; the underlying test is identical.
- **Same company/context, different numbers, same underlying trap** — this is the
  ambiguous case the mechanical 90%-on-stripped-numbers rule is built to catch, but it can
  also produce false positives (two genuinely different questions that happen to share
  boilerplate phrasing, e.g. two unrelated AS 16 borrowing-cost problems that both open
  "Glen Ltd. began construction of a new building..."). **Flag borderline cases for human
  judgment rather than deciding silently** — this is the same "flag, don't guess"
  discipline that governs the rest of this pipeline (see
  `SKILL-question-bank-verbatim-extraction.md`).

## 3. Mechanics (not yet built)

Two layers, cheap to add once the `questions.json` index exists (see the pipeline
overview skill):

1. **Exact-match `content_hash`** — SHA-256 over the normalised question text
   (lowercased, whitespace-collapsed, punctuation-stripped, **numbers preserved** —
   unlike the OP/PP fuzzy rule above, an exact hash is for catching literal re-prints,
   where numbers matter). Cheap, deterministic, catches the simplest recycling case
   immediately.
2. **Near-duplicate detection for the ≥90%-on-stripped-numbers rule** — a shingle/MinHash
   approach over the number-stripped text, not just the exact hash. This is what actually
   implements Pranav's rule; the exact hash alone would miss every renamed-company or
   changed-figure recurrence, which is the *common* case, not the exception.

## 4. Schema hooks

Once implemented, a question's `questions.json` row (see the pipeline overview skill §2
for the row shape) carries:

- `content_hash` — the exact-match hash.
- `recurring_group_id` — shared across all occurrences the fuzzy match groups together.
- `recurring_role` — `"OP"` or `"PP"`, computed from `exam_year`/`exam_month`/`session_key`
  ordering within the group.

This does **not** need a corresponding attribute on the sitting HTML itself — it's
entirely a Layer-2 (computed JSON) concern, consistent with the rule in the pipeline
overview skill §4: anything whose logic might need to change later belongs in Python, not
hand-authored per file.
