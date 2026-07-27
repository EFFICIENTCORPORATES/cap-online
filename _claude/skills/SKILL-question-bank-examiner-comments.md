# SKILL — Question Bank: Examiner Comments (Common Student Mistakes)

> **What this is:** how the `commonMistakes`/`.examiner-comment` field gets content for
> **every** Question Bank question, when real ICAI "Examiners' Comments on the Performance
> of the Examinees" only exist for 6 specific PYQ sittings. Covers where the actual style
> guide lives, the provenance-tagging discipline that keeps synthesized content honestly
> labelled, and a decision this pipeline deliberately did **not** make even though it was
> recommended once — read §3 before "fixing" the examiner-comment voice.

---

## 1. The actual style guide lives elsewhere — read it, don't duplicate it

The detailed "how to write in ICAI's examiner-report voice" guide is
`books/question-bank/metadata-index/examiner-comments-writing-skill.md`, built by
analysing all 6 real ICAI Examiner's Comments documents Pranav sourced for Paper 1
(Jan 2025, May 2024, Sep 2024, May 2025, Sep 2025, Jan 2026). It covers the opening
quantifier vocabulary ("Many examinees...", "A significant number of examinees..."), the
failure-mode → standard-citation → consequence-chain structure, tone rules, and a worked
example. **Read that file directly** when writing a synthesized comment — this skill file
is the meta-layer around it (provenance, schema attributes, the voice-dilution question),
not a replacement.

## 2. The provenance rule — non-negotiable

Every `.examiner-comment` carries two things:

1. A free-text `data-source` citation:
   - `"ICAI Examiner's Comment — {Session}, verbatim"` or `"...,paraphrased"` — only for
     the 6 sittings with a real sourced document, and only when the comment can be
     confidently matched to that exact question/sub-part.
   - `"Synthesized per examiner-comments-writing-skill.md — not ICAI-sourced"` —
     everything else (all MTP, all RTP, and PYQ sittings outside the 6 sourced ones).
2. As of the 2026-07-24 schema revision, also a clean enum attribute:
   `data-comment-source="synthesized"` or `data-comment-source="icai"` — so "show me
   every synthesized comment across the corpus" is a filter, not a string-match on free
   text.

Never blend the two without both the enum and the citation making it unambiguous which is
which.

## 3. Voice dilution was proposed once and rejected — know why, in case it comes up again

An external-AI review of this schema (2026-07-24) raised a real concern: synthesized
comments are written in the *exact* ICAI examiner-report register ("Many examinees...",
"A significant number of examinees...") even on **Mock Test Papers, which literally have
no examinees**. If screenshotted out of context, a synthesized MTP comment could read as
authentic ICAI commentary. The proposed fix was to reframe synthesized comments into a
visibly different voice ("A common error here is...", "Watch out for...").

**This was rejected, on purpose, because it would reverse a decision Pranav already made
and this pipeline was already built to.** The original design (see
`examiner-comments-writing-skill.md`'s own stated purpose) is explicit: synthesized
comments should be "written in the ICAI examiner voice per the skill file... indistinguishable
in *style* from the real thing — while the provenance rule... keeps it never confusable in
*authority* with the real thing." In other words: the safeguard against misattribution was
always meant to be the metadata (§2 above) plus visible on-page labelling, not a diluted
voice. Diluting the voice would also make the synthesized content noticeably lower-quality
as a study aid — the whole point of matching the real register is that it reads like a
genuine, useful examiner insight, not a generic study tip.

**What *was* adopted from that review:** the clean `data-comment-source` enum (§2), and a
requirement that the synthesized/real distinction be **visible on the rendered page**, not
only present in an attribute a reader never sees — e.g. `book-style.css`'s
`.examiner-comment.synthesized` rule should carry a visible marker (border style, small
label, icon) distinct from `.examiner-comment` without that class, so a student reading
the page — not just a script querying the DOM — can tell the two apart at a glance.

**If this tension resurfaces** (e.g. Pranav decides the misattribution risk outweighs
voice fidelity after all), that is a real reopening of a locked decision — flag it
explicitly and get an explicit answer before changing every synthesized comment already
written across the corpus. Don't silently drift the voice sitting-by-sitting.

## 4. MTP/RTP vs. PYQ

- **MTP and RTP papers can never have real ICAI comments** — they aren't real exams, ICAI
  never comments on them. Every comment on an MTP/RTP sitting is synthesized, always.
- **PYQ sittings** may have a real sourced comments document (6 exist so far, at
  `books/question-bank/Raw_PDF_Question_Bank_CA_Inter_Accounts/examiner-comments-paper1/
  Paper1-ExaminerComments-{Session}.md`) or may not. Check before assuming — a PYQ sitting
  without a sourced document still gets a synthesized comment, tagged as such.
