---
name: 1lavya-centralized-account-model
description: One student = one shared 1LAVYA account/wallet/MCQ-quota across the main bot AND every faculty bot — not siloed per bot
metadata: 
  node_type: memory
  type: project
  originSessionId: eff70d38-31a6-4cc7-baf2-a93b1aa25479
  modified: 2026-08-09T12:47:37.874Z
---

Decided 2026-08-09 (Pranav's explicit pick over the per-bot-silo alternative): a
student's wallet balance and MCQ quota (100 free/month, then ₹1/100 recharge — see
[[1lavya-faculty-onboarding-model]]) are **shared platform-wide**, one account per
student across the main 1LAVYA bot and every faculty white-label bot, not a separate
account/quota per bot.

**Why this matters for the build**: rules out per-bot SQLite silos for
user/wallet/credit state (today's actual pattern — MyFiles Hub has its own `users`
table, Exam Hub has no user table at all, Study Hub has none either). Implies a
**central account/wallet service** (one DB, or at minimum one shared table set) that
every bot process — main + all faculty instances — reads/writes against, keyed by
something stable across bots (Telegram user ID is the natural key, already present in
every bot's existing per-bot tables). This is the load-bearing decision for whatever
tenant/credits schema gets designed next — build the central account layer before or
alongside the per-tenant content-scoping work in
[[1lavya-faculty-onboarding-model]], not after.

Content scoping (which faculty's bot shows which content) stays per-tenant/per-bot as
already planned — only identity/wallet/quota is centralized, not content.
