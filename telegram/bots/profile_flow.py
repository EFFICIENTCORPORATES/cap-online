"""
telegram/bots/profile_flow.py -- student profile / identity system
(2026-08-11)
--------------------------------------------------------------------------------
Built as the identity foundation for the Phase 3 (Leaderboard) roadmap item
(Pranav's explicit confirmation, 2026-08-11: "build it now as that
foundation, so Phase 3 doesn't need to rebuild it later" -- see
[[1lavya-branding-report-leaderboard-portal-roadmap]] memory).

Trigger: a student types "profile" / "change profile" / "my profile" /
"edit profile" (case-insensitive, exact-phrase match -- NOT the general
free-text intent-routing system from the original big roadmap message,
which is separate, not-yet-scheduled scope). The bot asks for confirmation
before doing anything ("Would you like to view/edit your profile?"), per
Pranav's explicit ask.

IDENTITY MODEL: a `username` (telegram/database/schema.sql's
`student_profiles` table) is permanent -- locked forever once claimed,
Instagram-handle style (3-20 chars, letters/numbers/underscore,
case-insensitive uniqueness). ONE username can be shared across MULTIPLE
`students` rows (multiple phones/chat_ids for the same real person) --
Pranav's own scenario: a student practicing from 3 different mobile
numbers should have all 3 chat_ids mapped to the SAME username, so losing
a phone never loses their identity/progress. The very first time a chat_id
sets up a profile, it's asked "do you already have a username (from
another phone)?" -- yes links this chat_id to that EXISTING
student_profiles row (no new row created); no walks through creating a
brand-new one.

Editable at any time, shared across every chat_id linked to the same
username: display_name, course, level, exam_attempt. Editable per-chat-id
(NOT shared -- Pranav's own scenario: "he might give different email ids
as well" across phones): email, mobile_number (reuses report_flow.py's
exact echo-confirm collection pattern via the shared contact_utils.py).
NEVER editable once set: username itself.

Avatar is NOT collected or stored here at all -- Pranav's choice: pulled
live from the student's own Telegram profile photo whenever one is needed
(via context.bot.get_user_profile_photos()), never through this flow.

CALLBACK_DATA NAMESPACING: `profile:<action>` and `profileconfirm:<yes|
retry>` -- NEW prefixes, same discipline as report_flow.py's `report:`/
`reportconfirm:` (see that module's own docstring for the exact bug class
this is guarding against -- an unscoped or mis-scoped CallbackQueryHandler
silently swallowing another handler's buttons, found and fixed twice
already this session). Registered as their own CallbackQueryHandler in
every bot that imports this module.

STATE: tracked in context.user_data["profile_flow_state"].
is_awaiting_text_input() is what each bot's MessageHandler checks before
delegating a free-text message here (checked ALONGSIDE report_flow's own
is_awaiting_text_input() -- the two flows are mutually exclusive per chat
at any moment, never both active).
"""

import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "telegram" / "database"))
import db as platform_db  # noqa: E402
import contact_utils  # noqa: E402
import leaderboard_metrics  # noqa: E402 -- telegram/database/leaderboard_metrics.py, leaderboard config + eligibility (2026-08-11)

logger = logging.getLogger(__name__)

# --- trigger phrases -- exact match, case-insensitive, not a fuzzy search ---
TRIGGER_PHRASES = {"profile", "change profile", "my profile", "edit profile"}

# --- states ---
CONFIRMING_START = "profile_confirming_start"
AWAITING_USERNAME_HAS_ONE = "profile_awaiting_has_username"
AWAITING_EXISTING_USERNAME = "profile_awaiting_existing_username"
AWAITING_NEW_USERNAME = "profile_awaiting_new_username"
CONFIRMING_NEW_USERNAME = "profile_confirming_new_username"
AWAITING_DISPLAY_NAME = "profile_awaiting_display_name"
AWAITING_EXAM_ATTEMPT_OTHER = "profile_awaiting_exam_attempt_other"
AWAITING_EMAIL = "profile_awaiting_email"
CONFIRMING_EMAIL = "profile_confirming_email"
AWAITING_MOBILE = "profile_awaiting_mobile"
CONFIRMING_MOBILE = "profile_confirming_mobile"

