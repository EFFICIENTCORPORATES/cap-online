# The Telegram bot platform has moved out of this repo

**Read this before touching anything under `telegram/`.**

The 1LAVYA Telegram bot platform — every bot, the admin portal, the shared
database, the backup tooling and all of its documentation — was migrated out of
`cap-online` into its own repository:

| | |
|---|---|
| **Repository** | `EFFICIENTCORPORATES/Main1lavyaAIAgents` |
| **Folder** | `examstudyhub/` |
| **Local working copy** | `D:\EffCorp_Products\Main1Lavya\Main1lavyaAIAgents\examstudyhub` |
| **Runs on** | a Contabo server (not this PC any more) |
| **Cutover** | 2026-09-03, ~14:18 UTC |

That repo is the only source of truth for the platform. Do not edit bot code,
configs or platform docs here — anything left in this folder is either preserved
accounts content (below) or local runtime history.

## Why the leftovers here looked alarming

The old local deployment's traces are still on this machine and read like an
outage if you don't know about the migration:

- `telegram/database/platform.db` stops at 2026-09-03 14:18 — that is the
  cutover, not a crash. All nine bots' heartbeats end within 30 seconds of each
  other, which is what a clean `manage_bots.py stop` looks like.
- The seven `1LAVYA *` Windows scheduled tasks are **Disabled** and the startup
  shortcut is renamed `1LAVYA Bots - Ensure Running.lnk.disabled`. Correct — the
  bots no longer run from this PC.
- The bots themselves are live. The Telegram API reports zero pending updates
  for every one of them, which only happens while something is actively polling.

## What is deliberately kept here, and why

This is the accounts teaching repo, so **accounts content for CA / CMA / CS
stays**, even though the migrated repo also has it. Which papers count as
"accounts" is taken from the platform's own `course_catalog` subject names, not
guessed. Accounting papers only — Cost and Financial Management are excluded:

| Course | Level | Paper | Subject |
|---|---|---|---|
| CA | Foundation | 1 | Accounting |
| CA | Inter | 1 | Advanced Accounting |
| CA | Final | 1 | Financial Reporting |
| CMA | Foundation | 2 | Fundamentals of Financial and Cost Accounting |
| CMA | Intermediate | 6 | Financial Accounting |
| CMA | Intermediate | 10 | Corporate Accounting and Auditing |
| CMA | Final | 18 | Corporate Financial Reporting |
| CS | CSEET | 2 | Fundamentals of Accounting |
| CS | Executive | 4 | Corporate Accounting & Financial Management |

Also kept: the old deployment's **runtime logs and PID files** under
`database/run/`. They are the only record of how the platform behaved while it
ran on this machine — by their nature no copy exists in the migrated repo, so
nothing automated will ever delete them. Remove them by hand if you decide they
are not worth the space.

## How the duplicated content was removed

`tools/prune_migrated_telegram.py`. It never deletes on trust: a file goes only
when an identical copy is confirmed in the migrated repo **at the moment of
deletion**, or when the same path there holds a newer version. Dry run is the
default; `--execute` applies it; every removal is written to a manifest.

Before any of that ran, six files were found to exist **only** here and were
copied into the migrated repo first, hash-verified:

```
bots/myfiles_hub_bot.py                 (63,225 bytes)  the MyFiles Hub bot itself
bots/myfiles_activity_report.py         ( 4,408 bytes)
bots/README_Bot3_MyFilesHub.md          (13,331 bytes)
comparator/sales-agent-ARCHIVED-2026-08-26.md
assets/exam_bot/CMA Final Law Json/CMA_Final_P13_M1_Companies_Act_2013_180_MCQ.json
assets/exam_bot/faculty/csarunchouhan/mcq_questions_extracted.json
```

The MyFiles Hub bot is worth a flag: the migrated repo's `bots.json` still lists
`1lavya-myfileshub` as **active** and carries its data and PID file, but its
source code was absent from that repo's `bots/` folder until this copy. Whether
that bot is genuinely still in service is worth confirming.

The 1.22 GB `assets/study_bot/Study Materials.zip` was removed only after all
1,091 entries inside it were verified present in the migrated repo by content
hash — the same PDFs, renamed there to the `CA_L3_P02_C1_U0_…` human-id
convention, which is why a filename comparison alone made them look missing.
