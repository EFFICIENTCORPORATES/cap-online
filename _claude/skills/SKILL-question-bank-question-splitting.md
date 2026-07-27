# SKILL — Question Bank: Independent vs. Connected Sub-Part Splitting

> **What this is:** the rule for deciding whether a multi-part exam question (a single
> printed "Question 1" with sub-parts (a), (b), (c)) becomes **multiple separate Question
> Bank records** or **stays one record**. Get this wrong and either the Question Bank
> fragments a genuinely continuous problem into meaningless pieces, or it buries an
> unrelated 5-mark AS 2 problem inside a 14-mark blob that a student searching for AS 2
> can't actually use.
>
> Read `SKILL-question-bank-html-schema.md` §5 for the concrete HTML shape this produces.
> Read `SKILL-question-bank-topic-tagging.md` §4 for how `data-final-chapter` is computed
> once you know whether a question is split.

---

## 1. The classification rule (Pranav, 2026-07-24)

For every multi-part question, before tagging anything, ask: **do the sub-parts share one
continuous fact pattern, where a later sub-part depends on data or a result from an
earlier one — or are they independent problems that just happen to be printed together
under one question number?**

- **Independent** — different companies, different numbers, no data flows between
  sub-parts. The exam paper bundled them together purely for paper-length/marks-budget
  convenience (e.g. "Question 1 = three unrelated 5/5/4-mark problems on three different
  standards"). → **Each sub-part becomes its own separate Question Bank record.**
- **Connected** — one continuous scenario; a later sub-part builds on an earlier result,
  or all sub-parts describe facts about the same entity/transaction. → **Stays one
  record.**

**In practice, independent is the common case for CA Inter Advanced Accounting MTP/RTP/PYQ
descriptive questions.** Every multi-part Part II question in the first sitting processed
under this rule (`MTP_May2026_Set1.html`) turned out to be independent — e.g. Q1(a) Glen
Ltd./AS 16 borrowing costs, Q1(b) Karna Ltd./AS 11 forex, Q1(c) Sonu & Mohan/AS 2
inventory are three entirely unrelated fact patterns, bundled only because the paper
needed a 14-mark "Question 1." Don't assume connected is equally likely — actually check
each sub-part's facts before deciding.

## 2. What "independent" produces

Each independent sub-part becomes its own qblock, with:

- Its own ID: parent question number + sub-part letter suffix
  (`CAI-P1-MTP-2026-05-S1-PII-Q1-a`).
- `data-parent-qno="1"` and `data-subpart="a"` — so "this was Q1(a) on exam day" is still
  reconstructable, even though the Question Bank organises by chapter, not by original
  paper layout.
- Its own `data-marks` (a plain integer — the sub-part's own marks, not the parent
  question's total).
- Its own single `.topics` tag (`data-topic-rank="primary"`, since there's exactly one
  topic once split).
- Its own `data-final-chapter` — trivially that one topic's `unitCode`.
- Its own examiner comment / extraction note, scoped to that sub-part only.

The full worked example is in `SKILL-question-bank-html-schema.md` §5.

## 3. What "connected" produces

The question stays one qblock. `.topics` carries multiple `<span class="topic-tag">`
entries, each ranked `primary`/`secondary` and each carrying its own `data-marks` share
(so the shares sum to the qblock's total — this should be a validated invariant once the
Python extraction script exists). `data-final-chapter` is computed as the tagged topic
with the latest `teaching_sequence` (see the tagging skill §4).

## 4. OR-alternatives are a related but distinct case

Some questions offer a straight either/or choice — e.g. "6. (a) Analyse AS 24 disclosure
requirements... **OR** (a) [an amalgamation purchase-consideration problem]..." Both
alternatives are legitimate, independently useful Question Bank content (a student
studying AS 24 wants the first; a student studying Amalgamation wants the second), but
they were never both answerable by the same student on exam day.

Treat each alternative as its own independent record (same as §2), but link them with a
shared `data-alt-group` and distinguish with `data-alt="1"`/`data-alt="2"`. **A marks-total
validator must not sum both alternatives toward the parent question's marks** — only one
was ever actually worth marks on any single exam attempt. This is different from ordinary
independent splitting, where every sub-part's marks genuinely does sum to the parent's
total.

## 5. Case-scenario MCQ clusters are a related but distinct question (open, 2026-07-25)

This skill's independent/connected rule is about a multi-part *descriptive* question with
sub-parts (a)/(b)/(c). A **case-scenario MCQ cluster** (one `.case-scenario` narrative,
several dependent MCQs, per the html-schema skill §3) is structurally different: each MCQ
is already its own qblock, not a sub-part to decide whether to split. The open question
Pranav's review raised is whether a cluster whose sibling MCQs test *different* standards
needs its own cross-chapter handling (analogous to, but not the same as, this skill's
independent/connected rule) — see `SKILL-question-bank-chapter-book-rendering.md` §3.2 and
`SKILL-question-bank-topic-tagging.md` §4's open-issue note. Not resolved yet.

## 6. Edge cases to flag, not decide silently

- A sub-part that's *mostly* independent but reuses one figure from an earlier sub-part
  (e.g. "using the depreciation computed in part (a)...") — this is connected, even
  though the standards tested differ. When in doubt, connected is the safer default,
  since splitting a genuinely connected question loses information a student would need;
  wrongly leaving an independent question merged just costs some search precision.
- A question where the "independent" sub-parts are all about the same shell company name
  but with clearly unrelated fact patterns per sub-part (common in ICAI theory questions,
  e.g. "Discuss disclosure requirements... (i)... (ii)... (iii)... (iv)..." all nominally
  about "A Ltd.") — these are independent; a shared placeholder company name is not the
  same as a shared fact pattern.
- If genuinely unsure, tag the qblock with `data-issue="needs-human-judgment"` (extend the
  vocabulary in the HTML schema skill §7 if this comes up often enough to be worth a
  dedicated tag) rather than guessing.
