# Day End Faculty Reports (local PDF archive)

Auto-generated nightly by `telegram/tools/generate_day_end_faculty_reports.py`
(Task Scheduler job **"1LAVYA Day End Faculty Reports"**, daily ~23:50 local
time). One PDF per real faculty tenant per UTC calendar day:
`{tenant_id}/{tenant_id}_{YYYY-MM-DD}.pdf`.

Each PDF is the same Comprehensive Faculty Report the Admin Portal's
**Day End (Today)** button on `/reports/faculty` generates on demand —
level-wise sections (one per course/level the faculty teaches), students
identified by their permanent 1LAVYA username with every linked phone's
activity merged, colored accuracy badges. See
`telegram/admin_portal/faculty_report.py`'s module docstring for the full
design.

**Explicitly named "initial" by Pranav (2026-08-17)** — this on-disk
archive exists because the platform is new and he wants a standing dated
record while things stabilize, not because it's meant to be a permanent
feature. "Later on we might not need this" — his own words. Revisit/retire
this folder (and the Task Scheduler job that fills it) once he confirms
it's no longer needed; the same reports remain available on-demand from
the dashboard regardless.

Gitignored (`**/*.pdf` in the repo root `.gitignore`) — these files live
locally only, same as every other generated PDF in this repo.