_TEXT_INPUT_STATES = (
    AWAITING_EXISTING_USERNAME, AWAITING_NEW_USERNAME, AWAITING_DISPLAY_NAME,
    AWAITING_EXAM_ATTEMPT_OTHER, AWAITING_EMAIL, AWAITING_MOBILE,
)

# Fixed, small, stable taxonomy -- CA/CS/CMA each have a fixed set of
# levels, unlikely to change often enough to justify deriving this
# dynamically from a catalog file. See module docstring.
COURSE_LEVELS = {
    "CA": ["Foundation", "Inter", "Final"],
    "CS": ["Executive", "Professional"],
    "CMA": ["Foundation", "Intermediate", "Final"],
}

# Exam attempt is collected as Year then Month, two guided picker steps
# (Pranav, 2026-08-11 -- replaced the earlier single-step quick-pick list),
# combined into one "{Month} {Year}" string on save. Years are computed
# relative to "now" at render time (never hardcoded), so this never goes
# stale the way a fixed list of sitting labels would. "Other" free text is
# still offered at the year step as an escape hatch for an attempt further
# out than the window below covers.
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
ATTEMPT_YEAR_WINDOW = 5   # current year + this many more


def _attempt_years() -> list[str]:
    return [str(datetime.now(timezone.utc).year + offset) for offset in range(ATTEMPT_YEAR_WINDOW)]

MIN_USERNAME_LEN, MAX_USERNAME_LEN = 3, 20
MAX_LEADERBOARDS_PER_STUDENT = 5   # Pranav's explicit cap, 2026-08-11


def _now():
    return platform_db.now()


def is_awaiting_text_input(context) -> bool:
    return context.user_data.get("profile_flow_state") in _TEXT_INPUT_STATES


def matches_trigger(text: str) -> bool:
    return text.strip().lower() in TRIGGER_PHRASES


def _valid_username(text: str) -> str | None:
    """Returns the username if valid, else None. 3-20 chars,
    letters/numbers/underscore only -- Pranav's confirmed default,
    Instagram-style."""
    text = text.strip()
    if not (MIN_USERNAME_LEN <= len(text) <= MAX_USERNAME_LEN):
        return None
    if not all(c.isalnum() or c == "_" for c in text):
        return None
    return text


def _get_profile_for_chat(conn, telegram_user_id: int) -> dict | None:
    """The full profile (shared fields from student_profiles + per-chat
    fields from students) for this chat_id, or None if no username is
    linked yet."""
    row = conn.execute(
        """
        SELECT sp.username, sp.display_name, sp.course, sp.level, sp.exam_attempt,
               s.email, s.mobile_number
        FROM students s JOIN student_profiles sp ON sp.username = s.lavya_username
        WHERE s.telegram_user_id = ?
        """,
        (telegram_user_id,),
    ).fetchone()
    if not row:
        return None
    return {
        "username": row[0], "display_name": row[1], "course": row[2], "level": row[3],
        "exam_attempt": row[4], "email": row[5], "mobile_number": row[6],
    }


def _profile_summary_text(profile: dict | None, telegram_user_id: int, conn) -> str:
    if not profile:
        return "You don't have a 1LAVYA profile set up yet."
    lines = [
        f"<b>Username:</b> {profile['username']} <i>(permanent, cannot be changed)</i>",
        f"<b>Display Name:</b> {profile['display_name'] or 'Not set'}",
        f"<b>Course:</b> {profile['course'] or 'Not set'}",
        f"<b>Level:</b> {profile['level'] or 'Not set'}",
        f"<b>Target Attempt:</b> {profile['exam_attempt'] or 'Not set'}",
        f"<b>Email:</b> {profile['email'] or 'Not set'}",
        f"<b>Mobile:</b> {profile['mobile_number'] or 'Not set'}",
    ]
    return "\n".join(lines)


