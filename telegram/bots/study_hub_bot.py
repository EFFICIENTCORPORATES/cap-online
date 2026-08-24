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

This script is BOT-ID-AWARE (tenant-aware since 2026-08-09; refactored onto
the master bot mapping 2026-08-10) -- the same file serves the flagship
1LAVYA bot AND every faculty white-label study bot, parameterized purely by
which BOT_ID it's started with. BOT_ID selects a row in
telegram/config/bots.json (the master mapping -- which bot, which token,
which script); that row's tenant_id then selects a row in
telegram/config/tenants.json (what that tenant teaches -- content_scope).
See bots.README.md / tenants.README.md for both registries and the "plug
and play" design -- adding a new faculty's Study bot is a bots.json entry
(+ a tenants.json entry if they're new), not a code change, as long as
they're only licensing a slice of the shared catalog.

SETUP (do this before running):
1. pip install python-telegram-bot[job-queue] rapidfuzz openpyxl pandas python-dotenv
2. Bot token resolution, per BOT_ID (see resolve_bot_token()):
   - The flagship "1lavya-studyhub" bot still resolves via telegram/creds.txt
     ("Name: Official1LavyaStudyBot" / "Bot Token: ...") as a backward-compat
     fallback, OR the TELEGRAM_STUDY_BOT_TOKEN env var.
   - Every other bot resolves via the env var named in its bots.json
     `bot_token_env` field -- put the real value in telegram/.env
     (gitignored; copy telegram/.env.example for the template). This script
     loads telegram/.env automatically at startup.
3. Choose which bot this process serves by setting the BOT_ID environment
   variable before launching (defaults to "1lavya-studyhub" if unset, i.e.
   today's original single-tenant behavior; also accepts the older
   TENANT_ID name as a fallback, for single-bot tenants where bot_id ==
   tenant_id -- see bots.json's own note on that). BOT_ID is a per-run
   selector, not a secret -- set it in your shell, not in .env.
   PowerShell example:
       $env:BOT_ID = "capranav-study"; python study_hub_bot.py
4. Run: python study_hub_bot.py
   Keep the terminal/laptop running for the bot to stay online. Run a
   second, independent process (different terminal, different BOT_ID) per
   additional bot -- Telegram forces one token = one running bot process,
   this script is just reused, not duplicated. Or use
   telegram/tools/manage_bots.py to start every `active` bot in bots.json
   at once instead of doing this by hand.
"""

import os
import re
import sys
import json
import logging
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz
from dotenv import load_dotenv

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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
import db as platform_db  # noqa: E402 -- must follow the sys.path.insert() above
import log_rotation  # noqa: E402 -- telegram/database/log_rotation.py, Layer 1 of the log-rotation policy (2026-08-18)
import profile_flow  # noqa: E402 -- telegram/bots/profile_flow.py, the "profile"/"change profile" identity flow (2026-08-11)
import report_flow  # noqa: E402 -- telegram/bots/report_flow.py, now also reachable from Study Hub via its on-demand "report"/"analysis"/"email"/"mail" trigger (2026-08-11)
from telegram_safety import safe_edit_message_text  # noqa: E402 -- 2026-08-18, see that module's own docstring
import cancel_utils  # noqa: E402 -- telegram/bots/cancel_utils.py, universal "get me out of this" escape hatch (2026-08-16)
import fuzzy_trigger  # noqa: E402 -- telegram/bots/fuzzy_trigger.py, "did you mean X?" typo confirmation (2026-08-16)
import activity_logger  # noqa: E402 -- telegram/bots/activity_logger.py, the fine-grained activity log + correlation IDs (2026-08-17)
import rate_limiter  # noqa: E402 -- telegram/bots/rate_limiter.py, per-user flood/abuse controls (2026-08-24, SECURITY.md Phase 1)
import input_guard  # noqa: E402 -- telegram/bots/input_guard.py, free-text sanitization (2026-08-24, SECURITY.md Phase 1)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]   # telegram/bots/study_hub_bot.py -> repo root
CREDS_PATH = REPO_ROOT / "telegram" / "creds.txt"
EXCEL_PATH = REPO_ROOT / "telegram" / "source-docs" / "StudyHub_Master_Catalog.xlsx"
STUDY_BOT_ROOT = REPO_ROOT / "telegram" / "assets" / "study_bot"
TENANTS_PATH = REPO_ROOT / "telegram" / "config" / "tenants.json"
BOTS_PATH = REPO_ROOT / "telegram" / "config" / "bots.json"

load_dotenv(REPO_ROOT / "telegram" / ".env")   # secrets (faculty bot tokens) live here, gitignored

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


def load_bot(bot_id: str, bots_path: Path) -> dict:
    """Look up one bot's config block from telegram/config/bots.json (the
    master mapping). Raises SystemExit with the list of known bot_ids on a
    typo/unknown id -- never silently falls back to a different bot's
    config (that would mean serving one faculty's content under another's
    token, a real harm, not just a confusing error)."""
    data = json.loads(bots_path.read_text(encoding="utf-8"))
    for b in data["bots"]:
        if b["bot_id"] == bot_id:
            return b
    known = [b["bot_id"] for b in data["bots"]]
    raise SystemExit(f"Unknown BOT_ID '{bot_id}' -- no matching entry in {bots_path}. Known bot_ids: {known}")


def load_tenant(tenant_id: str, tenants_path: Path) -> dict:
    """Look up one tenant's config block from telegram/config/tenants.json.
    Raises SystemExit with the list of known tenant_ids on a typo/unknown
    id -- never silently falls back to a different tenant's config."""
    data = json.loads(tenants_path.read_text(encoding="utf-8"))
    for t in data["tenants"]:
        if t["tenant_id"] == tenant_id:
            return t
    known = [t["tenant_id"] for t in data["tenants"]]
    raise SystemExit(
        f"Unknown tenant_id '{tenant_id}' (from bots.json's BOT_ID entry) -- no matching entry in {tenants_path}. "
        f"Known tenant_ids: {known}"
    )


def resolve_bot_token(bot: dict):
    """Env var named by the bot's bot_token_env, else (for the flagship
    "1lavya-studyhub" bot only, for backward compatibility) fall back to
    telegram/creds.txt. Returns None if nothing resolves -- main() turns
    that into a clear startup error rather than an obscure Telegram one."""
    env_name = bot.get("bot_token_env")
    token = os.environ.get(env_name) if env_name else None
    if token:
        return token
    if bot["bot_id"] == "1lavya-studyhub":
        return load_token_from_creds(BOT_NAME_IN_CREDS, CREDS_PATH)
    return None


# BOT_ID is the master-mapping selector (bots.json); TENANT_ID (older name)
# still works as a fallback for any bot whose bot_id equals its tenant_id
# (true for every single-bot tenant, e.g. "csarunchouhan" -- only a
# multi-bot tenant like Pranav's "capranav-study"/"capranav-exam" actually
# needs the newer BOT_ID name).
BOT_ID = os.environ.get("BOT_ID") or os.environ.get("TENANT_ID", "1lavya-studyhub")
BOT_CONFIG = load_bot(BOT_ID, BOTS_PATH)
TENANT_ID = BOT_CONFIG["tenant_id"]
TENANT = load_tenant(TENANT_ID, TENANTS_PATH)
BOT_TOKEN = resolve_bot_token(BOT_CONFIG)

# 1LAVYA's own flagship bots carry no branding footer (they ARE 1LAVYA);
# every white-label faculty bot gets a one-line "Powered by 1LAVYA" signature
# -- but ONLY when actually delivering content (a file/PDF), never on
# welcome/menu/question screens or other plain communication. Revised
# 2026-08-10 (Pranav: the original "every response" rule from 2026-08-09
# was too much) -- use with_brand() only at the specific call sites that
# deliver a file; everything else (menus, questions, prompts) stays plain.
BRAND_FOOTER = "\n\n_Powered by 1LAVYA_" if TENANT.get("kind") == "faculty" else ""


def with_brand(text: str) -> str:
    return f"{text}{BRAND_FOOTER}"


# Any of these, alone on a line (case-insensitive, optional trailing !/.),
# resets the conversation back to /start -- same words myfiles_hub_bot.py
# already treats as a fresh-opener greeting, plus "reset" itself. Anchored
# (^...$) so it only fires on a *standalone* greeting/reset, never as a
# false-positive substring inside a real search query.
RESET_TRIGGER_RE = re.compile(
    r"^\s*(hi+|hey+|hello+|hiya|yo|namaste|reset)\s*[!.]*\s*$", re.IGNORECASE
)

# 2026-08-18: handlers=[...] explicit now (was implicit stderr-only before)
# -- see LOGGING-ARCHITECTURE.md §6/§10 and log_rotation.py's own docstring
# for why. StreamHandler kept alongside so a manual/interactive run still
# prints to the terminal same as before; RotatingFileHandler is the new,
# BOUNDED replacement for what used to be manage_bots.py's unbounded
# OS-level stdout redirect into this exact same file path.
logging.basicConfig(
    format=activity_logger.LOG_FORMAT_WITH_CORRELATION, level=logging.INFO,
    handlers=log_rotation.build_handlers(BOT_ID),
)
logging.getLogger("httpx").setLevel(logging.WARNING)  # 2026-08-17: see LOGGING-ARCHITECTURE.md §6
activity_logger.install_correlation_filter()
logger = logging.getLogger(__name__)

# Shared platform DB (telegram/database/platform.db) -- every bot writes
# here now, not its own separate .db file. See telegram/database/db.py's
# own module docstring for the multi-process WAL/retry design this relies
# on. One connection per process, reused for the whole run (never
# reconnect per query).
DB_CONN = platform_db.get_connection()
platform_db.init_schema(DB_CONN)

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

    def editions_for(self, category, course, level, subject):
        """Distinct real Session values (e.g. "May26", "May27") among a
        subject's Study/Revision Materials rows -- sorted so the picker
        order is stable across runs. Empty list means "no edition split
        needed" (either every row shares one Session, or Session is blank
        for this subject entirely) -- callers auto-skip the Edition step
        in that case, same auto-skip convention as Course/Level/Subject
        above. First needed 2026-08-18: GST is the first subject with two
        simultaneously-live ICAI editions -- see build_master_catalog.py's
        session_from_filename() for where this value actually comes from."""
        sub = self.df[
            (self.df["Category"] == category) & (self.df["Course"] == course)
            & (self.df["Level"] == level) & (self.df["Subject"] == subject)
        ]
        sessions = sorted(s for s in sub["Session"].unique().tolist() if s)
        return sessions if len(sessions) > 1 else []

    def chapters_for(self, category, course, level, subject, edition=None):
        """Study/Revision Materials: every row is one chapter/file. Each
        dict also carries its stable catalog row id under 'row_id' --
        Telegram callback_data has a hard 64-byte limit, so callers must
        use this id (not the FileName or Label, which can be much
        longer) when building a callback_data string.

        edition, when given, filters to just that Session -- used once a
        student has picked an Edition for a subject with >1 live one (see
        editions_for() above). None (the default) means "no filter",
        correct both for single-edition subjects and for the small number
        of Revision Material rows that may have no Session at all."""
        sub = self.df[
            (self.df["Category"] == category) & (self.df["Course"] == course)
            & (self.df["Level"] == level) & (self.df["Subject"] == subject)
        ]
        if edition is not None:
            sub = sub[sub["Session"] == edition]
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


def scoped_catalog_df(df, content_scope):
    """Restrict the loaded catalog to a tenant's licensed slice. "ALL"
    (the flagship/platform tenants) is a no-op. A faculty's content_scope
    is a list of {course, level, subject} -- matched exactly against the
    catalog's own values (see tenants.README.md: get these strings from
    the real catalog, don't guess/abbreviate them). Re-indexed so row_id
    (the df index Catalog.get_row_by_id relies on) stays contiguous and
    stable for THIS tenant's process."""
    if content_scope == "ALL":
        return df
    mask = pd.Series(False, index=df.index)
    for s in content_scope:
        mask |= (
            (df["Course"] == s["course"])
            & (df["Level"] == s["level"])
            & (df["Subject"] == s["subject"])
        )
    return df[mask].reset_index(drop=True)


catalog = Catalog(EXCEL_PATH)
catalog.df = scoped_catalog_df(catalog.df, TENANT["content_scope"])
logger.info(
    f"Tenant '{TENANT_ID}' ({TENANT['kind']}): catalog scoped to {len(catalog.df)} rows "
    f"(content_scope={TENANT['content_scope']})."
)

# ---------------------------------------------------------------------------
# HANDLERS
# ---------------------------------------------------------------------------

def scope_description() -> str:
    """One-line summary of what this tenant's bot covers, for the welcome
    message -- computed from the tenant's own content_scope + whatever
    categories actually survived scoping, never hardcoded per faculty."""
    if TENANT["content_scope"] == "ALL":
        return (
            "Covers *CA*, *CS*, and *CMA* — Study Materials, Exam Materials "
            "(MTP/PYQ/RTP), and Revision Material."
        )
    bits = ", ".join(f"*{s['course']} {s['level']}*" for s in TENANT["content_scope"])
    cats = [c for c in CATEGORIES if catalog.courses_for_category(c)]
    cats_text = " / ".join(cats) if cats else "content"
    return f"Your dedicated hub for {bits} — {cats_text}."


def welcome_text_and_keyboard():
    """Shared by /start (a message reply) and the "mainmenu" callback
    button (a message edit) so both render identically -- see start() and
    browse_callback's "mainmenu" branch."""
    opening = TENANT.get("welcome_message") or "*Welcome to 1Lavya Study Hub* \U0001F4DA"
    text = (
        f"{opening}\n\n"
        f"{scope_description()}\n\n"
        "You can either:\n"
        "1️⃣ Tap *Browse* to pick Course → Level → Subject, or\n"
        "2️⃣ Just *type* what you need directly\n"
    )
    keyboard = [[InlineKeyboardButton("\U0001F4C2 Browse", callback_data="browse:start")]]
    # No brand footer here -- per Pranav's 2026-08-10 instruction, "Powered by
    # 1LAVYA" only appears when delivering a PDF or an answer, never on
    # welcome/menu/question screens. See with_brand()'s own docstring.
    return text, InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    platform_db.upsert_student(DB_CONN, update.effective_user)
    platform_db.log_interaction(DB_CONN, BOT_ID, update.effective_user.id, "start")
    text, markup = welcome_text_and_keyboard()
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)


