"""
1Lavya Study Hub Bot (Bot 1)
----------------------------
Guided menu (Category -> Course -> Level -> Subject -> Chapter/Paper) OR
free-text fuzzy search, across all three professional courses (CA, CS,
CMA) and three material categories (Study Materials, Exam Materials,
Revision Material).

Reads its file catalog from one master Excel file and serves PDFs from
telegram/assets/study_bot/<Category>/ (three flat folders, one per
category -- Study Materials / Revision Material / Exam Materials).

Everything here is generated, not hand-maintained -- see
telegram/tools/build_master_catalog.py (which itself merges
build_study_bot_catalog.py's CA output and build_cs_cma_catalog.py's
CS/CMA output, plus parsing Exam Materials filenames directly) and
_claude/skills/SKILL-study-bot-catalog-pipeline.md /
SKILL-cs-cma-toc-pipeline.md for the full pipeline. Never hand-edit the
Excel or move files around inside telegram/assets/study_bot/ -- fix the
source and re-run the build scripts, or the catalog and the files on
disk will drift apart.

SETUP (do this before running):
1. pip install python-telegram-bot rapidfuzz openpyxl pandas
2. Put the bot's API token (from BotFather) into telegram/creds.txt under
   "Name: Official1LavyaStudyBot" / "Bot Token: ..." (this file is
   gitignored, never committed), or set the TELEGRAM_STUDY_BOT_TOKEN
   environment variable (takes priority over creds.txt if both are set).
3. Run: python study_hub_bot.py
   Keep the terminal/laptop running for the bot to stay online.
"""

import os
import re
import logging
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]   # telegram/bots/study_hub_bot.py -> repo root
CREDS_PATH = REPO_ROOT / "telegram" / "creds.txt"
EXCEL_PATH = REPO_ROOT / "telegram" / "source-docs" / "StudyHub_Master_Catalog.xlsx"
STUDY_BOT_ROOT = REPO_ROOT / "telegram" / "assets" / "study_bot"

BOT_NAME_IN_CREDS = "Official1LavyaStudyBot"

FUZZY_MATCH_THRESHOLD = 65   # 0-100. Below this, we don't even suggest a match.
# 8, not 3: the same topic can legitimately exist as a separate chapter in
# more than one course/level (e.g. "Inventories" in CA Foundation AND CA
# Final) -- a low cap here silently truncates real matches, not noise. See
# SKILL-study-bot-catalog-pipeline.md's 2026-08-07 incident for the story.
TOP_N_SUGGESTIONS = 8

# Fixed, stable order -- callback_data encodes a category as its INDEX into
# this list (see the 64-byte note in browse_callback), so this order must
# never change without also invalidating any in-flight callback_data (not a
# real concern for a polling bot with no persistence across restarts, but
# don't reorder this list casually anyway).
CATEGORIES = ["Study Materials", "Exam Materials", "Revision Material"]
CATEGORY_ICONS = {
    "Study Materials": "\U0001F4D8",   # 📘
    "Exam Materials": "\U0001F4C4",    # 📄
    "Revision Material": "\U0001F4DD",  # 📝
}


def load_token_from_creds(bot_name: str, creds_path: Path):
    """Parse 'Name: X' / 'Bot Token: Y' blocks out of telegram/creds.txt.
    Returns None if the file or the named block isn't found -- never
    raises, so a missing creds.txt just falls through to the env var
    check in main() with a clear error message."""
    if not creds_path.exists():
        return None
    text = creds_path.read_text(encoding="utf-8")
    for block in re.split(r"\n\s*\n", text.strip()):
        name_m = re.search(r"^Name:\s*(.+)$", block, re.MULTILINE)
        token_m = re.search(r"^Bot [Tt]oken:\s*(.+)$", block, re.MULTILINE)
        if name_m and token_m and name_m.group(1).strip() == bot_name:
            return token_m.group(1).strip()
    return None


BOT_TOKEN = os.environ.get("TELEGRAM_STUDY_BOT_TOKEN") or load_token_from_creds(BOT_NAME_IN_CREDS, CREDS_PATH)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CATALOG — loaded from Excel once at startup
# ---------------------------------------------------------------------------
TEXT_COLUMNS = [
    "Category", "Course", "Level", "Subject", "Label", "ShortLabel",
    "PaperType", "Session", "SetLabel", "DocType", "Keywords", "FileName",
]


