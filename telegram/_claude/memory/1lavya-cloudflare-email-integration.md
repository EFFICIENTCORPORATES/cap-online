---
name: 1lavya-cloudflare-email-integration
description: "Cloudflare Email Service (send-only, real REST API) now sends student report emails, one dedicated unmonitored address per bot on one shared domain; on-demand \"report\"/\"analysis\"/\"email\"/\"mail\" trigger added alongside \"profile\""
metadata: 
  node_type: memory
  type: project
  originSessionId: 82fc4833-12f2-45d0-bf8f-7222e49b86bc
  modified: 2026-08-11T14:23:25.871Z
---

Built 2026-08-11. Pranav provided real `CF_EMAIL_API_TOKEN` + `CF_EMAIL_ACCOUNT_ID` (`telegram/.env`) for Cloudflare's Email Service (public beta, launched 2026-04-16 — real product, researched via WebSearch/WebFetch before building, not guessed). REST endpoint: `POST https://api.cloudflare.com/client/v4/accounts/{account_id}/email/sending/send`.

**Confirmed setup** (via AskUserQuestion — this touches live domain/DNS config I can't verify myself): 1lavya.com already onboarded for Email Sending in the Cloudflare dashboard; **one shared domain, different local parts per bot** (not literal per-bot subdomains — Cloudflare onboarding/verification is per-domain, so this needed zero extra Cloudflare setup) — `studyhub@1lavya.com`, `examhub@1lavya.com`, `csarunchouhan@1lavya.com`, `capranav-study@1lavya.com`, `capranav-exam@1lavya.com`, each unmonitored by design; `support@1lavya.com`/`admin@1lavya.com` are real, already-monitored mailboxes referenced in every report email's footer.

New `telegram/database/cf_email.py` (raw REST client). Rewrote `telegram/database/report_delivery.py` to use it instead of Gmail SMTP — resolves each bot's own `from_email` from `bots.json`, sends fully 1LAVYA-branded HTML (new `brand_kit.render_email_footer_html()`, text-based not image-based for Outlook compatibility). `myfiles_hub_bot.py`'s own OTP email is UNCHANGED (still Gmail SMTP, not migrated).

Also built same day: an on-demand report trigger (`report_flow.py`'s `start_report_flow_on_demand()`) — typing "report"/"analysis"/"email"/"mail" (exact phrase) to any bot now offers the performance report anytime, not just at the 20-question milestone, reusing the entire existing channel-picker/delivery pipeline. Wired into `study_hub_bot.py` for the first time (previously had zero report_flow integration).

**Verified with a real send** through the actual production code path to Pranav's own email (pranavaiversion@gmail.com) — confirmed delivered with a real Cloudflare message_id. See [[1lavya-reporting-roadmap-decisions]] and [[1lavya-profile-system-built]] for related context. Full detail: `telegram/REPORT-PIPELINE.md`.

**Why:** real transactional email delivery for the report pipeline, replacing the placeholder/unconfigured SMTP path; the on-demand trigger matches the "profile" pattern students already understand.
**How to apply:** any NEW bot that should send report emails needs a `from_email` entry in `bots.json` — falls back to a generic `reports@1lavya.com` otherwise, never crashes. `report_flow.py` entry points now require a `bot_id` argument — any new call site must pass it.

**Real bug found+fixed same day**: a bot whose `bots.json` `display_name` contains a comma or parentheses (csarunchouhan's does) broke Cloudflare's From-header parser (unquoted RFC 5322 display name) — HTTP 400 `email.sending.error.email.invalid`. Fixed via `email.utils.formataddr` (new `cf_email.build_from_header()`), verified with a real send, permanent regression test added. Lesson: any FUTURE bot display_name with special characters needs no special handling now — formataddr always quotes correctly — but worth remembering this class of bug if a hand-rolled email header ever appears elsewhere in this codebase.
