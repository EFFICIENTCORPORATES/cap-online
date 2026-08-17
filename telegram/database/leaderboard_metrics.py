"""
telegram/database/leaderboard_metrics.py -- leaderboard config loading,
metrics registry, and ranking computation (2026-08-11, Phase 3 of the
branding-kit -> report-pipeline -> leaderboard -> admin-portal roadmap)
--------------------------------------------------------------------------------
Shared by telegram/bots/profile_flow.py (which leaderboards can a student
see/join -- eligibility matching only, no ranking) and
telegram/bots/leaderboard_broadcaster.py (the nightly job -- full ranking
computation). Same "one shared query layer" principle as analytics.py.

IDENTITY: every metric is computed per `username` (student_profiles),
aggregating activity across EVERY telegram_user_id (phone) linked to that
username -- consistent with the profile system's "one identity, several
phones" design (see telegram/PROFILE-SYSTEM.md). A student with no
username cannot be ranked (they also can't join a leaderboard -- see
profile_flow.py).

METRICS REGISTRY: adding a new metric is one new entry in METRICS below +
one compute_*() function -- referencing its key from any leaderboard's
`metrics` list in leaderboards.json needs no other code change.

MULTI-METRIC DISPLAY: each leaderboard's `metrics` list produces its OWN
separate mini-ranking (Pranav's choice, 2026-08-11 -- not a blended
weighted score). compute_rankings() returns one sorted list per metric.

MINIMUM-ATTEMPTS FLOOR: a blanket gate across ALL metrics for a given
leaderboard (Pranav's choice) -- a student needs >= min_attempts_floor
ANSWERED MCQs within that leaderboard's eligibility scope (course+level)
before they appear on ANY of its metric rankings, not just accuracy.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

LEADERBOARDS_PATH = Path(__file__).resolve().parents[1] / "config" / "leaderboards.json"


def load_leaderboards_config(path: Path = LEADERBOARDS_PATH) -> dict:
    """Reloaded fresh on every call (not cached at import time) -- same "no
    code change, no restart needed to pick up a config edit" ethos as
    tenants.json/bots.json/alerts.json. Returns {} shaped safely if the
    file is missing, so a fresh clone without this file yet doesn't crash
    a bot's profile menu -- just shows no leaderboards."""
    if not path.exists():
        return {"schema_version": 1, "defaults": {}, "leaderboards": []}
    return json.loads(path.read_text(encoding="utf-8"))


def active_leaderboards(config: dict = None) -> list:
    config = config or load_leaderboards_config()
    return [lb for lb in config.get("leaderboards", []) if lb.get("status") == "active"]


def eligible_leaderboards_for(course: str, level: str, config: dict = None) -> list:
    """Every ACTIVE leaderboard whose eligibility matches this student's
    profile course/level exactly -- what profile_flow.py's join menu
    shows. A student with no course/level set yet sees none (correct --
    they haven't told us what to match against)."""
    if not course or not level:
        return []
    return [
        lb for lb in active_leaderboards(config)
        if lb.get("eligibility", {}).get("course") == course
        and lb.get("eligibility", {}).get("level") == level
    ]


def get_leaderboard(leaderboard_id: str, config: dict = None) -> dict | None:
    config = config or load_leaderboards_config()
    for lb in config.get("leaderboards", []):
        if lb.get("leaderboard_id") == leaderboard_id:
            return lb
    return None


def _resolve(leaderboard: dict, key: str, config: dict):
    """A leaderboard entry's own value if present, else config['defaults'][key]."""
    if key in leaderboard:
        return leaderboard[key]
    return (config or load_leaderboards_config()).get("defaults", {}).get(key)


# ---------------------------------------------------------------------------
# Metric computation -- each takes (conn, chat_ids, course, level) and
# returns a number (or None if there's no data at all for that student in
# scope, e.g. accuracy with zero answered questions).
# ---------------------------------------------------------------------------