def effective_course_back(cat_idx, category):
    """Where the Back button on whichever screen ends up rendered once
    Course is settled should point -- the Category picker if Course itself
    was auto-skipped (only one course in this tenant's content_scope for
    this category), else the real Course-picker screen. Recomputed fresh
    from the catalog every call (cheap, always in sync -- no state to
    thread through callback_data)."""
    return "browse:start" if len(catalog.courses_for_category(category)) == 1 else f"cat:{cat_idx}"


def effective_level_back(cat_idx, category, course):
    if len(catalog.levels_for(category, course)) == 1:
        return effective_course_back(cat_idx, category)
    return f"crs:{cat_idx}:{course}"


def effective_subject_back(cat_idx, category, course, level):
    if len(catalog.subjects_for(category, course, level)) == 1:
        return effective_level_back(cat_idx, category, course)
    return f"lvl:{cat_idx}:{course}:{level}"


async def render_chapter_list(query, context, cat_idx, category, course, level, subject,
                               edition, back_cb, return_to):
    """Shared by the "subj" branch (single-edition subjects, edition=None)
    and the "ed" branch (edition picked) -- one place renders the actual
    chapter keyboard so the two paths can never drift apart. Remembers
    return_to so send_file()'s post-download "Download more" button comes
    straight back to this exact list, not just one level up."""
    context.user_data["return_to"] = return_to
    chapters = catalog.chapters_for(category, course, level, subject, edition=edition)
    keyboard = []
    for ch in chapters:
        chno = ch.get("ChapterNo")
        label = f"Ch {chno:g} - {ch['Label']}" if pd.notna(chno) else ch["Label"]
        keyboard.append([InlineKeyboardButton(label[:80], callback_data=f"file:{ch['row_id']}")])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=back_cb)])
    edition_bit = f" | Edition: *{edition}*" if edition else ""
    await safe_edit_message_text(query,
        f"Category: *{category}* | Course: *{course}* | Level: *{level}* | Subject: *{subject}*{edition_bit}\n"
        f"Select a *Chapter*:",
        parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def browse_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await route_browse(query, context, query.data)


async def route_browse(query, context, data):
    """The actual dispatcher -- factored out of browse_callback so it can
    recurse with a SYNTHETIC data string when a tenant's content_scope
    collapses a picker step to exactly one option (e.g. a faculty scoped
    to only CMA never needs to be asked "which course?"). Recursing here
    reuses every downstream branch completely unchanged -- see
    effective_course_back()/effective_level_back()/effective_subject_back()
    above for how the resulting screen's Back button still points to the
    correct PREVIOUS REAL screen, skipping over whatever was auto-skipped.

    callback_data shapes, all well under Telegram's 64-byte cap because
    every variable-length piece (Subject, Session, ...) is passed as an
    INDEX into a deterministic sorted list, never as the literal string --
    see SKILL-study-bot-catalog-pipeline.md §6 for the incident that
    taught us this the hard way:
      browse:start
      cat:{cat_idx}
      crs:{cat_idx}:{course}
      lvl:{cat_idx}:{course}:{level}
      subj:{cat_idx}:{course}:{level}:{subj_idx}
      ed:{cat_idx}:{course}:{level}:{subj_idx}:{ed_idx}   (only for a subject with >1 live edition -- see editions_for())
      pt:{cat_idx}:{course}:{level}:{subj_idx}:{paper_type}
      file:{row_id}
      mainmenu:go   (from the post-download "Main Menu" button)
    """
    parts = data.split(":")
    action = parts[0]

    if action == "browse" and parts[1] == "start":
        keyboard = [
            [InlineKeyboardButton(f"{CATEGORY_ICONS.get(c, '')} {c}", callback_data=f"cat:{i}")]
            for i, c in enumerate(CATEGORIES)
        ]
        await safe_edit_message_text(query,
            "Select a *Category*:", parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "cat":
        cat_idx = int(parts[1])
        category = CATEGORIES[cat_idx]
        courses = catalog.courses_for_category(category)
        if not courses:
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="browse:start")]]
            await safe_edit_message_text(query,
                f"No *{category}* available yet — check back soon!",
                parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return
        if len(courses) == 1:
            # Nothing to pick -- this tenant's content_scope only has one
            # course for this category. Skip straight to Level.
            await route_browse(query, context, f"crs:{cat_idx}:{courses[0]}")
            return
        keyboard = [[InlineKeyboardButton(c, callback_data=f"crs:{cat_idx}:{c}")] for c in courses]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="browse:start")])
        await safe_edit_message_text(query,
            f"Category: *{category}*\nSelect your *Course*:", parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "crs":
        cat_idx, course = int(parts[1]), parts[2]
        category = CATEGORIES[cat_idx]
        levels = catalog.levels_for(category, course)
        if len(levels) == 1:
            await route_browse(query, context, f"lvl:{cat_idx}:{course}:{levels[0]}")
            return
        keyboard = [
            [InlineKeyboardButton(lv, callback_data=f"lvl:{cat_idx}:{course}:{lv}")] for lv in levels
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=effective_course_back(cat_idx, category))])
        await safe_edit_message_text(query,
            f"Category: *{category}* | Course: *{course}*\nSelect your *Level*:",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "lvl":
        cat_idx, course, level = int(parts[1]), parts[2], parts[3]
        category = CATEGORIES[cat_idx]
        subjects = catalog.subjects_for(category, course, level)
        if len(subjects) == 1:
            await route_browse(query, context, f"subj:{cat_idx}:{course}:{level}:0")
            return
        # subject INDEX, not name, in callback_data -- some subject names
        # (e.g. "Advanced Auditing, Assurance & Professional Ethics") blow
        # past the 64-byte cap once a prefix is added. subjects_for() is
        # deterministic given the same loaded catalog, so the index
        # resolves back to the same subject in the "subj" branch below.
        keyboard = [
            [InlineKeyboardButton(s, callback_data=f"subj:{cat_idx}:{course}:{level}:{i}")]
            for i, s in enumerate(subjects)
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=effective_level_back(cat_idx, category, course))])
        await safe_edit_message_text(query,
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
                [InlineKeyboardButton("⬅️ Back", callback_data=effective_subject_back(cat_idx, category, course, level))]
            )
            await safe_edit_message_text(query,
                f"Subject: *{subject}*\nSelect *Paper Type*:",
                parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            # A subject with >1 live ICAI edition (first hit 2026-08-18,
            # GST) gets an Edition picker here instead of going straight to
            # Chapter -- editions_for() returns [] for every ordinary
            # single-edition subject, so this is a no-op auto-skip for
            # everything else, same convention as Course/Level/Subject.
            editions = catalog.editions_for(category, course, level, subject)
            if editions:
                keyboard = [
                    [InlineKeyboardButton(ed, callback_data=f"ed:{cat_idx}:{course}:{level}:{subj_idx}:{i}")]
                    for i, ed in enumerate(editions)
                ]
                keyboard.append(
                    [InlineKeyboardButton("⬅️ Back", callback_data=effective_subject_back(cat_idx, category, course, level))]
                )
                await safe_edit_message_text(query,
                    f"Category: *{category}* | Course: *{course}* | Level: *{level}* | Subject: *{subject}*\n"
                    f"This subject has more than one live ICAI edition — select the *attempt/session* "
                    f"you're preparing for:",
                    parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
                )
            else:
                await render_chapter_list(
                    query, context, cat_idx, category, course, level, subject, None,
                    effective_subject_back(cat_idx, category, course, level),
                    f"subj:{cat_idx}:{course}:{level}:{subj_idx}",
                )

    elif action == "ed":
        cat_idx, course, level, subj_idx, ed_idx = int(parts[1]), parts[2], parts[3], int(parts[4]), int(parts[5])
        category = CATEGORIES[cat_idx]
        subjects = catalog.subjects_for(category, course, level)
        subject = subjects[subj_idx]
        editions = catalog.editions_for(category, course, level, subject)
        edition = editions[ed_idx]
        await render_chapter_list(
            query, context, cat_idx, category, course, level, subject, edition,
            f"subj:{cat_idx}:{course}:{level}:{subj_idx}",
            f"ed:{cat_idx}:{course}:{level}:{subj_idx}:{ed_idx}",
        )

    elif action == "pt":
        cat_idx, course, level, subj_idx, paper_type = int(parts[1]), parts[2], parts[3], int(parts[4]), parts[5]
        category = CATEGORIES[cat_idx]
        subjects = catalog.subjects_for(category, course, level)
        subject = subjects[subj_idx]
        # Same reasoning as the chapters branch above -- "Download more"
        # returns to this exact file list, not one level up.
        context.user_data["return_to"] = f"pt:{cat_idx}:{course}:{level}:{subj_idx}:{paper_type}"
        files = catalog.exam_files_for(category, course, level, subject, paper_type)
        keyboard = [[InlineKeyboardButton(f["Label"][:80], callback_data=f"file:{f['row_id']}")] for f in files]
        keyboard.append(
            [InlineKeyboardButton("⬅️ Back", callback_data=f"subj:{cat_idx}:{course}:{level}:{subj_idx}")]
        )
        await safe_edit_message_text(query,
            f"Subject: *{subject}* | Paper Type: *{paper_type}*\nSelect a file:",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif action == "file":
        row_id = parts[1]
        await send_file(query, context, row_id)

    elif action == "mainmenu":
        context.user_data.clear()
        text, markup = welcome_text_and_keyboard()
        await safe_edit_message_text(query, text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)


async def send_file(query_or_update, context, row_id):
    """Send the PDF from local disk to the user, looked up by catalog row_id
    (see Catalog.get_row_by_id -- never by filename, which can exceed
    Telegram's 64-byte callback_data limit). Follows up with a "download
    more / main menu" prompt once the file is sent -- see
    prompt_download_more()."""
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

    # This IS a file/PDF delivery -- the one place in this bot that keeps
    # the brand footer, per Pranav's 2026-08-10 scoping.
    edition_bit = f" ({row.get('Session')} Attempt)" if row.get("Session") else ""
    caption = with_brand(
        f"\U0001F4C4 {row.get('Label', filename)}{edition_bit}\n"
        f"{row.get('Category','')} — {row.get('Course','')} {row.get('Level','')} — "
        f"{row.get('Subject','')}"
    )
    with open(filepath, "rb") as f:
        await context.bot.send_document(
            chat_id=chat_id, document=f, filename=filename, caption=caption, parse_mode=ParseMode.MARKDOWN
        )

    platform_db.log_interaction(DB_CONN, BOT_ID, chat_id, "file_sent")
    platform_db.execute_with_retry(
        DB_CONN,
        "INSERT INTO study_hub_events (bot_id, telegram_user_id, event_type, category, course, level, subject, file_label) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (BOT_ID, chat_id, "file_download", row.get("Category"), row.get("Course"), row.get("Level"),
         row.get("Subject"), row.get("Label", filename)),
    )

    await prompt_download_more(chat_id, context)


async def prompt_download_more(chat_id, context: ContextTypes.DEFAULT_TYPE):
    """Sent right after every file, as its own message (a document message
    can't be turned into a menu via edit). "Download more" jumps straight
    back to whichever chapter/paper-type list the file was picked from --
    see the "return_to" writes in browse_callback's "subj"/"pt" branches --
    falling back to the Category picker if the file came from free-text
    search, where there's no narrower list to return to."""
    return_to = context.user_data.get("return_to", "browse:start")
    keyboard = [
        [InlineKeyboardButton("\U0001F4E5 Download More", callback_data=return_to)],
        [InlineKeyboardButton("\U0001F3E0 Main Menu", callback_data="mainmenu:go")],
    ]
    await context.bot.send_message(
        chat_id=chat_id,
        text="Would you like to download another file, or are you done for now?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def _fuzzy_dispatch():
    """Shared by free_text_search() (detection) and
    _fuzzy_trigger_callback() (resolution) -- must be the SAME mapping
    both times, see fuzzy_trigger.py's own docstring."""
    return {
        "profile": lambda u, c: profile_flow.start_profile_flow(u, c, BOT_ID),
        "report": lambda u, c: report_flow.start_report_flow_on_demand(u, c, BOT_ID),
    }


async def _search_original_text(update, context, original_text):
    update.message.text = original_text
    await free_text_search(update, context)


async def _fuzzy_trigger_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await fuzzy_trigger.handle_confirm_callback(update, context, _fuzzy_dispatch(), on_decline=_search_original_text)


async def free_text_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles direct text like 'CA Inter cash flow' or 'CS company law',
    searched across every course and category at once -- except a
    standalone greeting/"reset" (see RESET_TRIGGER_RE), which resets the
    conversation via start() instead of being treated as a search query."""
    query_text = input_guard.sanitize_free_text(update.message.text)

    # 2026-08-16 (independent code review): a universal cancel phrase,
    # checked before anything else -- see cancel_utils.py's own docstring.
    if cancel_utils.matches_cancel(query_text):
        if cancel_utils.cancel_all_flows(context):
            await update.message.reply_text("❌ Cancelled — you can start fresh anytime.")
            return
        # nothing was active -- fall through to normal handling below.

    # Profile flow takes priority over both search and the reset-greeting
    # check below -- a display-name/username reply mid-edit must never be
    # swallowed by either (see profile_flow.py's own docstring for the full
    # trigger/state design; same "check awaiting-state first" discipline
    # exam_hub_bot.py's text_router already applies).
    if profile_flow.is_awaiting_text_input(context):
        if await profile_flow.handle_profile_text_input(update, context):
            return
    if profile_flow.matches_trigger(query_text):
        await profile_flow.start_profile_flow(update, context, BOT_ID)
        return
    if report_flow.matches_trigger(query_text) and not report_flow.is_awaiting_text_input(context):
        await report_flow.start_report_flow_on_demand(update, context, BOT_ID)
        return
    if report_flow.is_awaiting_text_input(context):
        if await report_flow.handle_contact_text_input(update, context):
            return

    if RESET_TRIGGER_RE.match(query_text):
        await start(update, context)
        return

    # 2026-08-16: nothing matched exactly -- check for a plausible TYPO of
    # "profile"/"report" (the only two triggers Study Hub itself has) before
    # silently running it as a search (see fuzzy_trigger.py's own
    # docstring -- this is what stops "dne" from returning unrelated PDF
    # results instead of a "did you mean X?" confirmation).
    if await fuzzy_trigger.maybe_confirm(update, context, _fuzzy_dispatch()):
        return

    # SECURITY.md §3.A.2 -- a narrower, dedicated limit on real catalog
    # searches specifically (checked here, not via the registration-time
    # decorator, so it never throttles the flow-trigger/awaiting-input
    # branches above -- those are legitimate continuations, not searches).
    if not await rate_limiter.check_and_notify(update, context, BOT_ID, "search"):
        return

    results = catalog.search_text(query_text)

    platform_db.log_interaction(DB_CONN, BOT_ID, update.effective_user.id, "search")
    platform_db.execute_with_retry(
        DB_CONN,
        "INSERT INTO study_hub_events (bot_id, telegram_user_id, event_type, query_text) VALUES (?,?,?,?)",
        (BOT_ID, update.effective_user.id, "search_query" if results else "search_no_match", query_text),
    )

    if not results:
        await update.message.reply_text(
            "I couldn't find a close match. Try /start to browse by menu instead, "
            "or rephrase (e.g. include the course, chapter number, or subject name)."
        )
        return

    # No chapter/paper-type list exists to return to for a search-triggered
    # download -- explicitly reset (not just default-if-absent) so a STALE
    # return_to left over from earlier Browse navigation this session never
    # leaks into an unrelated search's "Download more" button.
    context.user_data["return_to"] = "browse:start"

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
        # -- without them, two buttons could be indistinguishable. Session
        # is included too (2026-08-18) for the same reason one level deeper
        # -- a subject with >1 live edition (e.g. GST) has literally
        # identical chapter titles across editions.
        session_bit = f" ({row.get('Session')})" if row.get("Session") else ""
        label = f"{row.get('Label', row['FileName'])}{session_bit} — {row.get('Category','')} · {row.get('Course','')} {row.get('Level','')} {row.get('Subject','')}"
        # row_id, never FileName, in callback_data -- see the 64-byte note in browse_callback.
        keyboard.append([InlineKeyboardButton(label[:80], callback_data=f"file:{row_id}")])
    await update.message.reply_text(
        "I found a few possible matches — please pick one:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def main():
    if not BOT_TOKEN:
        env_name = BOT_CONFIG.get("bot_token_env")
        hint = f"set the {env_name} variable in telegram/.env" if env_name else "check bots.json"
        raise SystemExit(
            f"No bot token found for bot_id '{BOT_ID}'. {hint} "
            f"(see telegram/config/bots.README.md)."
            + (f" '1lavya-studyhub' can also fall back to a "
               f"'Name: {BOT_NAME_IN_CREDS}' / 'Bot Token: ...' block in {CREDS_PATH}."
               if BOT_ID == "1lavya-studyhub" else "")
        )

    app = Application.builder().token(BOT_TOKEN).build()
    platform_db.schedule_heartbeat(app, BOT_ID)

    # 2026-08-17: every handler below wrapped with activity_logger.log_activity()
    # at registration time only -- see telegram/LOGGING-ARCHITECTURE.md §3.
    # 2026-08-24: rate_limiter.rate_limited() wraps OUTERMOST (see that
    # module's own docstring for why) -- a "general" flood cap on every
    # handler, SECURITY.md §4.1. Narrower per-action buckets (e.g. "search")
    # are applied INLINE at the specific expensive chokepoint instead --
    # see free_text_search()'s own body.
    def _rl(kind, func):
        return rate_limiter.rate_limited("general", BOT_ID)(activity_logger.log_activity(kind, BOT_ID)(func))

    app.add_handler(CommandHandler("start", _rl("command", start)))
    app.add_handler(CommandHandler("reset", _rl("command", start)))
    app.add_handler(CallbackQueryHandler(_rl("callback", browse_callback), pattern=r"^(browse|cat|crs|lvl|subj|ed|pt|file|mainmenu):"))
    app.add_handler(CallbackQueryHandler(_rl("callback", profile_flow.profile_flow_callback), pattern=r"^(profile|profileconfirm):"))
    app.add_handler(CallbackQueryHandler(_rl("callback", report_flow.report_flow_callback), pattern=r"^(report|reportconfirm):"))
    app.add_handler(CallbackQueryHandler(_rl("callback", _fuzzy_trigger_callback), pattern=r"^fuzzytrigger:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _rl("text", free_text_search)))

    # Re-arm any access_requests still pending from before this restart
    # (job_queue jobs do not survive a restart) -- see profile_flow.py's
    # own docstring.
    profile_flow.rearm_pending_access_requests(app, BOT_ID)

    logger.info(f"Study Hub Bot starting for bot_id '{BOT_ID}' (tenant '{TENANT_ID}', {TENANT['display_name']})...")
    app.run_polling()


if __name__ == "__main__":
    main()