def _menu_keyboard(profile: dict | None) -> InlineKeyboardMarkup:
    rows = []
    if not profile:
        rows.append([InlineKeyboardButton("\U0001F194 Set up my username", callback_data="profile:start_username")])
    else:
        rows.append([InlineKeyboardButton("✏️ Display Name", callback_data="profile:edit_display_name")])
        rows.append([InlineKeyboardButton("\U0001F393 Course & Level", callback_data="profile:edit_course")])
        rows.append([InlineKeyboardButton("\U0001F4C5 Target Attempt", callback_data="profile:edit_exam_attempt")])
        rows.append([InlineKeyboardButton("\U0001F4E7 Email", callback_data="profile:edit_email")])
        rows.append([InlineKeyboardButton("\U0001F4F1 Mobile", callback_data="profile:edit_mobile")])
        # Leaderboards need an identity (username) to attach participation
        # to -- only offered once a profile actually exists. Course/Level
        # further gate WHICH boards show (see _show_leaderboards_menu), but
        # the button itself is always reachable so a student without
        # Course/Level set yet still finds out why the list is empty,
        # rather than the menu option disappearing with no explanation.
        rows.append([InlineKeyboardButton("\U0001F3C6 Leaderboards", callback_data="profile:leaderboards")])
    rows.append([InlineKeyboardButton("✅ Done", callback_data="profile:done")])
    return InlineKeyboardMarkup(rows)


async def _show_leaderboards_menu(query_or_message, context, telegram_user_id: int, edit: bool):
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    profile = _get_profile_for_chat(conn, telegram_user_id)

    if not profile or not profile.get("course") or not profile.get("level"):
        text = (
            "Set your <b>Course &amp; Level</b> first (from the profile menu) so we can show you "
            "leaderboards relevant to what you're actually studying."
        )
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="profile:confirm_yes")]])
    else:
        username = profile["username"]
        eligible = leaderboard_metrics.eligible_leaderboards_for(profile["course"], profile["level"])
        joined_ids = {
            r[0] for r in conn.execute(
                "SELECT leaderboard_id FROM leaderboard_participants WHERE username=?", (username,)
            ).fetchall()
        }
        joined_count = len(joined_ids)

        lines = [
            f"<b>Leaderboards for {profile['course']} {profile['level']}</b>",
            f"Joined: {joined_count}/{MAX_LEADERBOARDS_PER_STUDENT}",
            "",
        ]
        rows = []
        if not eligible:
            lines.append("No live leaderboards for your Course &amp; Level yet -- check back soon!")
        else:
            for lb in eligible:
                joined = lb["leaderboard_id"] in joined_ids
                icon = "✅" if joined else "➕"
                rows.append([InlineKeyboardButton(
                    f"{icon} {lb['display_name']}", callback_data=f"profile:toggle_lb:{lb['leaderboard_id']}",
                )])
        rows.append([InlineKeyboardButton("⬅️ Back", callback_data="profile:confirm_yes")])
        text = "\n".join(lines)
        markup = InlineKeyboardMarkup(rows)

    if edit:
        await query_or_message.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await query_or_message.reply_text(text, parse_mode="HTML", reply_markup=markup)