def _seconds_between(a: str, b: str) -> float:
    def parse(ts):
        return datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts.endswith("Z") else datetime.fromisoformat(ts)
    dt_a, dt_b = parse(a), parse(b)
    if dt_a.tzinfo is None:
        dt_a = dt_a.replace(tzinfo=timezone.utc)
    if dt_b.tzinfo is None:
        dt_b = dt_b.replace(tzinfo=timezone.utc)
    return (dt_b - dt_a).total_seconds()


def _linked_chat_ids(conn, username: str) -> list:
    rows = conn.execute("SELECT telegram_user_id FROM students WHERE lavya_username=?", (username,)).fetchall()
    return [r[0] for r in rows]


def compute_questions_attempted(conn, chat_ids: list, course: str, level: str) -> int:
    """Count of ANSWERED (not just shown) MCQs in this course+level scope,
    summed across every chat_id linked to this username."""
    if not chat_ids:
        return 0
    placeholders = ",".join("?" * len(chat_ids))
    row = conn.execute(
        f"SELECT COUNT(*) FROM exam_hub_mcq_attempts WHERE telegram_user_id IN ({placeholders}) "
        f"AND answered_at IS NOT NULL AND course=? AND level=?",
        (*chat_ids, course, level),
    ).fetchone()
    return row[0] or 0


def compute_accuracy_pct(conn, chat_ids: list, course: str, level: str):
    if not chat_ids:
        return None
    placeholders = ",".join("?" * len(chat_ids))
    row = conn.execute(
        f"SELECT COUNT(*), SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) FROM exam_hub_mcq_attempts "
        f"WHERE telegram_user_id IN ({placeholders}) AND answered_at IS NOT NULL AND course=? AND level=?",
        (*chat_ids, course, level),
    ).fetchone()
    answered, correct = row[0], row[1] or 0
    if not answered:
        return None
    return round(100 * correct / answered, 1)


def compute_time_spent_minutes(conn, chat_ids: list, course: str, level: str) -> float:
    """Same idle-gap-safe technique student_analytics.py's "time on bot"
    uses (session span = MAX(real activity timestamp) - started_at, never
    wider than what's actually recorded) -- reimplemented here rather than
    imported because the SCOPE differs (multiple chat_ids aggregated
    together, filtered to one course+level) from that module's single-
    chat_id, platform-wide definition. Same principle, different query
    shape."""
    if not chat_ids:
        return 0.0
    placeholders = ",".join("?" * len(chat_ids))
    sessions = conn.execute(
        f"SELECT session_id, started_at FROM exam_hub_sessions "
        f"WHERE telegram_user_id IN ({placeholders}) AND course=? AND level=?",
        (*chat_ids, course, level),
    ).fetchall()
    if not sessions:
        return 0.0
    session_ids = [s[0] for s in sessions]
    sp = ",".join("?" * len(session_ids))
    last_activity = {}
    for session_id, ts in conn.execute(
        f"""
        SELECT session_id, MAX(ts) FROM (
            SELECT session_id, shown_at AS ts FROM exam_hub_mcq_attempts WHERE session_id IN ({sp})
            UNION ALL
            SELECT session_id, answered_at AS ts FROM exam_hub_mcq_attempts WHERE session_id IN ({sp}) AND answered_at IS NOT NULL
            UNION ALL
            SELECT session_id, shown_at AS ts FROM exam_hub_descriptive_events WHERE session_id IN ({sp})
            UNION ALL
            SELECT session_id, answer_shown_at AS ts FROM exam_hub_descriptive_events WHERE session_id IN ({sp}) AND answer_shown_at IS NOT NULL
        ) GROUP BY session_id
        """,
        (*session_ids, *session_ids, *session_ids, *session_ids),
    ).fetchall():
        last_activity[session_id] = ts

    total_seconds = 0.0
    for session_id, started_at in sessions:
        la = last_activity.get(session_id)
        if la:
            span = _seconds_between(started_at, la)
            if span > 0:
                total_seconds += span
    return round(total_seconds / 60, 1)


