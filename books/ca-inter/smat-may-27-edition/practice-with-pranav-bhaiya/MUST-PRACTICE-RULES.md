# Must Practice — how a question earns its place

The rule this file states is the whole reason the shortlist is defensible. A
student should be able to ask "why these ten?" and get the same answer every
time, for every chapter.

Until 2026-09-24 this logic lived only in one session's working notes: the AS 2
list was computed, reviewed and published, but the formula behind it was never
written down and the build script only *rendered* a hand-typed list of ten ids.
That is fixed — `capranav_com_revamped/tools/build_must_practice_data.py` now
computes the shortlist from the rules below.

Encoding the formula reproduced nine of the ten questions in the AS 2 list that
had already been published by hand. It differed on one: the hand-picked list
kept `M2C5U1-013` (PYQ September 2025 — the most recent question actually set in
a real exam on the chapter's top-ranked topic) while the formula ranks
`M2C5U1-009` above it. Pranav's call, 2026-09-24: **the formula stands, and AS 2
was republished to match it.** The rule is worth more than any one hand pick.

## What the question is

**"Which questions has ICAI most likely to set again in the next attempt?"** —
not "which are hardest", not "which are most interesting to teach". Everything
below follows from that one question.

## The four signals, and why each is weighted as it is

Every descriptive question in a unit is scored out of 1.0.

| Signal | Weight | What it measures |
|---|---:|---|
| Topic weight | **40%** | How heavily that question's topic has actually been examined, from the 400-topic ranking built over the last ten PYQ sittings. Uses the topic's total allocated PYQ marks, capped at 5. |
| Study Material match | **25%** | How close the question is to a question in ICAI's own Study Material. A = 1.0, B = its measured similarity %, C = 0.30, D = 0. |
| Source and recency | **20%** | `0.45 × paper-type + 0.55 × recency`. MTP = 1.0, RTP = 0.95, **PYQ = 0.6**. Recency is the sitting's position across the ten-sitting window. |
| Marks | **15%** | The question's marks, capped at 7. |

Three of these deserve their reasoning stated, because they are the ones a
reader would otherwise argue with:

**Study Material match is the strongest single repeat signal.** ICAI visibly
re-uses its own Study Material illustrations. A Category A question is one it
has already lifted near-verbatim once; that it might do so again is the most
concrete evidence available. It is not weighted higher than topic weight only
because a perfect match on a topic that is never examined is still not worth a
student's evening.

**A PYQ scores *lower* than an MTP or RTP (0.6 vs 1.0/0.95).** This looks
backwards and is deliberate. A question already set in a past exam has, in that
exact form, just been used. MTPs and RTPs are ICAI *signalling what it is
thinking about* for the sitting ahead, so they are the better predictor of the
next paper. A PYQ still scores well when its topic is heavy — it simply does
not get a bonus for having already appeared.

**Recency is a gradient, not a cutoff.** Nothing is excluded for being old; a
2023 MTP on a heavily examined topic can still outrank a recent one on a thin
topic.

## The coverage pass

Raw score alone clusters. On AS 2, six of the top ten by raw score are
near-identical questions on exclusions from cost of inventories, and three
Top-100 topics went untouched entirely.

So after ranking:

1. Take the top N by score (N = 10).
2. Find any Top-100 topic of that chapter with no question in the set.
3. For each, add the highest-scoring question that covers it.
4. To stay at N, drop the lowest-scoring question whose every topic is still
   covered by at least one other question in the set — never one that is the
   sole carrier of a topic.

Every question in the final set still had to score well on its own; coverage
only decides *which* of several strong candidates makes it.

On AS 2 (before the diversity rules above) this swapped out `M2C5U1-016` and `-013` for `-010` (Joint and By-Products,
the only question covering it, and the largest at 7 marks) and `-007` (retail
method and NRV estimation). That was the published list until the diversity rules above replaced it.

## Duplicates and diversity (added 2026-09-24)

**Why this exists.** AS 2 was first published with `-002` (MTP Jan 2026) and `-012`
(PYQ Sep 2024) — the *same question word for word* — both in the ten, and with
`-006` and `-005` (the Wooden Plywood wastage problem, only the year changed) both in
as well. Six of the ten were on one topic. The formula had no way to notice: a
repeat scores as high as its twin, so both climb together. The earlier
"known limitation" note named the topic clustering but not literal repeats, and
nothing checked for either. A student's ten practice slots were being spent on
five or six distinct questions.

Applied to the score-ranked list, before the coverage pass:

1. **Repeats are removed.** Question text with numbers, currency and tags stripped
   is compared pairwise; **90% or more similar = the same question**, and only
   the higher-scoring one may appear (`DUPLICATE_THRESHOLD`). This is the same
   90% rule as the OP/PP design, used here only to stop a repeat taking a second slot.
2. **A reworded repeat is caught by its figures.** Two questions that share
   at least 5 distinct figures, covering 60% or more of the smaller question's
   figures, are the same problem (`SHARED_FIGURES_*`). Text similarity alone missed
   AS 2's `-001` (MTP Jan 2026 Set 1), which is PYQ May 2024 Q1(b) with a new
   company name and a shortened stem: 58% text match, 13 of 14 figures identical.
3. **At most two questions per topic** (a question's best-ranked topic,
   `MAX_PER_TOPIC`). Extras are held back, then used in this order: first to
   cover a Top-100 topic nothing else covers, then — **the list is always
   ten** — to pad it, best score first. The cap therefore shapes the list without
   ever shortening it. (Pranav, 2026-09-24: keep it at ten; a first version
   that stopped short produced nine on AS 2.)

The build prints every repeat it drops and which twin it kept.

**What this cannot catch.** Similarity finds repeats and reworded repeats, not *the same idea in
a different story*. AS 2's `-017` (Zing Ltd.) is the joint/by-product closing-stock problem again with new figures, but is mapped to an unrelated topic, so nothing mechanical sees it — it is excluded by hand with a written reason (`force_exclude`), and `M2C5U1-013` is the same template as the hand-picked `-003`, so it stays out for the same reason. Likewise two different companies facing the same normal-versus-abnormal
loss trap read as different questions. The per-topic cap is the guard against
that. It costs something real: on a chapter where one topic holds most of the
strongest questions (AS 2's exclusions from cost), the cap pushes in questions
from thinner topics with lower scores. That is the intended trade — wider
practice over a stronger-but-repetitive list. If a chapter's list looks too weak,
raise `MAX_PER_TOPIC` for a reason stated here, or `force_include` with a reason.

## What is deliberately not in the formula

- **Difficulty.** Not a predictor of what gets set, and the corpus has no
  trustworthy difficulty field.
- **Teaching order.** A chapter's natural teaching sequence is a different
  concern from exam probability; ordering the printed list by it would hide the
  ranking that justifies the list.
- **Anything hand-tuned per question.** A thumb on the scale for a question
  someone likes defeats the point. Overrides exist (below) but must be stated.

## Overrides

`build_must_practice_data.py`'s `UNITS` table accepts, per unit:

- `force_include` / `force_exclude` — ids that must or must not appear,
  **each with a written reason**, applied after scoring and before coverage.
- `why_overrides` — replaces the auto-generated "Why this one" line on a card
  with hand-written wording.

Overrides are for real editorial judgement the formula cannot see — not for
nudging a ranking. If a unit needs several, the formula is wrong and should be
fixed instead.

AS 2's ten carry `why_overrides` so every card reads in one voice rather than
mixing reviewed prose with generated lines. They change the wording only —
never which questions are chosen.

## Inputs

All already reviewed; nothing here is re-typed or re-derived:

| Input | File |
|---|---|
| Topic ranks, priority bands, per-question topic mapping, Study Material match category and % | `data/descriptive_topic_priority.json` |
| Verbatim question and answer HTML, marks, source label, badges, Author's Note | `data/mcq-library/*_Descriptive.json` |
| Printed page number in the Question Bank | the distributed `..._V1.pdf`, matched on each question's own printed header line |

## Changing the rules

Change the weights in one place — `SCORING` in
`build_must_practice_data.py` — then re-run. The script prints each unit's full
ranking with the score breakdown, so the effect on every published unit is
visible before anything is deployed. Update this file in the same commit: a
weight that is in the code but not described here is exactly the situation this
document exists to prevent.

## Hand exclusions made under these rules (2026-09-24)

Each is a `force_exclude` in `UNITS` with its reason beside it. They exist
because a question can be a repeat that no similarity measure sees: a *part* of
a larger question reissued alone, or the same idea under an unrelated topic tag.

| Unit | Excluded | Why |
|---|---|---|
| AS 2 | `-017` | Joint/by-product closing-stock problem again (same as `-010`), mapped to an unrelated topic. |
| AS 2 | `-004` | Same normal-versus-abnormal-loss idea as `-006`; Pranav flagged the pair as too similar. |
| AS 10 | `-007`, `-008`, `-009`, `-010` | The four parts of `-002` (MTP Nov 2023 Set 1), each reissued alone in RTP Jan 2026. |
| AS 10 | `-013` | Replacing a machine component — the subsequent-cost idea of `-006`, mapped elsewhere. |

Known remaining softness: AS 2's tenth slot is `-009`, whose part (i) is the same
"costs excluded from inventory cost" theory as `-002`; its part (ii) is a distinct
NRV-with-commission problem, which is why it was taken over the alternatives
(`-013` is the same template as the hand-picked `-003`). Swap it with a written
reason if you would rather.