# ---------------------------------------------------------------------------
# ENTRY POINT (trigger phrase matched)
# ---------------------------------------------------------------------------
async def start_profile_flow(update, context):
    context.user_data["profile_flow_state"] = CONFIRMING_START
    keyboard = [[
        InlineKeyboardButton("Yes", callback_data="profile:confirm_yes"),
        InlineKeyboardButton("No", callback_data="profile:confirm_no"),
    ]]
    await update.message.reply_text(
        "Would you like to view/edit your profile?", reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ---------------------------------------------------------------------------
# CALLBACK DISPATCH
# ---------------------------------------------------------------------------
async def profile_flow_callback(update, context):
    query = update.callback_query
    await query.answer()
    action, _, value = query.data.partition(":")

    if action == "profile":
        await _handle_profile_action(query, context, value)
    elif action == "profileconfirm":
        await _handle_profile_confirm(query, context, value)


async def _show_menu(query_or_message, context, telegram_user_id: int, edit: bool):
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    profile = _get_profile_for_chat(conn, telegram_user_id)
    text = _profile_summary_text(profile, telegram_user_id, conn)
    markup = _menu_keyboard(profile)
    if edit:
        await query_or_message.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await query_or_message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def _handle_profile_action(query, context, value: str):
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    telegram_user_id = query.from_user.id

    if value == "confirm_no":
        context.user_data["profile_flow_state"] = None
        await query.edit_message_text("No problem!")
        return

    if value == "confirm_yes":
        context.user_data["profile_flow_state"] = None
        await _show_menu(query, context, telegram_user_id, edit=True)
        return

    if value == "done":
        context.user_data["profile_flow_state"] = None
        await query.edit_message_text("✅ Your profile is saved. You can type \"profile\" anytime to view or edit it again.")
        return

    if value == "start_username":
        context.user_data["profile_flow_state"] = AWAITING_USERNAME_HAS_ONE
        keyboard = [[
            InlineKeyboardButton("Yes, I have one", callback_data="profile:has_username_yes"),
            InlineKeyboardButton("No, create new", callback_data="profile:has_username_no"),
        ]]
        await query.edit_message_text(
            "Do you already have a 1LAVYA username (set up from another phone/device)?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if value == "has_username_yes":
        context.user_data["profile_flow_state"] = AWAITING_EXISTING_USERNAME
        await query.edit_message_text("Please type your existing 1LAVYA username.")
        return

    if value == "has_username_no":
        context.user_data["profile_flow_state"] = AWAITING_NEW_USERNAME
        await query.edit_message_text(
            "Great! Choose your 1LAVYA username -- <b>this is PERMANENT and can never be "
            "changed once set</b>, so pick carefully.\n\n"
            "3-20 characters, letters/numbers/underscore only (e.g. rahul_ca_2026).",
            parse_mode="HTML",
        )
        return

    if value == "edit_display_name":
        context.user_data["profile_flow_state"] = AWAITING_DISPLAY_NAME
        await query.edit_message_text("What display name would you like to use? (This is public, shown on leaderboards.)")
        return

    if value == "edit_course":
        keyboard = [[InlineKeyboardButton(c, callback_data=f"profile:pick_course:{c}")] for c in COURSE_LEVELS]
        await query.edit_message_text("Which course are you studying?", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if value.startswith("pick_course:"):
        course = value.split(":", 1)[1]
        context.user_data["profile_flow_pending_course"] = course
        keyboard = [[InlineKeyboardButton(lvl, callback_data=f"profile:pick_level:{lvl}")] for lvl in COURSE_LEVELS[course]]
        await query.edit_message_text(f"Course: <b>{course}</b>\nWhich level?", parse_mode="HTML",
                                       reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if value.startswith("pick_level:"):
        level = value.split(":", 1)[1]
        course = context.user_data.pop("profile_flow_pending_course", None)
        platform_db.execute_with_retry(
            conn, "UPDATE student_profiles SET course=?, level=?, updated_at=? WHERE username=(SELECT lavya_username FROM students WHERE telegram_user_id=?)",
            (course, level, _now(), telegram_user_id),
        )
        await query.edit_message_text(f"✅ Course & Level updated: {course} {level}")
        await _show_menu(query.message, context, telegram_user_id, edit=False)
        return

    if value == "edit_exam_attempt":
        years = _attempt_years()
        # 3 per row -- 5 years fits as 2 rows of 3 (last row short), reads
        # better than one long row of 5 skinny buttons.
        keyboard = [
            [InlineKeyboardButton(y, callback_data=f"profile:pick_attempt_year:{y}") for y in years[i:i + 3]]
            for i in range(0, len(years), 3)
        ]
        keyboard.append([InlineKeyboardButton("Other (type it)", callback_data="profile:pick_attempt_other")])
        await query.edit_message_text("Which year are you targeting?", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if value.startswith("pick_attempt_year:"):
        year = value.split(":", 1)[1]
        context.user_data["profile_flow_pending_attempt_year"] = year
        keyboard = [
            [InlineKeyboardButton(m, callback_data=f"profile:pick_attempt_month:{m}") for m in MONTHS[i:i + 3]]
            for i in range(0, len(MONTHS), 3)
        ]
        await query.edit_message_text(f"Year: <b>{year}</b>\nWhich month?", parse_mode="HTML",
                                       reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if value.startswith("pick_attempt_month:"):
        month = value.split(":", 1)[1]
        year = context.user_data.pop("profile_flow_pending_attempt_year", None)
        if not year:
            # Stale/replayed callback with no year in context (e.g. bot
            # restarted mid-flow) -- restart the picker rather than saving
            # a month with no year attached.
            await query.edit_message_text("Session expired -- let's try again. Which year are you targeting?")
            await _handle_profile_action(query, context, "edit_exam_attempt")
            return
        attempt = f"{month} {year}"
        platform_db.execute_with_retry(
            conn, "UPDATE student_profiles SET exam_attempt=?, updated_at=? WHERE username=(SELECT lavya_username FROM students WHERE telegram_user_id=?)",
            (attempt, _now(), telegram_user_id),
        )
        await query.edit_message_text(f"✅ Target attempt updated: {attempt}")
        await _show_menu(query.message, context, telegram_user_id, edit=False)
        return

    if value == "pick_attempt_other":
        context.user_data["profile_flow_state"] = AWAITING_EXAM_ATTEMPT_OTHER
        await query.edit_message_text("Please type the attempt you're targeting (e.g. \"Jan 2028\").")
        return

    if value == "edit_email":
        context.user_data["profile_flow_state"] = AWAITING_EMAIL
        await query.edit_message_text("Please type the email address you'd like on file.")
        return

    if value == "edit_mobile":
        context.user_data["profile_flow_state"] = AWAITING_MOBILE
        await query.edit_message_text("Please type your mobile number (e.g. 9876543210).")
        return

    if value == "leaderboards":
        await _show_leaderboards_menu(query, context, telegram_user_id, edit=True)
        return

    if value.startswith("toggle_lb:"):
        leaderboard_id = value.split(":", 1)[1]
        profile = _get_profile_for_chat(conn, telegram_user_id)
        if not profile:
            await query.answer("Set up your profile first.", show_alert=True)
            return
        username = profile["username"]
        already_joined = conn.execute(
            "SELECT 1 FROM leaderboard_participants WHERE username=? AND leaderboard_id=?",
            (username, leaderboard_id),
        ).fetchone()
        if already_joined:
            platform_db.execute_with_retry(
                conn, "DELETE FROM leaderboard_participants WHERE username=? AND leaderboard_id=?",
                (username, leaderboard_id),
            )
            await query.answer("Left leaderboard.")
        else:
            current_count = conn.execute(
                "SELECT COUNT(*) FROM leaderboard_participants WHERE username=?", (username,)
            ).fetchone()[0]
            if current_count >= MAX_LEADERBOARDS_PER_STUDENT:
                await query.answer(
                    f"You can join at most {MAX_LEADERBOARDS_PER_STUDENT} leaderboards -- leave one first.",
                    show_alert=True,
                )
                return
            platform_db.execute_with_retry(
                conn, "INSERT INTO leaderboard_participants (username, leaderboard_id, joined_at) VALUES (?,?,?)",
                (username, leaderboard_id, _now()),
            )
            await query.answer("Joined leaderboard!")
        await _show_leaderboards_menu(query, context, telegram_user_id, edit=True)
        return


async def _handle_profile_confirm(query, context, value: str):
    """Echo-confirm step, shared shape with report_flow.py's own -- but a
    SEPARATE state/callback namespace (profileconfirm: not reportconfirm:)
    since the two flows track entirely different pending values and must
    never be confused with each other mid-conversation."""
    state = context.user_data.get("profile_flow_state")
    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    telegram_user_id = query.from_user.id

    if value == "retry":
        if state == CONFIRMING_NEW_USERNAME:
            context.user_data["profile_flow_state"] = AWAITING_NEW_USERNAME
            await query.edit_message_text("No problem -- please type your desired username again.")
        elif state == CONFIRMING_EMAIL:
            context.user_data["profile_flow_state"] = AWAITING_EMAIL
            await query.edit_message_text("No problem -- please type your email address again.")
        elif state == CONFIRMING_MOBILE:
            context.user_data["profile_flow_state"] = AWAITING_MOBILE
            await query.edit_message_text("No problem -- please type your mobile number again.")
        return

    # value == "yes"
    if state == CONFIRMING_NEW_USERNAME:
        username = context.user_data.pop("profile_flow_pending_username", None)
        # Re-check uniqueness right before the actual insert -- someone else
        # could have claimed it in the gap between the echo and this
        # confirm (low-probability, but free to guard against).
        exists = conn.execute("SELECT 1 FROM student_profiles WHERE username=?", (username,)).fetchone()
        if exists:
            context.user_data["profile_flow_state"] = AWAITING_NEW_USERNAME
            await query.edit_message_text(f"Sorry, \"{username}\" was just taken by someone else -- please try a different username.")
            return
        now = _now()
        platform_db.execute_with_retry(
            conn, "INSERT INTO student_profiles (username, created_at, updated_at) VALUES (?,?,?)",
            (username, now, now),
        )
        platform_db.execute_with_retry(
            conn, "UPDATE students SET lavya_username=? WHERE telegram_user_id=?",
            (username, telegram_user_id),
        )
        context.user_data["profile_flow_state"] = None
        await query.edit_message_text(f"\U0001F389 Username <b>{username}</b> is yours -- permanently!", parse_mode="HTML")
        await _show_menu(query.message, context, telegram_user_id, edit=False)
        return

    if state == CONFIRMING_EMAIL:
        email = context.user_data.pop("profile_flow_pending_email", None)
        platform_db.execute_with_retry(
            conn, "UPDATE students SET email=?, email_verification_method='echo_confirm' WHERE telegram_user_id=?",
            (email, telegram_user_id),
        )
        context.user_data["profile_flow_state"] = None
        await query.edit_message_text(f"✅ Email updated: {email}")
        await _show_menu(query.message, context, telegram_user_id, edit=False)
        return

    if state == CONFIRMING_MOBILE:
        mobile = context.user_data.pop("profile_flow_pending_mobile", None)
        platform_db.execute_with_retry(
            conn, "UPDATE students SET mobile_number=?, mobile_verification_method='echo_confirm' WHERE telegram_user_id=?",
            (mobile, telegram_user_id),
        )
        context.user_data["profile_flow_state"] = None
        await query.edit_message_text(f"✅ Mobile updated: {mobile}")
        await _show_menu(query.message, context, telegram_user_id, edit=False)
        return


# ---------------------------------------------------------------------------
# TEXT INPUT HANDLING
# ---------------------------------------------------------------------------
async def handle_profile_text_input(update, context) -> bool:
    """Returns True if this message was consumed by the profile flow
    (caller should not process it further), False if the flow isn't
    active. Mirrors report_flow.py's handle_contact_text_input() shape."""
    state = context.user_data.get("profile_flow_state")
    if state not in _TEXT_INPUT_STATES:
        return False

    conn = platform_db.get_connection()
    platform_db.init_schema(conn)
    telegram_user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    if state == AWAITING_EXISTING_USERNAME:
        row = conn.execute("SELECT username FROM student_profiles WHERE username=?", (text,)).fetchone()
        if not row:
            await update.message.reply_text(
                f"No 1LAVYA username \"{text}\" found -- please check the spelling and try again, "
                f"or type /start to go back."
            )
            return True
        platform_db.execute_with_retry(
            conn, "UPDATE students SET lavya_username=? WHERE telegram_user_id=?",
            (row[0], telegram_user_id),
        )
        context.user_data["profile_flow_state"] = None
        await update.message.reply_text(f"✅ Linked to your existing username: <b>{row[0]}</b>", parse_mode="HTML")
        await _show_menu(update.message, context, telegram_user_id, edit=False)
        return True

    if state == AWAITING_NEW_USERNAME:
        username = _valid_username(text)
        if not username:
            await update.message.reply_text(
                f"Usernames must be {MIN_USERNAME_LEN}-{MAX_USERNAME_LEN} characters, "
                f"letters/numbers/underscore only -- please try again."
            )
            return True
        exists = conn.execute("SELECT 1 FROM student_profiles WHERE username=?", (username,)).fetchone()
        if exists:
            await update.message.reply_text(f"Sorry, \"{username}\" is already taken -- please try a different username.")
            return True
        context.user_data["profile_flow_pending_username"] = username
        context.user_data["profile_flow_state"] = CONFIRMING_NEW_USERNAME
        keyboard = [[
            InlineKeyboardButton("✅ Confirm (permanent)", callback_data="profileconfirm:yes"),
            InlineKeyboardButton("✏️ Re-type", callback_data="profileconfirm:retry"),
        ]]
        await update.message.reply_text(
            f"Is this correct? <b>{username}</b>\n\n⚠️ <b>This cannot be changed once confirmed.</b>",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return True

    if state == AWAITING_DISPLAY_NAME:
        platform_db.execute_with_retry(
            conn, "UPDATE student_profiles SET display_name=?, updated_at=? WHERE username=(SELECT lavya_username FROM students WHERE telegram_user_id=?)",
            (text, _now(), telegram_user_id),
        )
        context.user_data["profile_flow_state"] = None
        await update.message.reply_text(f"✅ Display name updated: {text}")
        await _show_menu(update.message, context, telegram_user_id, edit=False)
        return True

    if state == AWAITING_EXAM_ATTEMPT_OTHER:
        platform_db.execute_with_retry(
            conn, "UPDATE student_profiles SET exam_attempt=?, updated_at=? WHERE username=(SELECT lavya_username FROM students WHERE telegram_user_id=?)",
            (text, _now(), telegram_user_id),
        )
        context.user_data["profile_flow_state"] = None
        await update.message.reply_text(f"✅ Target attempt updated: {text}")
        await _show_menu(update.message, context, telegram_user_id, edit=False)
        return True

    if state == AWAITING_EMAIL:
        if not contact_utils.valid_email(text):
            await update.message.reply_text("That doesn't look like a valid email address -- please try again.")
            return True
        context.user_data["profile_flow_pending_email"] = text
        context.user_data["profile_flow_state"] = CONFIRMING_EMAIL
        keyboard = [[
            InlineKeyboardButton("✅ Confirm", callback_data="profileconfirm:yes"),
            InlineKeyboardButton("✏️ Re-type", callback_data="profileconfirm:retry"),
        ]]
        await update.message.reply_text(f"Is this correct? <b>{text}</b>", parse_mode="HTML",
                                         reply_markup=InlineKeyboardMarkup(keyboard))
        return True

    if state == AWAITING_MOBILE:
        normalized = contact_utils.normalize_mobile(text)
        if not normalized:
            await update.message.reply_text("That doesn't look like a valid 10-digit mobile number -- please try again (e.g. 9876543210).")
            return True
        context.user_data["profile_flow_pending_mobile"] = normalized
        context.user_data["profile_flow_state"] = CONFIRMING_MOBILE
        keyboard = [[
            InlineKeyboardButton("✅ Confirm", callback_data="profileconfirm:yes"),
            InlineKeyboardButton("✏️ Re-type", callback_data="profileconfirm:retry"),
        ]]
        await update.message.reply_text(f"Is this correct? <b>{normalized}</b>", parse_mode="HTML",
                                         reply_markup=InlineKeyboardMarkup(keyboard))
        return True

    return False
