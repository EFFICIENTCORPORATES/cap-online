"""
telegram/bots/cancel_utils.py -- universal "get me out of this" escape
hatch (2026-08-16)
--------------------------------------------------------------------------------
Built after independent code review flagged that no flow module on this
platform had any way to abort a multi-step text dialog once started --
profile edit, report contact collection, an MCQ issue report, a wallet
custom-recharge amount, a Test Mode descriptive-upload prompt -- the ONLY
way out was to actually finish that step, or accidentally type something
that happened to match a DIFFERENT flow's own trigger word.

SCOPE, DELIBERATELY NARROW: this cancels an in-progress DATA-ENTRY DIALOG
(the "awaiting text/callback" state a flow module tracks in
context.user_data), never a standing, already-committed thing like an
active paid Test Mode session (test_sessions.status='in_progress') -- that
already has its own deliberate exit path (the Submit Test confirmation
screen's own Cancel button, and the test itself is real money already
spent -- typing one stray word should never abandon it). Typing "stop"
mid-test only cancels an active UPLOAD sub-step if one is running, exactly
like "pass" already does -- it never touches the test session itself.

Every bot's text_router should check matches_cancel() near the top (after
whichever flow's own is_awaiting_text_input() check for text a flow is
ACTIVELY, correctly expecting right now -- e.g. a report flow waiting on an
email mid-CONFIRM step should still get to react to "cancel" as "cancel",
not have it silently swallowed as an invalid email) and call
cancel_all_flows() if it matches, so a student is never stuck in a step
they no longer want to be in. State key names below are mirrored as
literals (not imported) from each flow module's own constants, the same
"stay a dependency-free leaf" reasoning telegram/database/identity.py's own
docstring gives for not importing profile_flow.py -- keep these in sync if
any flow module ever renames its own user_data keys.
"""

CANCEL_PHRASES = {"cancel", "exit", "stop"}


def matches_cancel(text: str) -> bool:
    return (text or "").strip().lower() in CANCEL_PHRASES


def cancel_all_flows(context) -> bool:
    """Clears every flow module's own "mid-dialog" state. Returns True if
    anything was actually in progress (so a caller only shows a
    "Cancelled" reply when there was something real to cancel -- never a
    confusing "Cancelled" to a student who typed "stop" with nothing
    active, who should just fall through to normal handling instead)."""
    ud = context.user_data
    was_active = False

    if ud.get("profile_flow_state"):
        was_active = True
    ud["profile_flow_state"] = None
    for key in ("profile_flow_pending_username", "profile_flow_pending_course",
                "profile_flow_pending_attempt_year", "profile_flow_pending_attempt_profile_id",
                "profile_flow_pending_email", "profile_flow_pending_mobile"):
        ud.pop(key, None)

    if ud.get("report_flow_state"):
        was_active = True
    ud["report_flow_state"] = None
    for key in ("report_flow_pending_mobile", "report_flow_pending_email", "report_flow_upsell"):
        ud.pop(key, None)

    if ud.get("issue_report"):
        was_active = True
    ud.pop("issue_report", None)

    if ud.get("walletrc_awaiting_custom_amount"):
        was_active = True
    ud["walletrc_awaiting_custom_amount"] = False

    # Test Mode's UPLOAD SUB-STEP only -- never the test session itself,
    # see module docstring.
    if ud.get("testflow_upload_seq") is not None or ud.get("testflow_awaiting_upload_pick"):
        was_active = True
    for key in ("testflow_upload_seq", "testflow_upload_page_counter", "testflow_awaiting_upload_pick"):
        ud.pop(key, None)

    return was_active
