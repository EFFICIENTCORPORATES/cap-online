# telegram/_claude/ — portable snapshot of Claude's skills + session memory

Added **2026-08-18**, as part of the `telegram/` standalone-portability pass (see
`telegram/FIRST_PROMPT.md`'s "Running this folder standalone" section).

Two things live here, both of which previously existed ONLY outside `telegram/` and
would NOT have travelled with a folder copy:

## `skills/`

A copy of the 4 telegram-relevant skill docs from the cap-online repo's own
`_claude/skills/` (the other files there are for the book pillars and aren't relevant
here). These are reference docs — read them before doing the matching kind of work —
not a special Claude Code tool-loading mechanism; a plain copy works identically to the
originals. **Not auto-synced** — if the originals in cap-online's `_claude/skills/`
are updated, re-copy the telegram-relevant ones here by hand.

| File | Covers |
|---|---|
| `SKILL-telegram-sql-query.md` | Writing SQL against `platform.db` — schema map, verified join recipes, SQLite gotchas |
| `SKILL-study-bot-catalog-pipeline.md` | CA Study Hub catalog build (flat-folder PDFs → Excel) |
| `SKILL-study-hub-bot-architecture.md` | Study Hub bot's own architecture |
| `SKILL-cs-cma-toc-pipeline.md` | CS/CMA chapter Table-of-Contents extraction + PDF splitting |

## `memory/`

A **point-in-time export** (2026-08-18) of Claude's own persistent session memory for
this project — normally stored OUTSIDE any git repo, at
`~/.claude/projects/<sanitized-repo-path>/memory/` on whichever machine a Claude Code
session runs from, keyed to that exact project path. That location is genuinely not
part of `telegram/` and can't be made "self-contained" through a file edit — it's a
tool-level construct tied to one machine's Claude Code installation. This folder is the
closest thing to a portable substitute: a real, git-tracked snapshot of everything
Claude understood about this platform's architecture/decisions/gotchas as of the export
date, readable by any future AI session (or human) working from `telegram/` alone.

**This snapshot does not auto-update and will drift from reality.** Every file below
inherits the same caveat Claude Code's own memory system carries: *"Memories are
point-in-time observations, not live state — claims about code behavior or file:line
citations may be outdated. Verify against current code before asserting as fact."* If
you want a fresher export later, re-copy from the live memory path above (or, in a new
location entirely, from wherever a Claude Code session's own project-memory folder
ends up for that new path).

`MEMORY.md` is the index (one line per file). Files link to each other via `[[name]]`
— every link target that existed in the original 18-file set is included here too, so
none of them dangle.
