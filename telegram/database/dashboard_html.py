"""
telegram/database/dashboard_html.py -- the ONE dashboard page template
(2026-08-10, split out of generate_dashboard.py the same day
dashboard_server.py was added)
-----------------------------------------------------------------------------
Renders the exact same HTML/CSS/JS for both reporting surfaces:
  - telegram/tools/generate_dashboard.py  -- static snapshot, DATA baked in,
    no Refresh button (nothing to fetch -- it's a plain file on disk).
  - telegram/tools/dashboard_server.py    -- live version, same page PLUS a
    Refresh button that fetches /api/data and re-renders in place.
One template, one set of query results shown, one place to fix a rendering
bug -- see CLAUDE.md section 7's "single source of truth" print/pagination
rule; same principle, applied to this dashboard instead.

render_page(data, live) is the only thing callers need. `data` is whatever
telegram/database/analytics.py's fetch_all() returned (or the equivalent
JSON an API call gets back) -- {generated_at, bots, heartbeats, daily,
summary}.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "branding"))
import brand_kit  # noqa: E402 -- must follow the sys.path.insert() above

# Categorical palette, validated (dataviz skill's reference instance) --
# fixed hue order, never cycled; slot 8+ folds into "Other" (see below).
CATEGORICAL = [
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100",
    "#e87ba4", "#008300", "#4a3aa7", "#e34948",
]
STATUS_GOOD = "#0ca30c"
STATUS_CRITICAL = "#d03b3b"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
SURFACE = "#fcfcfb"
PAGE_PLANE = "#f9f9f7"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
BORDER = "rgba(11,11,11,0.10)"


def render_page(data: dict, live: bool) -> str:
    data_json = json.dumps(data, ensure_ascii=False)
    refresh_button_html = (
        '<button id="refresh-btn" class="refresh-btn">↻ Refresh</button>'
        '<span id="refresh-status" class="refresh-status"></span>'
        if live else ""
    )
    refresh_js = _REFRESH_JS if live else ""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>1LAVYA Bot Analytics{' (live)' if live else ''}</title>
<style>
  :root {{
    --surface: {SURFACE}; --plane: {PAGE_PLANE}; --ink: {INK_PRIMARY}; --ink-2: {INK_SECONDARY};
    --muted: {INK_MUTED}; --grid: {GRIDLINE}; --baseline: {BASELINE}; --border: {BORDER};
    --good: {STATUS_GOOD}; --critical: {STATUS_CRITICAL};
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--plane); color: var(--ink);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    padding: 24px;
  }}
  h1 {{ font-size: 20px; margin: 0 0 4px; display: inline-block; }}
  .header-row {{ display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }}
  .subtitle {{ color: var(--muted); font-size: 13px; margin-bottom: 24px; }}
  .refresh-btn {{
    background: #2a78d6; color: white; border: none; border-radius: 6px;
    padding: 6px 14px; font-size: 13px; cursor: pointer;
  }}
  .refresh-btn:disabled {{ opacity: .6; cursor: default; }}
  .refresh-status {{ color: var(--muted); font-size: 12px; }}
  .stat-row {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }}
  .stat-tile {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px 20px; min-width: 160px; flex: 1;
  }}
  .stat-tile .label {{ color: var(--ink-2); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
  .stat-tile .value {{ font-size: 28px; font-weight: 600; margin-top: 4px; font-variant-numeric: tabular-nums; }}
  .card {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
    padding: 20px; margin-bottom: 24px;
  }}
  .card h2 {{ font-size: 15px; margin: 0 0 12px; }}
  .table-scroll {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; color: var(--ink-2); font-weight: 500; padding: 6px 8px; border-bottom: 1px solid var(--grid); white-space: nowrap; }}
  td {{ padding: 6px 8px; border-bottom: 1px solid var(--grid); white-space: nowrap; }}
  .dot {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }}
  .range-buttons {{ display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }}
  .range-buttons button {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 6px;
    padding: 6px 12px; font-size: 13px; cursor: pointer; color: var(--ink);
  }}
  .range-buttons button.active {{ background: #2a78d6; color: white; border-color: #2a78d6; }}
  .custom-range {{ display: flex; gap: 8px; align-items: center; font-size: 13px; }}
  .custom-range input {{ padding: 4px 6px; border: 1px solid var(--border); border-radius: 4px; }}
  svg text {{ font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
  .axis-label {{ fill: var(--muted); font-size: 11px; }}
  .legend {{ display: flex; gap: 16px; flex-wrap: wrap; margin-top: 12px; font-size: 12px; color: var(--ink-2); }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; }}
  .legend-swatch {{ width: 10px; height: 10px; border-radius: 2px; }}
  .bar-tooltip {{
    position: absolute; background: var(--ink); color: white; font-size: 12px;
    padding: 6px 10px; border-radius: 6px; pointer-events: none; opacity: 0; transition: opacity .1s;
    white-space: nowrap; z-index: 10;
  }}
</style>
</head>
<body>
  {brand_kit.render_header_html("Bot Analytics" + (" (live)" if live else ""))}
  <div class="header-row" style="margin-top:4px;">
    {refresh_button_html}
  </div>
  <div class="subtitle" id="generated-at"></div>

  <div class="stat-row" id="stat-row"></div>

  <div class="card">
    <h2>Bot Status</h2>
    <div class="table-scroll">
    <table id="bot-status-table">
      <thead><tr><th></th><th>Bot ID</th><th>Kind</th><th>Tenant</th><th>Config Status</th><th>Last Heartbeat</th></tr></thead>
      <tbody></tbody>
    </table>
    </div>
  </div>

  <div class="card">
    <h2>Student Master <span id="student-master-count" style="color:var(--muted); font-weight:normal; font-size:12px;"></span></h2>
    <p style="color:var(--muted); font-size:12px; margin:0 0 12px;">
      Every known student: contact info, and which faculty/course(s) they've actually studied
      (derived from real activity, not a bot's full possible scope) -- "Self Study" means they've
      only used a platform bot, no dedicated faculty. Sorted by most recently active.
    </p>
    <input id="student-master-filter" type="text" placeholder="Filter by name, chat ID, email, mobile, or faculty..."
           style="width:100%; padding:6px 10px; border:1px solid var(--border); border-radius:6px; font-size:13px; margin-bottom:12px; box-sizing:border-box;">
    <div class="table-scroll">
    <table id="student-master-table">
      <thead><tr>
        <th>Chat ID</th><th>Name</th><th>Mobile</th><th>Email</th><th>Faculty</th><th>Courses</th><th>Last Seen</th>
      </tr></thead>
      <tbody></tbody>
    </table>
    </div>
  </div>

  <div class="card">
    <h2>Student Breakdown</h2>
    <p style="color:var(--muted); font-size:12px; margin:0 0 12px;">
      Chat-ID-wise MCQ activity for <b>one bot at a time</b> -- attempted, answered, correct, wrong.
      A student using more than one bot appears in each bot's own list separately, so summing the
      counts shown here across bots will overcount real people -- see "Unique MCQ-Attempters" above
      for the true deduped total, or "Student Master" below for one row per real student.
    </p>
    <select id="student-breakdown-bot-select" style="padding:6px 10px; border:1px solid var(--border); border-radius:6px; font-size:13px; margin-bottom:12px;"></select>
    <div class="table-scroll">
    <table id="student-breakdown-table">
      <thead><tr>
        <th>Chat ID</th><th>Name</th><th>Attempted</th><th>Answered</th><th>Correct</th><th>Wrong</th><th>Accuracy</th>
      </tr></thead>
      <tbody></tbody>
    </table>
    </div>
  </div>

  <div class="card">
    <h2>Faculty Report — Student-wise &amp; Chapter-wise</h2>
    <p style="color:var(--muted); font-size:12px; margin:0 0 12px;">
      For <b>one bot at a time</b>: every student's total MCQs attempted and accuracy, sorted by
      engagement (most-attempted first) -- click a row to see that student's chapter-wise
      breakdown. Same per-chat-id granularity as Student Breakdown above (a student on two phones
      shows as two rows).
    </p>
    <select id="faculty-report-bot-select" style="padding:6px 10px; border:1px solid var(--border); border-radius:6px; font-size:13px; margin-bottom:12px;"></select>
    <div class="table-scroll">
    <table id="faculty-report-table">
      <thead><tr>
        <th></th><th>Chat ID</th><th>Name</th><th>Total Attempted</th><th>Correct</th><th>Accuracy</th><th>Chapters Covered</th>
      </tr></thead>
      <tbody></tbody>
    </table>
    </div>
  </div>

  <div class="card">
    <h2>Content Health <span id="content-health-badge"></span></h2>
    <p style="color:var(--muted); font-size:12px; margin:0 0 12px;">
      Checks every tenant's MCQ/descriptive JSON against the fields the bot code
      actually reads (telegram/tools/validate_content_json.py) -- catches a
      faculty's malformed file here, before a student hits it. Extra
      faculty-specific fields never trigger a flag, only missing/malformed
      core ones do.
    </p>
    <div id="content-health-list"></div>
  </div>

  <div class="card">
    <h2>Bot-wise Usage Summary (all-time)</h2>
    <div class="table-scroll">
    <table id="bot-summary-table">
      <thead><tr>
        <th>Bot ID</th><th>Interactions</th><th>Unique Users</th>
        <th>Downloads</th><th>Searches</th>
        <th>Exam Sessions</th><th>MCQ Shown</th><th>MCQ Answered</th><th>MCQ Accuracy</th><th>Descriptive Shown</th>
        <th>Last Seen</th>
      </tr></thead>
      <tbody></tbody>
    </table>
    </div>
  </div>

  <div class="card">
    <h2>Message Volume &amp; Unique Visitors</h2>
    <div class="range-buttons" id="range-buttons"></div>
    <div class="custom-range">
      From <input type="date" id="custom-from"> To <input type="date" id="custom-to">
      <button id="custom-apply">Apply</button>
    </div>
    <div style="position:relative; margin-top:16px;">
      <svg id="chart" width="100%" height="320" viewBox="0 0 900 320" preserveAspectRatio="xMinYMin meet"></svg>
      <div class="bar-tooltip" id="tooltip"></div>
    </div>
    <div class="legend" id="legend"></div>
  </div>

<script>
let DATA = {data_json};
const CATEGORICAL = {json.dumps(CATEGORICAL)};

// ---------------------------------------------------------------------
// Top-level render: (re)draws every section from the current DATA. Called
// once on load, and again after a Refresh in live mode -- nothing here
// assumes DATA is only ever set once.
// ---------------------------------------------------------------------
function applyData(newData) {{
  DATA = newData;
  document.getElementById('generated-at').textContent =
    'Snapshot generated ' + new Date(DATA.generated_at).toLocaleString();
  renderBotStatusTable();
  renderStudentMaster();
  renderStudentBreakdown();
  renderFacultyReport();
  renderContentHealth();
  renderBotSummaryTable();
  rebuildRangePresets();
  render();
}}

function renderStudentMaster() {{
  document.getElementById('student-master-count').textContent = `(${{(DATA.student_master || []).length}})`;
  const filterInput = document.getElementById('student-master-filter');
  filterInput.oninput = renderStudentMasterTable;
  renderStudentMasterTable();
}}

function renderStudentMasterTable() {{
  const rows = DATA.student_master || [];
  const filterText = (document.getElementById('student-master-filter').value || '').toLowerCase().trim();
  const tbody = document.querySelector('#student-master-table tbody');
  tbody.innerHTML = '';

  const filtered = rows.filter(r => {{
    if (!filterText) return true;
    const haystack = [
      r.telegram_user_id, r.display_name, r.username, r.email, r.mobile_number,
      ...(r.faculty || []), ...(r.courses || []),
    ].filter(Boolean).join(' ').toLowerCase();
    return haystack.includes(filterText);
  }});

  if (filtered.length === 0) {{
    tbody.innerHTML = '<tr><td colspan="7" style="color:var(--muted)">No students match.</td></tr>';
    return;
  }}
  for (const r of filtered) {{
    const tr = document.createElement('tr');
    const lastSeen = r.last_seen_at ? new Date(r.last_seen_at).toLocaleString() : '—';
    tr.innerHTML = `<td>${{r.telegram_user_id}}</td>
      <td>${{r.display_name}}${{r.username ? ` (@${{r.username}})` : ''}}</td>
      <td>${{r.mobile_number || '—'}}</td>
      <td>${{r.email || '—'}}</td>
      <td>${{(r.faculty || []).join(', ') || '—'}}</td>
      <td>${{(r.courses || []).join(', ') || '—'}}</td>
      <td>${{lastSeen}}</td>`;
    tbody.appendChild(tr);
  }}
}}

let _studentBreakdownSelectedBot = null;

function renderStudentBreakdown() {{
  const breakdown = DATA.student_breakdown || {{}};
  const botIds = Object.keys(breakdown);
  const select = document.getElementById('student-breakdown-bot-select');

  if (!_studentBreakdownSelectedBot || !botIds.includes(_studentBreakdownSelectedBot)) {{
    _studentBreakdownSelectedBot = botIds[0] || null;
  }}

  select.innerHTML = '';
  botIds.forEach(botId => {{
    const opt = document.createElement('option');
    opt.value = botId;
    const meta = DATA.bots[botId];
    opt.textContent = (meta ? meta.display_name : botId) + ` (${{breakdown[botId].length}} students)`;
    if (botId === _studentBreakdownSelectedBot) opt.selected = true;
    select.appendChild(opt);
  }});
  select.onchange = () => {{
    _studentBreakdownSelectedBot = select.value;
    renderStudentBreakdownTable();
  }};

  renderStudentBreakdownTable();
}}

function renderStudentBreakdownTable() {{
  const breakdown = DATA.student_breakdown || {{}};
  const rows = breakdown[_studentBreakdownSelectedBot] || [];
  const tbody = document.querySelector('#student-breakdown-table tbody');
  tbody.innerHTML = '';
  if (rows.length === 0) {{
    tbody.innerHTML = '<tr><td colspan="7" style="color:var(--muted)">No MCQ activity recorded for this bot yet.</td></tr>';
    return;
  }}
  for (const r of rows) {{
    const tr = document.createElement('tr');
    const acc = r.accuracy_pct === null ? '—' : r.accuracy_pct + '%';
    tr.innerHTML = `<td>${{r.telegram_user_id}}</td><td>${{r.display_name}}</td><td>${{r.attempted}}</td>
      <td>${{r.answered}}</td><td>${{r.correct}}</td><td>${{r.wrong}}</td><td>${{acc}}</td>`;
    tbody.appendChild(tr);
  }}
}}

let _facultyReportSelectedBot = null;
let _facultyReportExpandedRow = null;   // telegram_user_id of the currently expanded row, or null

function renderFacultyReport() {{
  const report = DATA.faculty_report || {{}};
  const botIds = Object.keys(report);
  const select = document.getElementById('faculty-report-bot-select');

  if (!_facultyReportSelectedBot || !botIds.includes(_facultyReportSelectedBot)) {{
    _facultyReportSelectedBot = botIds[0] || null;
  }}

  select.innerHTML = '';
  botIds.forEach(botId => {{
    const opt = document.createElement('option');
    opt.value = botId;
    const meta = DATA.bots[botId];
    opt.textContent = (meta ? meta.display_name : botId) + ` (${{report[botId].length}} students)`;
    if (botId === _facultyReportSelectedBot) opt.selected = true;
    select.appendChild(opt);
  }});
  select.onchange = () => {{
    _facultyReportSelectedBot = select.value;
    _facultyReportExpandedRow = null;
    renderFacultyReportTable();
  }};

  renderFacultyReportTable();
}}

function renderFacultyReportTable() {{
  const report = DATA.faculty_report || {{}};
  const rows = report[_facultyReportSelectedBot] || [];
  const tbody = document.querySelector('#faculty-report-table tbody');
  tbody.innerHTML = '';
  if (rows.length === 0) {{
    tbody.innerHTML = '<tr><td colspan="7" style="color:var(--muted)">No MCQ activity recorded for this bot yet.</td></tr>';
    return;
  }}
  for (const r of rows) {{
    const acc = r.accuracy_pct === null ? '—' : r.accuracy_pct + '%';
    const expanded = _facultyReportExpandedRow === r.telegram_user_id;
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.innerHTML = `<td>${{expanded ? '▼' : '▶'}}</td><td>${{r.telegram_user_id}}</td><td>${{r.display_name}}</td>
      <td>${{r.total_attempted}}</td><td>${{r.total_correct}}</td><td>${{acc}}</td><td>${{r.chapters.length}}</td>`;
    tr.onclick = () => {{
      _facultyReportExpandedRow = expanded ? null : r.telegram_user_id;
      renderFacultyReportTable();
    }};
    tbody.appendChild(tr);

    if (expanded) {{
      const detailTr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 7;
      td.style.cssText = 'background:var(--plane); padding:10px;';
      let inner = `<table style="width:100%; font-size:12px;"><thead><tr>
        <th style="text-align:left; color:var(--ink-2); padding:4px;">Chapter</th>
        <th style="text-align:left; color:var(--ink-2); padding:4px;">MCQ Attempted</th>
        <th style="text-align:left; color:var(--ink-2); padding:4px;">Correct</th>
        <th style="text-align:left; color:var(--ink-2); padding:4px;">Accuracy</th>
        <th style="text-align:left; color:var(--ink-2); padding:4px;">Descriptive Viewed</th>
        </tr></thead><tbody>`;
      for (const c of r.chapters) {{
        const cAcc = c.accuracy_pct === null ? '—' : c.accuracy_pct + '%';
        inner += `<tr><td style="padding:4px;">${{c.chapter_label}}</td><td style="padding:4px;">${{c.mcq_attempted}}</td>
          <td style="padding:4px;">${{c.mcq_correct}}</td><td style="padding:4px;">${{cAcc}}</td>
          <td style="padding:4px;">${{c.descriptive_shown}}</td></tr>`;
      }}
      inner += '</tbody></table>';
      td.innerHTML = inner;
      detailTr.appendChild(td);
      tbody.appendChild(detailTr);
    }}
  }}
}}

function renderContentHealth() {{
  const reports = DATA.content_health || [];
  const totalErrors = reports.reduce((n, r) => n + r.issues.filter(i => i.severity === 'ERROR').length, 0);
  const totalWarnings = reports.reduce((n, r) => n + r.issues.filter(i => i.severity === 'WARNING').length, 0);

  const badge = document.getElementById('content-health-badge');
  if (totalErrors > 0) {{
    badge.innerHTML = `<span style="color:var(--critical); font-size:12px;">● ${{totalErrors}} error(s)</span>`;
  }} else if (totalWarnings > 0) {{
    badge.innerHTML = `<span style="color:#b8860b; font-size:12px;">● ${{totalWarnings}} warning(s)</span>`;
  }} else {{
    badge.innerHTML = `<span style="color:var(--good); font-size:12px;">● all clear</span>`;
  }}

  const container = document.getElementById('content-health-list');
  container.innerHTML = '';
  if (reports.length === 0) {{
    container.innerHTML = '<div style="color:var(--muted)">No content files discoverable from tenants.json.</div>';
    return;
  }}
  for (const r of reports) {{
    const errors = r.issues.filter(i => i.severity === 'ERROR');
    const warnings = r.issues.filter(i => i.severity === 'WARNING');
    const shortPath = r.path.split(/[\\/]/).slice(-3).join('/');
    const dotColor = errors.length ? 'var(--critical)' : (warnings.length ? '#b8860b' : 'var(--good)');
    const block = document.createElement('div');
    block.style.cssText = 'padding:10px 0; border-bottom:1px solid var(--grid);';
    let html = `<div><span class="dot" style="background:${{dotColor}}"></span>
      <strong>${{shortPath}}</strong>
      <span style="color:var(--muted)">(${{r.kind}}, ${{r.record_count}} records, tenants: ${{(r.tenant_ids||[]).join(', ') || '—'}})</span></div>`;
    if (errors.length === 0 && warnings.length === 0) {{
      html += `<div style="color:var(--muted); font-size:12px; margin-top:4px;">No issues.</div>`;
    }} else {{
      html += '<ul style="margin:6px 0 0; padding-left:20px; font-size:12px;">';
      for (const i of [...errors, ...warnings]) {{
        const color = i.severity === 'ERROR' ? 'var(--critical)' : '#b8860b';
        html += `<li><span style="color:${{color}}; font-weight:600;">[${{i.severity}}]</span> ${{i.record_id}} :: ${{i.field || ''}} — ${{i.message}}</li>`;
      }}
      html += '</ul>';
    }}
    block.innerHTML = html;
    container.appendChild(block);
  }}
}}

function renderBotStatusTable() {{
  const tbody = document.querySelector('#bot-status-table tbody');
  tbody.innerHTML = '';
  for (const [botId, meta] of Object.entries(DATA.bots)) {{
    const hb = DATA.heartbeats[botId];
    const online = hb && hb.online;
    const dotColor = online ? getComputedStyle(document.documentElement).getPropertyValue('--good')
                             : getComputedStyle(document.documentElement).getPropertyValue('--critical');
    const lastSeen = hb ? new Date(hb.last_heartbeat_at).toLocaleString() : 'never';
    const tr = document.createElement('tr');
    tr.innerHTML = `<td><span class="dot" style="background:${{dotColor}}"></span>${{online ? 'Online' : 'Offline'}}</td>
                    <td>${{botId}}</td><td>${{meta.kind}}</td><td>${{meta.tenant_id || '—'}}</td>
                    <td>${{meta.status}}</td><td>${{lastSeen}}</td>`;
    tbody.appendChild(tr);
  }}
}}

function renderBotSummaryTable() {{
  const tbody = document.querySelector('#bot-summary-table tbody');
  tbody.innerHTML = '';
  const dash = '—';
  const rows = Object.entries(DATA.summary || {{}}).sort((a, b) => b[1].total_interactions - a[1].total_interactions);
  for (const [botId, s] of rows) {{
    const sh = s.study_hub, eh = s.exam_hub;
    const lastSeen = s.last_seen_at ? new Date(s.last_seen_at).toLocaleString() : dash;
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${{botId}}</td><td>${{s.total_interactions}}</td><td>${{s.unique_users}}</td>
      <td>${{sh ? sh.file_download : dash}}</td>
      <td>${{sh ? (sh.search_query + sh.search_no_match) : dash}}</td>
      <td>${{eh ? eh.sessions : dash}}</td>
      <td>${{eh ? eh.mcq_shown : dash}}</td>
      <td>${{eh ? eh.mcq_answered : dash}}</td>
      <td>${{eh && eh.mcq_accuracy_pct !== null ? eh.mcq_accuracy_pct + '%' : dash}}</td>
      <td>${{eh ? eh.descriptive_shown : dash}}</td>
      <td>${{lastSeen}}</td>`;
    tbody.appendChild(tr);
  }}
  if (rows.length === 0) {{
    tbody.innerHTML = `<tr><td colspan="11" style="color:var(--muted)">No activity recorded yet.</td></tr>`;
  }}
}}

// ---------------------------------------------------------------------
// Date range handling -- recomputed from current DATA every call, not
// captured once at load, so a live Refresh with new dates/bots works.
// ---------------------------------------------------------------------
function isoDate(d) {{ return d.toISOString().slice(0, 10); }}
function daysAgo(n) {{ const d = new Date(); d.setDate(d.getDate() - n); return isoDate(d); }}
function monthStart() {{ const d = new Date(); d.setDate(1); return isoDate(d); }}

function presets() {{
  const allDates = Object.keys(DATA.daily).sort();
  return {{
    'Today': [daysAgo(0), daysAgo(0)],
    'Last 7 days': [daysAgo(6), daysAgo(0)],
    'Last 30 days': [daysAgo(29), daysAgo(0)],
    'This month': [monthStart(), daysAgo(0)],
    'All time': [allDates[0] || daysAgo(0), allDates[allDates.length - 1] || daysAgo(0)],
  }};
}}

let currentRange = null;
let activePresetLabel = 'Last 30 days';

function rebuildRangePresets() {{
  const P = presets();
  if (!currentRange) currentRange = P[activePresetLabel];
  const rangeButtonsDiv = document.getElementById('range-buttons');
  rangeButtonsDiv.innerHTML = '';
  Object.keys(P).forEach(label => {{
    const btn = document.createElement('button');
    btn.textContent = label;
    btn.onclick = () => {{
      activePresetLabel = label;
      currentRange = P[label];
      [...rangeButtonsDiv.children].forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      render();
    }};
    if (label === activePresetLabel) btn.classList.add('active');
    rangeButtonsDiv.appendChild(btn);
  }});
}}

document.getElementById('custom-apply').onclick = () => {{
  const from = document.getElementById('custom-from').value;
  const to = document.getElementById('custom-to').value;
  if (from && to) {{
    activePresetLabel = null;
    currentRange = [from, to];
    [...document.getElementById('range-buttons').children].forEach(b => b.classList.remove('active'));
    render();
  }}
}};

// ---------------------------------------------------------------------
// Compute stats + chart for the current range
// ---------------------------------------------------------------------
function datesInRange(from, to) {{
  return Object.keys(DATA.daily).sort().filter(d => d >= from && d <= to);
}}

function botIdsSortedByVolume() {{
  const totals = {{}};
  for (const day of Object.values(DATA.daily)) {{
    for (const [botId, v] of Object.entries(day)) {{
      totals[botId] = (totals[botId] || 0) + v.count;
    }}
  }}
  return Object.entries(totals).sort((a, b) => b[1] - a[1]).map(([id]) => id);
}}

function render() {{
  const [from, to] = currentRange;
  const dates = datesInRange(from, to);

  // Top-7 bots by volume get their own series; everything else folds into
  // "Other" -- the dataviz skill's own rule for a categorical palette
  // beyond its safe slot count.
  const rankedBotIds = botIdsSortedByVolume();
  const topBotIds = rankedBotIds.slice(0, 7);
  const hasOther = rankedBotIds.length > 7;
  const seriesIds = hasOther ? [...topBotIds, '__other__'] : topBotIds;

  let totalMessages = 0;
  const uniqueUsers = new Set();
  const perDaySeries = dates.map(d => {{
    const day = DATA.daily[d] || {{}};
    const bars = {{}};
    for (const sid of seriesIds) {{
      bars[sid] = 0;
    }}
    for (const [botId, v] of Object.entries(day)) {{
      const key = topBotIds.includes(botId) ? botId : '__other__';
      bars[key] = (bars[key] || 0) + v.count;
      totalMessages += v.count;
      v.users.forEach(u => uniqueUsers.add(u));
    }}
    return {{ date: d, bars }};
  }});

  const onlineCount = Object.values(DATA.heartbeats).filter(h => h.online).length;
  document.getElementById('stat-row').innerHTML = `
    <div class="stat-tile"><div class="label">Bots Configured</div><div class="value">${{Object.keys(DATA.bots).length}}</div></div>
    <div class="stat-tile"><div class="label">Online Now</div><div class="value">${{onlineCount}}</div></div>
    <div class="stat-tile"><div class="label">Messages (${{from}} to ${{to}})</div><div class="value">${{totalMessages}}</div></div>
    <div class="stat-tile" title="Every distinct chat_id with ANY interaction (menu taps, searches, file downloads, MCQs...) across ALL bots -- including Study Hub and MyFiles Hub, not just exam bots.">
      <div class="label">Unique Visitors (${{from}} to ${{to}})</div><div class="value">${{uniqueUsers.size}}</div>
    </div>
    <div class="stat-tile" title="Distinct students who have shown at least one MCQ, deduped across every bot (all-time, not range-limited) -- a smaller, more specific population than Unique Visitors above, which counts ANY interaction on ANY bot.">
      <div class="label">Unique MCQ-Attempters (all-time)</div><div class="value">${{DATA.unique_mcq_attempters ?? '—'}}</div>
    </div>
  `;

  drawChart(perDaySeries, seriesIds);
}}

function drawChart(perDaySeries, seriesIds) {{
  const svg = document.getElementById('chart');
  const tooltip = document.getElementById('tooltip');
  svg.innerHTML = '';
  const W = 900, H = 320, padL = 40, padB = 30, padT = 10, padR = 10;
  const plotW = W - padL - padR, plotH = H - padT - padB;

  const maxVal = Math.max(1, ...perDaySeries.map(d => Object.values(d.bars).reduce((a, b) => a + b, 0)));
  const barW = perDaySeries.length ? Math.max(2, plotW / perDaySeries.length * 0.7) : 0;
  const step = perDaySeries.length ? plotW / perDaySeries.length : 0;

  const ns = 'http://www.w3.org/2000/svg';
  function el(tag, attrs) {{
    const e = document.createElementNS(ns, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    return e;
  }}

  for (let i = 0; i <= 4; i++) {{
    const y = padT + plotH - (plotH * i / 4);
    svg.appendChild(el('line', {{x1: padL, x2: W - padR, y1: y, y2: y, stroke: '{GRIDLINE}', 'stroke-width': 1}}));
    const label = Math.round(maxVal * i / 4);
    const t = el('text', {{x: padL - 6, y: y + 3, 'text-anchor': 'end', class: 'axis-label'}});
    t.textContent = label;
    svg.appendChild(t);
  }}
  svg.appendChild(el('line', {{x1: padL, x2: W - padR, y1: padT + plotH, y2: padT + plotH, stroke: '{BASELINE}', 'stroke-width': 1}}));

  perDaySeries.forEach((d, i) => {{
    let yCursor = padT + plotH;
    const x = padL + i * step + (step - barW) / 2;
    seriesIds.forEach((sid, si) => {{
      const val = d.bars[sid] || 0;
      if (val <= 0) return;
      const h = plotH * val / maxVal;
      yCursor -= h;
      const color = sid === '__other__' ? '{INK_MUTED}' : CATEGORICAL[si % CATEGORICAL.length];
      const rect = el('rect', {{x: x, y: yCursor, width: barW, height: Math.max(0, h - 1), fill: color, rx: 2}});
      rect.addEventListener('mousemove', (evt) => {{
        tooltip.style.opacity = 1;
        tooltip.style.left = (evt.pageX + 12) + 'px';
        tooltip.style.top = (evt.pageY - 12) + 'px';
        const botLabel = sid === '__other__' ? 'Other' : (DATA.bots[sid] ? DATA.bots[sid].display_name : sid);
        tooltip.textContent = `${{d.date}} · ${{botLabel}}: ${{val}}`;
      }});
      rect.addEventListener('mouseleave', () => {{ tooltip.style.opacity = 0; }});
      svg.appendChild(rect);
    }});
    if (perDaySeries.length <= 14 || i % Math.ceil(perDaySeries.length / 14) === 0) {{
      const t = el('text', {{x: x + barW / 2, y: H - 8, 'text-anchor': 'middle', class: 'axis-label'}});
      t.textContent = d.date.slice(5);
      svg.appendChild(t);
    }}
  }});

  const legendDiv = document.getElementById('legend');
  legendDiv.innerHTML = '';
  seriesIds.forEach((sid, si) => {{
    const color = sid === '__other__' ? '{INK_MUTED}' : CATEGORICAL[si % CATEGORICAL.length];
    const label = sid === '__other__' ? 'Other' : (DATA.bots[sid] ? DATA.bots[sid].display_name : sid);
    const item = document.createElement('div');
    item.className = 'legend-item';
    item.innerHTML = `<span class="legend-swatch" style="background:${{color}}"></span>${{label}}`;
    legendDiv.appendChild(item);
  }});
}}

{refresh_js}

applyData(DATA);
</script>
{brand_kit.render_footer_html()}
</body>
</html>
"""


_REFRESH_JS = """
// ---------------------------------------------------------------------
// Live mode only: Refresh button re-queries the platform DB via
// dashboard_server.py's /api/data and re-renders in place -- no full page
// reload, no manual re-run of a script (Pranav, 2026-08-10: "refresh
// button which will make the necessary query and get the latest Bot
// Progress and the Analytics part as well").
// ---------------------------------------------------------------------
const refreshBtn = document.getElementById('refresh-btn');
const refreshStatus = document.getElementById('refresh-status');
refreshBtn.addEventListener('click', async () => {
  refreshBtn.disabled = true;
  refreshStatus.textContent = 'Refreshing…';
  try {
    const resp = await fetch('/api/data');
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const fresh = await resp.json();
    applyData(fresh);
    refreshStatus.textContent = 'Refreshed ' + new Date().toLocaleTimeString();
  } catch (e) {
    refreshStatus.textContent = 'Refresh failed: ' + e.message;
  } finally {
    refreshBtn.disabled = false;
  }
});
"""
