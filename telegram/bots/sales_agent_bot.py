"""
telegram/bots/sales_agent_bot.py -- "1LAVYA Faculty Search" sales-agent bot (sample build, 2026-08-24)
--------------------------------------------------------------------------------------------------
One generic bot script, reused per client institute -- same pattern as study_hub_bot.py
being reused per faculty tenant. Which client this process serves is picked with the
SALES_AGENT_CLIENT env var (default: "coceducation", the one client with a real catalog
built so far). Adding vcgurukul / bbvirtuals / vsmartacademy later is: run
extract_catalog.py-equivalent for that client's own site-mirror, add a
client_config.json next to it, start a new process with SALES_AGENT_CLIENT set --
no code change here.

Per-client folder layout (telegram/comparator/sales-agent/<client>/):
    client_config.json  -- display name, token env var, file paths (see coceducation/)
    catalog.json         -- the knowledge base this bot actually answers from,
                             built by extract_catalog.py from that client's own
                             site-mirror/ -- never hand-edited, re-run the extractor
                             after a fresh mirror instead
    sales_agent.db        -- this client's OWN sqlite file (logs searches/views/
                             clicks only -- no PII beyond the student's Telegram
                             user id). Deliberately NOT the shared platform.db --
                             each client's interaction data stays in its own file,
                             one per client, per Pranav's explicit instruction
                             (2026-08-24).

What this bot does (confirmed scope, 2026-08-24): answers a student's free-text or
menu-driven questions about ONE client's own course catalog (price, faculty, what's
included, how it's delivered) using ONLY that client's own catalog.json, and -- when
the student is ready to buy -- hands them the REAL course/website URL on that client's
own domain. It never takes a payment itself; "purchase" always means "here is the
link," matching how this was scoped.

Token: reads {bot_token_env} from the environment (falls back to the client config's
own placeholder string, which will refuse to start it -- see resolve_bot_token()).
Never hardcode a real token into this file or into client_config.json.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from rapidfuzz import fuzz, process
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("sales_agent_bot")

REPO_ROOT = Path(__file__).resolve().parents[2]
SALES_AGENT_ROOT = REPO_ROOT / "telegram" / "comparator" / "sales-agent"

CLIENT_SLUG = os.environ.get("SALES_AGENT_CLIENT", "coceducation")
CLIENT_DIR = SALES_AGENT_ROOT / CLIENT_SLUG

PAGE_SIZE = 8  # courses per page in "Browse by Exam" listings
SEARCH_RESULT_LIMIT = 6


# --------------------------------------------------------------------------------
# Client config / catalog / DB loading
# --------------------------------------------------------------------------------

def load_client_config() -> dict:
    config_path = CLIENT_DIR / "client_config.json"
    if not config_path.exists():
        raise SystemExit(
            f"No client_config.json for '{CLIENT_SLUG}' at {config_path}. "
            f"Set SALES_AGENT_CLIENT to a folder that has one, e.g. 'coceducation'."
        )
    return json.loads(config_path.read_text(encoding="utf-8"))


def load_catalog(config: dict) -> dict:
    catalog_path = CLIENT_DIR / config["catalog_path"]
    if not catalog_path.exists():
        raise SystemExit(
            f"No catalog at {catalog_path}. Run extract_catalog.py for '{CLIENT_SLUG}' first."
        )
    return json.loads(catalog_path.read_text(encoding="utf-8"))


def resolve_bot_token(config: dict) -> str | None:
    env_name = config.get("bot_token_env")
    token = os.environ.get(env_name) if env_name else None
    if token:
        return token
    placeholder = config.get("bot_token_placeholder")
    if placeholder:
        logger.warning(
            "No real token in env var %s -- using placeholder %r. "
            "This bot will NOT be able to connect to Telegram until a real "
            "BotFather token is set in that env var.",
            env_name,
            placeholder,
        )
    return None


DB_PATH = CLIENT_DIR / "sales_agent.db"


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sales_agent_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,       -- 'start' | 'search' | 'browse' | 'course_view' | 'buy_click'
                query_text TEXT,                -- free-text search query, if any
                course_slug TEXT,                -- course involved, if any
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def log_event(user_id: int, event_type: str, *, query_text: str | None = None, course_slug: str | None = None) -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO sales_agent_events (telegram_user_id, event_type, query_text, course_slug, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, event_type, query_text, course_slug, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    except Exception:
        logger.exception("Failed to log sales_agent_events row (event_type=%s)", event_type)
    finally:
        conn.close()


CONFIG = load_client_config()
CATALOG = load_catalog(CONFIG)
COURSES: list[dict] = CATALOG["courses"]
ORG = CATALOG["org"]
BOT_TOKEN = resolve_bot_token(CONFIG)

# Course lookup by small integer index, not by slug -- callback_data has Telegram's
# hard 64-byte limit, and several real slugs here (e.g. long "By <faculty>" titles)
# would blow past it once prefixed. This exact bug class has bitten this platform
# multiple times before (see CLAUDE.md's callback-data-collision history) --
# building it index-based from day one avoids repeating it here.
def _course_by_index(index: int) -> dict | None:
    if 0 <= index < len(COURSES):
        return COURSES[index]
    return None


# Precomputed search corpus: "title -- faculty" per course, same order as COURSES.
_SEARCH_CORPUS = [f"{c['title']} {c['faculty']}".strip() for c in COURSES]


def search_courses(query: str, limit: int = SEARCH_RESULT_LIMIT) -> list[tuple[int, dict, float]]:
    """Returns [(course_index, course_dict, score), ...] best matches first."""
    matches = process.extract(
        query,
        _SEARCH_CORPUS,
        scorer=fuzz.WRatio,
        limit=limit,
    )
    results = []
    for _text, score, idx in matches:
        if score < 45:  # below this, the match is noise, not a real hit
            continue
        results.append((idx, COURSES[idx], score))
    return results


# --------------------------------------------------------------------------------
# Rendering helpers
# --------------------------------------------------------------------------------

def main_menu_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🔍 Search a course", callback_data="menu:search")],
        [InlineKeyboardButton("📚 Browse by exam", callback_data="menu:browse")],
        [InlineKeyboardButton("ℹ️ About " + ORG["name"], callback_data="menu:about")],
        [InlineKeyboardButton("📞 Contact / Enquiry", callback_data="menu:contact")],
        [InlineKeyboardButton("🌐 Visit " + ORG["domain"].replace("https://", ""), url=ORG["domain"])],
    ]
    return InlineKeyboardMarkup(rows)


def exam_group_keyboard() -> InlineKeyboardMarkup:
    counts = {}
    for c in COURSES:
        counts[c["exam_group"]] = counts.get(c["exam_group"], 0) + 1
    rows = [
        [InlineKeyboardButton(f"{g} ({counts.get(g, 0)} courses)", callback_data=f"list:{g}:0")]
        for g in CONFIG.get("exam_groups", sorted(counts))
        if counts.get(g)
    ]
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="back:menu")])
    return InlineKeyboardMarkup(rows)


def course_list_keyboard(group: str, page: int) -> InlineKeyboardMarkup:
    filtered = [(i, c) for i, c in enumerate(COURSES) if c["exam_group"] == group]
    start = page * PAGE_SIZE
    page_items = filtered[start : start + PAGE_SIZE]

    rows = []
    for idx, c in page_items:
        label = c["title"]
        if len(label) > 55:
            label = label[:52] + "..."
        rows.append([InlineKeyboardButton(label, callback_data=f"course:{idx}")])

    nav = []
    if start > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"list:{group}:{page - 1}"))
    if start + PAGE_SIZE < len(filtered):
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"list:{group}:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("⬅️ Back to exams", callback_data="menu:browse")])
    return InlineKeyboardMarkup(rows)


def search_results_keyboard(results: list[tuple[int, dict, float]]) -> InlineKeyboardMarkup:
    rows = []
    for idx, c, _score in results:
        label = c["title"]
        if len(label) > 55:
            label = label[:52] + "..."
        rows.append([InlineKeyboardButton(label, callback_data=f"course:{idx}")])
    rows.append([InlineKeyboardButton("⬅️ Back to menu", callback_data="back:menu")])
    return InlineKeyboardMarkup(rows)


# The handful of highlights fields most useful to a student deciding whether to buy --
# the full highlights dict has ~12 fields (system requirements, refund policy, etc.)
# that would make every course card a wall of text if shown in full.
HEADLINE_HIGHLIGHT_KEYS = [
    "Course Content",
    "No's of Lecture",
    "Lecture Duration",
    "Video Language",
    "Doubt Solving",
]


def format_course_card(course: dict) -> str:
    lines = [f"*{course['title']}*"]
    if course["faculty"]:
        lines.append(f"👩‍🏫 Faculty: {course['faculty']}")
    lines.append(f"📂 Exam: {course['exam_group']}")

    price = course.get("price_inr")
    mrp = course.get("mrp_inr")
    if price is not None:
        price_line = f"💰 ₹{price:,}"
        if mrp and mrp > price:
            price_line += f"  ~~₹{mrp:,}~~"
            if course.get("discount_pct"):
                price_line += f"  ({course['discount_pct']}% off)"
        lines.append(price_line)

    for key in HEADLINE_HIGHLIGHT_KEYS:
        value = course["highlights"].get(key)
        if value:
            lines.append(f"• *{key}:* {value}")

    for attr_name, options in course.get("attributes", {}).items():
        lines.append(f"• *{attr_name}:* {', '.join(options)}")

    return "\n".join(lines)


def course_detail_keyboard(course: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🛒 Buy Now / View Full Details", url=course["url"])],
            [InlineKeyboardButton("⬅️ Back to menu", callback_data="back:menu")],
        ]
    )


# --------------------------------------------------------------------------------
# Handlers
# --------------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log_event(update.effective_user.id, "start")
    text = (
        f"👋 Welcome to *{CONFIG['bot_display_name']}*!\n\n"
        f"Ask me anything about {ORG['name']}'s courses -- price, faculty, what's "
        f"included, how classes run -- or use the menu below."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())


async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "back:menu":
        await query.edit_message_text(
            "Main menu:",
            reply_markup=main_menu_keyboard(),
        )
        return

    if data == "menu:search":
        await query.edit_message_text(
            "Type what you're looking for -- e.g. a subject, a faculty name, "
            "or an exam (\"CMA foundation\", \"Santosh Kumar\", \"strategic financial "
            "management\") -- and I'll find matching courses.",
        )
        return

    if data == "menu:browse":
        log_event(user_id, "browse")
        await query.edit_message_text("Which exam?", reply_markup=exam_group_keyboard())
        return

    if data == "menu:about":
        text = f"*{ORG['name']}*\n\n{ORG['about']}\n\n🌐 {ORG['domain']}"
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Back", callback_data="back:menu")]]
            ),
        )
        return

    if data == "menu:contact":
        contact = ORG["contact"]
        lines = [f"*{ORG['name']} -- Contact*", ""]
        lines.append("📞 Call Sales: " + " | ".join(contact.get("call_sales", [])))
        if contact.get("purchase_enquiry"):
            lines.append(f"🧾 Purchase Enquiry: {contact['purchase_enquiry']}")
        if contact.get("tech_login_support"):
            lines.append(f"🛠 Tech / Login Support: {contact['tech_login_support']}")
        if contact.get("whatsapp"):
            lines.append(f"💬 WhatsApp: {contact['whatsapp']}")
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Back", callback_data="back:menu")]]
            ),
        )
        return

    if data.startswith("list:"):
        _, group, page_str = data.split(":", 2)
        page = int(page_str)
        await query.edit_message_text(
            f"*{group}* courses:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=course_list_keyboard(group, page),
        )
        return

    if data.startswith("course:"):
        idx = int(data.split(":", 1)[1])
        course = _course_by_index(idx)
        if course is None:
            await query.edit_message_text("Sorry, that course isn't available anymore.", reply_markup=main_menu_keyboard())
            return
        log_event(user_id, "course_view", course_slug=course["slug"])
        await query.edit_message_text(
            format_course_card(course),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=course_detail_keyboard(course),
            disable_web_page_preview=True,
        )
        return

    # Unknown callback -- shouldn't happen, but never leave the tap unanswered.
    await query.edit_message_text("Something went wrong -- let's start over.", reply_markup=main_menu_keyboard())


async def free_text_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    if not text:
        return
    user_id = update.effective_user.id
    log_event(user_id, "search", query_text=text)

    results = search_courses(text)
    if not results:
        await update.message.reply_text(
            "I couldn't find a course matching that. Try a different subject, faculty "
            "name, or use \"Browse by exam\" instead.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await update.message.reply_text(
        f"Here's what I found for “{text}”:",
        reply_markup=search_results_keyboard(results),
    )


def build_application() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, free_text_search))
    return app


def main() -> None:
    init_db()
    logger.info(
        "Loaded %d courses for client '%s' (%s)",
        len(COURSES),
        CLIENT_SLUG,
        ORG.get("name"),
    )
    if not BOT_TOKEN:
        logger.error(
            "Refusing to start: no real Telegram bot token configured for client "
            "'%s'. Set the %s environment variable to a real BotFather token "
            "and re-run.",
            CLIENT_SLUG,
            CONFIG.get("bot_token_env"),
        )
        return
    app = build_application()
    logger.info("Starting %s ...", CONFIG["bot_display_name"])
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