METRICS = {
    "accuracy_pct": {"label": "Accuracy", "suffix": "%", "compute": compute_accuracy_pct},
    "questions_attempted": {"label": "Questions Attempted", "suffix": "", "compute": compute_questions_attempted},
    "time_spent_minutes": {"label": "Time Spent", "suffix": " min", "compute": compute_time_spent_minutes},
}


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------

def qualifying_participants(conn, leaderboard_id: str, eligibility: dict, min_attempts_floor: int) -> list:
    """Usernames who (a) opted into this leaderboard_id, (b) still match
    its eligibility per their CURRENT profile (re-checked at ranking time,
    never trusting a stale opt-in -- a student who joined then later
    REMOVED the matching course/level from their profile should not keep
    appearing on a leaderboard that no longer matches them), and (c) meet
    the min-attempts floor (gated on questions_attempted, the same metric
    regardless of which metrics this leaderboard actually ranks by).

    2026-08-16: joins against student_academic_profiles, not
    student_profiles.course/level directly -- those two columns are now a
    frozen historical trace (see schema.sql's own comment on
    student_academic_profiles), never written to by a profile created or
    edited after the multi-course rollout, so a query still reading them
    here would silently stop finding ANY newly-added profile's leaderboard
    eligibility. A student matches if ANY of their (possibly several)
    academic profiles has this exact course+level -- correct even for a
    student simultaneously preparing for other courses too."""
    rows = conn.execute(
        "SELECT DISTINCT lp.username FROM leaderboard_participants lp "
        "JOIN student_academic_profiles sap ON sap.username = lp.username "
        "WHERE lp.leaderboard_id=? AND sap.course=? AND sap.level=?",
        (leaderboard_id, eligibility["course"], eligibility["level"]),
    ).fetchall()
    qualifying = []
    for (username,) in rows:
        chat_ids = _linked_chat_ids(conn, username)
        attempted = compute_questions_attempted(conn, chat_ids, eligibility["course"], eligibility["level"])
        if attempted >= min_attempts_floor:
            qualifying.append(username)
    return qualifying


def compute_rankings(conn, leaderboard: dict, config: dict = None) -> dict:
    """{metric_key: [(username, display_name, value), ...]} sorted
    descending, trimmed to top_n, for every metric in this leaderboard's
    `metrics` list -- what leaderboard_broadcaster.py renders into the
    nightly message. Unknown metric keys are silently skipped (a typo in
    leaderboards.json shouldn't crash the whole broadcast -- caller should
    still check for a metric it expected but didn't get back)."""
    eligibility = leaderboard["eligibility"]
    leaderboard_id = leaderboard["leaderboard_id"]
    min_attempts_floor = _resolve(leaderboard, "min_attempts_floor", config)
    top_n = _resolve(leaderboard, "top_n", config)

    qualifying = qualifying_participants(conn, leaderboard_id, eligibility, min_attempts_floor)

    display_names = {}
    chat_ids_cache = {}
    for username in qualifying:
        row = conn.execute("SELECT display_name FROM student_profiles WHERE username=?", (username,)).fetchone()
        display_names[username] = (row[0] if row and row[0] else username)
        chat_ids_cache[username] = _linked_chat_ids(conn, username)

    out = {}
    for metric_key in leaderboard.get("metrics", []):
        meta = METRICS.get(metric_key)
        if not meta:
            continue
        values = []
        for username in qualifying:
            value = meta["compute"](conn, chat_ids_cache[username], eligibility["course"], eligibility["level"])
            if value is None:
                continue
            values.append((username, display_names[username], value))
        values.sort(key=lambda t: t[2], reverse=True)
        out[metric_key] = values[: top_n or 10]
    return out