class Catalog:
    def __init__(self, excel_path: Path):
        self.excel_path = excel_path
        self.df = None
        self.load()

    def load(self):
        df = pd.read_excel(self.excel_path, sheet_name="Catalog")
        df = df.dropna(subset=["FileName"]).reset_index(drop=True).copy()
        for col in TEXT_COLUMNS:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()
        df["ChapterNo"] = pd.to_numeric(df["ChapterNo"], errors="coerce")
        self.df = df
        logger.info(f"Loaded {len(df)} rows from master catalog "
                    f"({(df['Category']=='Study Materials').sum()} Study, "
                    f"{(df['Category']=='Exam Materials').sum()} Exam, "
                    f"{(df['Category']=='Revision Material').sum()} Revision).")

    # -- browse-tree helpers ------------------------------------------------
    def courses_for_category(self, category):
        sub = self.df[self.df["Category"] == category]
        return sorted(sub["Course"].unique().tolist())

    def levels_for(self, category, course):
        sub = self.df[(self.df["Category"] == category) & (self.df["Course"] == course)]
        return sorted(sub["Level"].unique().tolist())

    def subjects_for(self, category, course, level):
        sub = self.df[
            (self.df["Category"] == category) & (self.df["Course"] == course) & (self.df["Level"] == level)
        ]
        return sorted(sub["Subject"].unique().tolist())

    def chapters_for(self, category, course, level, subject):
        """Study/Revision Materials: every row is one chapter/file. Each
        dict also carries its stable catalog row id under 'row_id' --
        Telegram callback_data has a hard 64-byte limit, so callers must
        use this id (not the FileName or Label, which can be much
        longer) when building a callback_data string."""
        sub = self.df[
            (self.df["Category"] == category) & (self.df["Course"] == course)
            & (self.df["Level"] == level) & (self.df["Subject"] == subject)
        ]
        sub = sub.sort_values(["ChapterNo", "Label"], na_position="last")
        return [dict(row, row_id=idx) for idx, row in sub.iterrows()]

    def paper_types_for(self, category, course, level, subject):
        sub = self.df[
            (self.df["Category"] == category) & (self.df["Course"] == course)
            & (self.df["Level"] == level) & (self.df["Subject"] == subject)
        ]
        return sorted(p for p in sub["PaperType"].unique().tolist() if p)

    def exam_files_for(self, category, course, level, subject, paper_type):
        sub = self.df[
            (self.df["Category"] == category) & (self.df["Course"] == course)
            & (self.df["Level"] == level) & (self.df["Subject"] == subject)
            & (self.df["PaperType"] == paper_type)
        ]
        sub = sub.sort_values(["Session", "SetLabel", "DocType"])
        return [dict(row, row_id=idx) for idx, row in sub.iterrows()]

    def get_row_by_id(self, row_id):
        """Look up a row by its stable catalog row id (the df index at
        load time -- see load()'s reset_index(drop=True)). Returns None
        for an out-of-range/garbage id instead of raising, since row_id
        can come straight from unvalidated callback_data."""
        try:
            row_id = int(row_id)
            return self.df.iloc[row_id].to_dict()
        except (ValueError, IndexError):
            return None

    # -- free-text search -----------------------------------------------
    def search_text(self, query: str, top_n=TOP_N_SUGGESTIONS):
        """Fuzzy match free text against every descriptive column, across
        all categories/courses at once. Returns (score, row_id, row_dict)
        tuples -- row_id is this row's stable catalog id, for the same
        64-byte callback_data reason as chapters_for() above."""
        query_clean = query.strip().lower()

        candidates = []  # (score, row_id, row_dict)
        for idx, row in self.df.iterrows():
            searchable_parts = [
                str(row.get("Label", "")),
                str(row.get("Subject", "")),
                str(row.get("Course", "")),
                str(row.get("Level", "")),
                str(row.get("Keywords", "")),
                str(row.get("PaperType", "")),
                str(row.get("Session", "")),
            ]
            chno = row.get("ChapterNo")
            if pd.notna(chno):
                searchable_parts += [f"chapter {chno:g}", f"ch {chno:g}", f"{chno:g}"]
            searchable = " | ".join(searchable_parts).lower()
            score = fuzz.partial_ratio(query_clean, searchable)
            score = max(score, fuzz.token_sort_ratio(query_clean, searchable))
            candidates.append((score, idx, row.to_dict()))

        candidates.sort(key=lambda x: x[0], reverse=True)
        return [c for c in candidates if c[0] >= FUZZY_MATCH_THRESHOLD][:top_n]


catalog = Catalog(EXCEL_PATH)

