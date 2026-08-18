---
name: 1lavya-branding-footer-scope-corrected
description: "Powered by 1LAVYA" was scoped back from every faculty-bot message to only PDF deliveries and answer reveals — never on welcome/menu/question screens
metadata:
  type: project
---

Corrected 2026-08-10 (same day it was first built, per Pranav's follow-up: "not with
every message... too much"). The footer now appears at exactly 3 call sites total
across `study_hub_bot.py` + `exam_hub_bot.py`: `send_file()`'s file/PDF caption in
Study Hub; `send_answer()` (descriptive) and `handle_mcq_answer()` (MCQ result) in
Exam Hub; and `send_pdf()`'s document caption in Exam Hub. Everywhere else — welcome
screens, every menu/picker, the question text itself (both descriptive and MCQ), the
post-download "download more?" prompt, "queue exhausted" messages, search results —
is deliberately unbranded now. `faculty_bot.py`'s top-level hub picker is unbranded
too. Verified by test (not just inspection) across both hubs, including the exact
descriptive/MCQ answer-vs-question boundary. See [[1lavya-menu-autoskip-and-next-step-ux]]
for the mechanism (`with_brand`/`with_brand_md`/`with_brand_html`) this scoping applies to.