# ---------------------------------------------------------------------------
# HANDLERS
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = (
        "*Welcome to 1Lavya Study Hub* \U0001F4DA\n\n"
        "Covers *CA*, *CS*, and *CMA* — Study Materials, Exam Materials "
        "(MTP/PYQ/RTP), and Revision Material.\n\n"
        "You can either:\n"
        "1️⃣ Tap *Browse* to pick Category → Course → Level → Subject, or\n"
        "2️⃣ Just *type* what you need directly "
        "(e.g. `CA Inter cash flow` or `CS company law`)\n"
    )
    keyboard = [[InlineKeyboardButton("\U0001F4C2 Browse", callback_data="browse:start")]]
    await update.message.reply_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def browse_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    # callback_data shapes, all well under Telegram's 64-byte cap because
    # every variable-length piece (Subject, Session, ...) is passed as an
    # INDEX into a deterministic sorted list, never as the literal string --
    # see SKILL-study-bot-catalog-pipeline.md §6 for the incident that
    # taught us this the hard way:
    #   browse:start
    #   cat:{cat_idx}
    #   crs:{cat_idx}:{course}
    #   lvl:{cat_idx}:{course}:{level}
    #   subj:{cat_idx}:{course}:{level}:{subj_idx}
    #   pt:{cat_idx}:{course}:{level}:{subj_idx}:{paper_type}
    #   file:{row_id}
    parts = data.split(":")
    action = parts[0]

    if action == "browse" and parts[1] == "start":
        keyboard = [
            [InlineKeyboardButton(f"{CATEGORY_ICONS.get(c, '')} {c}", callback_data=f"cat:{i}")]
            for i, c in enumerate(CATEGORIES)
        ]
        await query.edit_message_text(
            "Select a *Category*:", parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "cat":
        cat_idx = int(parts[1])
        category = CATEGORIES[cat_idx]
        courses = catalog.courses_for_category(category)
        if not courses:
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="browse:start")]]
            await query.edit_message_text(
                f"No *{category}* available yet — check back soon!",
                parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return
        keyboard = [[InlineKeyboardButton(c, callback_data=f"crs:{cat_idx}:{c}")] for c in courses]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="browse:start")])
        await query.edit_message_text(
            f"Category: *{category}*\nSelect your *Course*:", parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "crs":
        cat_idx, course = int(parts[1]), parts[2]
        category = CATEGORIES[cat_idx]
        levels = catalog.levels_for(category, course)
        keyboard = [
            [InlineKeyboardButton(lv, callback_data=f"lvl:{cat_idx}:{course}:{lv}")] for lv in levels
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"cat:{cat_idx}")])
        await query.edit_message_text(
            f"Category: *{category}* | Course: *{course}*\nSelect your *Level*:",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "lvl":
        cat_idx, course, level = int(parts[1]), parts[2], parts[3]
        category = CATEGORIES[cat_idx]
        subjects = catalog.subjects_for(category, course, level)
        # subject INDEX, not name, in callback_data -- some subject names
        # (e.g. "Advanced Auditing, Assurance & Professional Ethics") blow
        # past the 64-byte cap once a prefix is added. subjects_for() is
        # deterministic given the same loaded catalog, so the index
        # resolves back to the same subject in the "subj" branch below.
        keyboard = [
            [InlineKeyboardButton(s, callback_data=f"subj:{cat_idx}:{course}:{level}:{i}")]
            for i, s in enumerate(subjects)
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"crs:{cat_idx}:{course}")])
        await query.edit_message_text(
            f"Category: *{category}* | Course: *{course}* | Level: *{level}*\nSelect your *Subject*:",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "subj":
        cat_idx, course, level, subj_idx = int(parts[1]), parts[2], parts[3], int(parts[4])
        category = CATEGORIES[cat_idx]
        subjects = catalog.subjects_for(category, course, level)
        subject = subjects[subj_idx]

        if category == "Exam Materials":
            paper_types = catalog.paper_types_for(category, course, level, subject)
            keyboard = [
                [InlineKeyboardButton(pt, callback_data=f"pt:{cat_idx}:{course}:{level}:{subj_idx}:{pt}")]
                for pt in paper_types
            ]
            keyboard.append(
                [InlineKeyboardButton("⬅️ Back", callback_data=f"lvl:{cat_idx}:{course}:{level}")]
            )
            await query.edit_message_text(
                f"Subject: *{subject}*\nSelect *Paper Type*:",
                parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            chapters = catalog.chapters_for(category, course, level, subject)
            keyboard = []
            for ch in chapters:
                chno = ch.get("ChapterNo")
                label = f"Ch {chno:g} - {ch['Label']}" if pd.notna(chno) else ch["Label"]
                keyboard.append([InlineKeyboardButton(label[:80], callback_data=f"file:{ch['row_id']}")])
            keyboard.append(
                [InlineKeyboardButton("⬅️ Back", callback_data=f"lvl:{cat_idx}:{course}:{level}")]
            )
            await query.edit_message_text(
                f"Category: *{category}* | Course: *{course}* | Level: *{level}* | Subject: *{subject}*\n"
                f"Select a *Chapter*:",
                parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
            )

    elif action == "pt":
        cat_idx, course, level, subj_idx, paper_type = int(parts[1]), parts[2], parts[3], int(parts[4]), parts[5]
        category = CATEGORIES[cat_idx]
        subjects = catalog.subjects_for(category, course, level)
        subject = subjects[subj_idx]
        files = catalog.exam_files_for(category, course, level, subject, paper_type)
        keyboard = [[InlineKeyboardButton(f["Label"][:80], callback_data=f"file:{f['row_id']}")] for f in files]
        keyboard.append(
            [InlineKeyboardButton("⬅️ Back", callback_data=f"subj:{cat_idx}:{course}:{level}:{subj_idx}")]
        )
        await query.edit_message_text(
            f"Subject: *{subject}* | Paper Type: *{paper_type}*\nSelect a file:",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "file":
        row_id = parts[1]
        await send_file(query, context, row_id)


async def send_file(query_or_update, context, row_id):
    """Send the PDF from local disk to the user, looked up by catalog row_id
    (see Catalog.get_row_by_id -- never by filename, which can exceed
    Telegram's 64-byte callback_data limit)."""
    row = catalog.get_row_by_id(row_id)

    chat_id = (
        query_or_update.message.chat_id
        if hasattr(query_or_update, "message") and query_or_update.message
        else query_or_update.effective_chat.id
    )

    if not row:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, that file could not be found. Please try /start again.",
        )
        return

    filename = row["FileName"]
    filepath = STUDY_BOT_ROOT / row["Category"] / filename

    if not filepath.exists():
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, that file could not be found on the server. Please contact support.",
        )
        return

    caption = (
        f"\U0001F4C4 {row.get('Label', filename)}\n"
        f"{row.get('Category','')} — {row.get('Course','')} {row.get('Level','')} — "
        f"{row.get('Subject','')}"
    )
    with open(filepath, "rb") as f:
        await context.bot.send_document(chat_id=chat_id, document=f, filename=filename, caption=caption)


async def free_text_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles direct text like 'CA Inter cash flow' or 'CS company law',
    searched across every course and category at once."""
    query_text = update.message.text
    results = catalog.search_text(query_text)

    if not results:
        await update.message.reply_text(
            "I couldn't find a close match. Try /start to browse by menu instead, "
            "or rephrase (e.g. include the course, chapter number, or subject name)."
        )
        return

    if len(results) == 1 and results[0][0] >= 90:
        # confident single match -> send directly
        _, row_id, _ = results[0]
        await send_file(update, context, row_id)
        return

    # otherwise show top matches as buttons
    keyboard = []
    for score, row_id, row in results:
        # Category/Course/Level are all included (not just Subject) because
        # the same title can legitimately appear more than once across
        # them (e.g. "Inventories" in both CA Foundation and CA Final;
        # "Cash Flow Statement" as both a chapter AND an exam question set)
        # -- without them, two buttons could be indistinguishable.
        label = f"{row.get('Label', row['FileName'])} — {row.get('Category','')} · {row.get('Course','')} {row.get('Level','')} {row.get('Subject','')}"
        # row_id, never FileName, in callback_data -- see the 64-byte note in browse_callback.
        keyboard.append([InlineKeyboardButton(label[:80], callback_data=f"file:{row_id}")])
    await update.message.reply_text(
        "I found a few possible matches — please pick one:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def main():
    if not BOT_TOKEN:
        raise SystemExit(
            f"No bot token found. Either add a "
            f"'Name: {BOT_NAME_IN_CREDS}' / 'Bot Token: ...' block to "
            f"{CREDS_PATH}, or set the TELEGRAM_STUDY_BOT_TOKEN "
            f"environment variable."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(browse_callback, pattern=r"^(browse|cat|crs|lvl|subj|pt|file):"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, free_text_search))

    logger.info("1Lavya Study Hub Bot is starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
