/* /topics/ — Important Topics explorer.
   Everything is computed in the browser from /topics/data/topics.json, so any mix of
   paper type, year, attempt, module, chapter and unit re-ranks instantly.
   Data is built by tools/build_topics_explorer_data.py. */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function fmt(n) { return Number.isInteger(n) ? String(n) : (Math.round(n * 10) / 10).toString(); }

  var D = null;            // topics.json
  var unitById = {};       // "M2-C5-U2" -> unit
  var topicById = {};      // "M2-C5-U2-T2.6" -> topic
  var chapters = [];       // [{key:"2-5", module, no, name, units:[unit...]}]
  var PAPERS = ["PYQ", "MTP", "RTP"];
  var MONTHS = [["January", "Jan"], ["May", "May"], ["September", "Sep"], ["November", "Nov"]];
  var PAPER_TEXT = { PYQ: "PYQ (past exams)", MTP: "MTP (mock tests)", RTP: "RTP (revision tests)" };

  var DEFAULTS = {
    papers: ["PYQ"], years: [], months: [], modules: [], chapters: [], units: [], q: "",
    sort: "measure", reverse: false, limit: 100, zero: false, preset: "top100"
  };
  var state = JSON.parse(JSON.stringify(DEFAULTS));

  var PRESETS = [
    { id: "top100", title: "Top 100 topics", note: "From real past exam papers. The classic must-study list.",
      set: { papers: ["PYQ"], limit: 100 } },
    { id: "mtp", title: "What mock tests love", note: "Topics ICAI's Mock Test Papers keep setting.",
      set: { papers: ["MTP"], limit: 50 } },
    { id: "rtp", title: "Revision test favourites", note: "Topics in Revision Test Papers, by times asked.",
      set: { papers: ["RTP"], limit: 50 } },
    { id: "all", title: "Everything ICAI has asked", note: "Past exams, mocks and revision tests together.",
      set: { papers: PAPERS.slice(), limit: 100 } },
    { id: "recent", title: "Asked most recently", note: "Only the latest year of papers.",
      set: { papers: PAPERS.slice(), limit: 50, latestYear: true } },
    { id: "never", title: "Never asked yet", note: "Topics no paper has tested. Lower priority, but not zero risk.",
      set: { papers: PAPERS.slice(), limit: 0, zero: true, sort: "syllabus" } }
  ];

  // ------------------------------------------------------------------ ranking
  // For a set of filters, aggregate every topic and rank all 400.
  function compute(f) {
    var papers = new Set(f.papers), years = new Set(f.years.map(Number)), months = new Set(f.months);
    var okSitting = D.sittings.map(function (s) {
      return papers.has(s.type) && (!years.size || years.has(s.year)) && (!months.size || months.has(s.month));
    });
    var agg = D.topics.map(function (t, i) {
      return { i: i, t: t, marks: 0, count: 0, sit: new Set(), last: -1, lastSitting: null, items: [] };
    });
    D.rows.forEach(function (r) {
      if (!okSitting[r[1]]) return;
      var a = agg[r[0]], s = D.sittings[r[1]];
      a.marks += r[2]; a.count += 1; a.sit.add(r[1]);
      var order = s.year * 100 + s.monthNo;
      if (order > a.last) { a.last = order; a.lastSitting = s; }
      a.items.push({ s: s, q: r[3], marks: r[2] });
    });
    // Marks are split into thirds etc.; round to 2 places so equal scores compare equal.
    agg.forEach(function (a) { a.marks = Math.round(a.marks * 100) / 100; });
    var onlyRtp = f.papers.length > 0 && f.papers.every(function (p) { return p === "RTP"; });
    var key = onlyRtp ? "count" : "marks";
    // Equal score: fall back to the workbook's own rank, so the default view reproduces
    // Pranav's official ranking exactly (its tie order is not derivable from the counts).
    // RTP-only views have no marks, so they prefer more papers before that fallback.
    var official = function (a) { return a.t.officialRank || 1e6; };
    var ranked = agg.slice().sort(function (x, y) {
      return (y[key] - x[key]) || (onlyRtp ? y.sit.size - x.sit.size : 0) || (official(x) - official(y)) || (x.i - y.i);
    });
    var pos = 0;
    ranked.forEach(function (a) { a.measure = a[key]; a.rank = a.count > 0 ? ++pos : null; });
    return { agg: agg, ranked: ranked, key: key, onlyRtp: onlyRtp, max: ranked.length ? ranked[0][key] : 0 };
  }

  function band(a) {
    if (!a.count) return { cls: "none", text: "Not asked yet" };
    if (a.rank <= 50) return { cls: "must", text: "Must know" };
    if (a.rank <= 100) return { cls: "imp", text: "Important" };
    return { cls: "good", text: "Good to know" };
  }

  function pageKey(p) {
    var m = /^(\d+)\.(\d+)/.exec(p || "");
    return m ? Number(m[1]) * 1000 + Number(m[2]) : 1e9;
  }

  function compareFor(sort) {
    var byOrder = function (x, y) { return x.i - y.i; };
    var official = function (a) { return a.t.officialRank || 1e6; };
    switch (sort) {
      case "count": return function (x, y) { return (y.count - x.count) || (y.marks - x.marks) || byOrder(x, y); };
      case "last": return function (x, y) { return (y.last - x.last) || (y.count - x.count) || byOrder(x, y); };
      case "syllabus": return function (x, y) {
        return (D.units[x.t.unit].teach - D.units[y.t.unit].teach) || byOrder(x, y); };
      case "name": return function (x, y) { return x.t.name.localeCompare(y.t.name) || byOrder(x, y); };
      case "page": return function (x, y) { return (pageKey(x.t.page) - pageKey(y.t.page)) || byOrder(x, y); };
      default: return function (x, y) { return (y.measure - x.measure) || (official(x) - official(y)) || byOrder(x, y); };
    }
  }

  function currentList() {
    var res = compute(state);
    var q = state.q.trim().toLowerCase();
    var qid = q.replace(/_/g, "-");
    var list = res.agg.filter(function (a) {
      var u = D.units[a.t.unit];
      if (state.modules.length && state.modules.indexOf(String(u.module)) < 0) return false;
      if (state.chapters.length && state.chapters.indexOf(u.module + "-" + u.chapterNo) < 0) return false;
      if (state.units.length && state.units.indexOf(u.id) < 0) return false;
      if (state.zero && a.count > 0) return false;
      if (q) {
        var hay = (a.t.name + " " + u.chapter + " " + u.unit + " " + a.t.id).toLowerCase();
        if (hay.indexOf(q) < 0 && a.t.id.toLowerCase().indexOf(qid) < 0) return false;
      }
      return true;
    });
    // Rank-based sorts read `measure`; the compute step already set it for every topic.
    var cmp = compareFor(state.sort);
    list.sort(cmp);
    if (state.reverse) list.reverse();
    return { res: res, all: list, shown: state.limit ? list.slice(0, state.limit) : list };
  }

  // ------------------------------------------------------------------ rendering
  function sortLabel(sort, res) {
    var word = res.onlyRtp ? "times asked" : "marks";
    switch (sort) {
      case "count": return state.reverse ? "fewest times asked first" : "most times asked first";
      case "last": return state.reverse ? "oldest first" : "most recent first";
      case "syllabus": return state.reverse ? "syllabus order, reversed" : "syllabus order (as taught)";
      case "name": return state.reverse ? "topic name, Z to A" : "topic name, A to Z";
      case "page": return state.reverse ? "Study Material page, last to first" : "Study Material page order";
      default: return state.reverse ? "fewest " + word + " first" : "most " + word + " first";
    }
  }

  function scopeText() {
    var p = state.papers.length ? state.papers.join(" + ") : "no paper type";
    var y = state.years.length ? state.years.slice().sort().join(", ") : "all years";
    var m = state.months.length ? state.months.join(", ") + " attempts" : "all attempts";
    var where = "the whole syllabus";
    var names = function (n, one, many) { return n + " " + (n === 1 ? one : many); };
    if (state.units.length) where = state.units.length === 1 ? unitById[state.units[0]].unit : names(state.units.length, "unit", "units") + " selected";
    else if (state.chapters.length) {
      var picked = chapters.filter(function (x) { return state.chapters.indexOf(x.key) >= 0; });
      where = picked.length === 1 ? "Chapter " + picked[0].no + " (" + picked[0].name + ")" : names(picked.length, "chapter", "chapters") + " selected";
    } else if (state.modules.length) where = state.modules.length === 1 ? "Module " + state.modules[0] : "Modules " + state.modules.slice().sort().join(", ");
    return { p: p, y: y, m: m, where: where };
  }

  function render() {
    var out = currentList();
    var res = out.res, shown = out.shown;
    var s = scopeText();
    $("summary").textContent = "Showing " + shown.length + " of " + out.all.length + " topic" + (out.all.length === 1 ? "" : "s") +
      " · " + s.p + " · " + s.y + " · " + s.m + " · " + s.where + " · " +
      sortLabel(state.sort, res) + (state.zero ? " · only topics never asked" : "") + ".";
    $("rtp-note").hidden = !res.onlyRtp;
    $("th-measure").textContent = res.onlyRtp ? "Questions" : "Marks";

    // heading arrows
    Array.prototype.forEach.call(document.querySelectorAll(".t-table thead button"), function (b) {
      if (b.dataset.sort === state.sort) b.setAttribute("aria-sort", state.reverse ? "ascending" : "descending");
      else b.removeAttribute("aria-sort");
    });
    // Descending is the natural direction for measure/count/last; ascending for the rest.
    var natural = { measure: "descending", count: "descending", last: "descending", syllabus: "ascending", name: "ascending", page: "ascending" };
    var active = document.querySelector('.t-table thead button[data-sort="' + state.sort + '"]');
    if (active) {
      var dir = natural[state.sort];
      if (state.reverse) dir = dir === "descending" ? "ascending" : "descending";
      active.setAttribute("aria-sort", dir);
    }

    var body = $("rows");
    body.textContent = "";
    if (!shown.length) {
      var tr = el("tr"); var td = el("td", "empty", "No topics match these choices. Try ticking more papers or years, or press “Reset everything”.");
      td.colSpan = 6; tr.appendChild(td); body.appendChild(tr); return;
    }
    shown.forEach(function (a) { body.appendChild(rowFor(a, res)); });
  }

  function rowFor(a, res) {
    var u = D.units[a.t.unit], b = band(a);
    var tr = el("tr", "t-row");
    tr.tabIndex = 0; tr.setAttribute("aria-expanded", "false");
    var c1 = el("td", "c-rank"); c1.appendChild(el("span", "rank", a.rank ? "#" + a.rank : "—"));
    var c2 = el("td");
    c2.appendChild(el("div", "tname", a.t.name));
    c2.appendChild(el("div", "tpath", u.chapter + (u.single ? "" : " › " + u.unit)));
    c2.appendChild(el("span", "tag " + b.cls, b.text));
    var c3 = el("td", "c-marks");
    var num = el("span", "num", a.count ? fmt(a.measure) : "0");
    c3.appendChild(num);
    if (res.max > 0) { var bar = el("span", "bar"); var i = el("i"); i.style.width = Math.round((a.measure / res.max) * 100) + "%"; bar.appendChild(i); c3.appendChild(bar); }
    var c4 = el("td", "c-times");
    c4.appendChild(el("span", "num", String(a.count)));
    if (a.count) c4.appendChild(el("span", "small", "in " + a.sit.size + " paper" + (a.sit.size === 1 ? "" : "s")));
    var c5 = el("td", "c-last");
    if (a.lastSitting) { c5.appendChild(el("span", "num", a.lastSitting.month.slice(0, 3) + " " + a.lastSitting.year)); c5.appendChild(el("span", "small", a.lastSitting.type)); }
    else c5.appendChild(el("span", "num", "—"));
    var c6 = el("td", "c-page", a.t.page || "—");
    [c1, c2, c3, c4, c5, c6].forEach(function (c) { tr.appendChild(c); });

    var detail = null;
    function toggle() {
      if (detail) { detail.remove(); detail = null; tr.setAttribute("aria-expanded", "false"); return; }
      detail = el("tr", "detail-row");
      var td = el("td"); td.colSpan = 6;
      var box = el("div", "detail");
      box.appendChild(el("div", "meta", "Topic ID " + a.t.id + " · Module " + u.module + ", Chapter " + u.chapterNo + (u.single ? "" : ", " + u.unit) +
        " · Study Material page " + (a.t.page || "—") +
        (a.t.officialRank ? " · Officially #" + a.t.officialRank + " of 400 by past-exam marks (" + a.t.band + ")" : "")));
      if (!a.items.length) {
        box.appendChild(el("p", null, "No paper in your current selection has asked this topic."));
      } else {
        box.appendChild(el("p", null, "Asked " + a.items.length + " time" + (a.items.length === 1 ? "" : "s") + " in the papers you selected:"));
        var ul = el("ul");
        a.items.slice().sort(function (x, y) { return (y.s.year * 100 + y.s.monthNo) - (x.s.year * 100 + x.s.monthNo); }).forEach(function (it) {
          ul.appendChild(el("li", null, it.s.label + " — " + it.q + (it.s.type === "RTP" ? " (no marks printed)" : " — " + fmt(it.marks) + " mark" + (it.marks === 1 ? "" : "s"))));
        });
        box.appendChild(ul);
      }
      td.appendChild(box); detail.appendChild(td);
      tr.parentNode.insertBefore(detail, tr.nextSibling);
      tr.setAttribute("aria-expanded", "true");
    }
    tr.addEventListener("click", toggle);
    tr.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); } });
    return tr;
  }

  // ------------------------------------------------------------------ controls
  function chip(text, pressed, onClick) {
    var b = el("button", "chip", text); b.type = "button"; b.setAttribute("aria-pressed", String(pressed));
    b.addEventListener("click", onClick); return b;
  }
  function toggleIn(arr, v) { var i = arr.indexOf(v); if (i >= 0) arr.splice(i, 1); else arr.push(v); }

  function buildPresets() {
    var host = $("presets"); host.textContent = "";
    PRESETS.forEach(function (p) {
      var b = el("button", "preset"); b.type = "button"; b.setAttribute("aria-pressed", String(state.preset === p.id));
      b.appendChild(el("strong", null, p.title)); b.appendChild(el("span", null, p.note));
      b.addEventListener("click", function () { applyPreset(p); });
      host.appendChild(b);
    });
  }

  function latestYear() { return Math.max.apply(null, D.sittings.map(function (s) { return s.year; })); }

  function applyPreset(p) {
    var keep = { modules: state.modules, chapters: state.chapters, units: state.units, q: state.q };
    state = JSON.parse(JSON.stringify(DEFAULTS));
    state.modules = keep.modules; state.chapters = keep.chapters; state.units = keep.units; state.q = keep.q;
    Object.keys(p.set).forEach(function (k) { if (k !== "latestYear") state[k] = JSON.parse(JSON.stringify(p.set[k])); });
    if (p.set.latestYear) state.years = [String(latestYear())];
    state.preset = p.id;
    syncControls(); render();
  }

  function buildFilters() {
    var papers = $("f-papers"); papers.textContent = "";
    PAPERS.forEach(function (p) {
      papers.appendChild(chip(PAPER_TEXT[p], state.papers.indexOf(p) >= 0, function () { toggleIn(state.papers, p); changed(); }));
    });
    var years = $("f-years"); years.textContent = "";
    var ys = Array.from(new Set(D.sittings.map(function (s) { return s.year; }))).sort();
    ys.forEach(function (y) {
      years.appendChild(chip(String(y), state.years.indexOf(String(y)) >= 0, function () { toggleIn(state.years, String(y)); changed(); }));
    });
    var months = $("f-months"); months.textContent = "";
    MONTHS.forEach(function (m) {
      months.appendChild(chip(m[1], state.months.indexOf(m[0]) >= 0, function () { toggleIn(state.months, m[0]); changed(); }));
    });
  }

  // ---- tick-many pickers for Module / Chapter / Unit ------------------------------
  function unitLabel(u) {
    return u.single ? u.chapter + " (whole chapter)" : (u.standard ? u.standard + " — " + u.unit.replace(/^Accounting Standard \d+\s*/i, "") : u.unit);
  }

  function multiItem(value, text, checked, onChange) {
    var lab = el("label", "ms-item"), cb = el("input"); cb.type = "checkbox"; cb.value = value; cb.checked = checked;
    cb.addEventListener("change", function () { onChange(value, cb.checked); });
    lab.appendChild(cb); lab.appendChild(el("span", null, text)); return lab;
  }

  function toggleValue(arr, v, on) { var i = arr.indexOf(v); if (on && i < 0) arr.push(v); if (!on && i >= 0) arr.splice(i, 1); }

  function visibleChapters() {
    return chapters.filter(function (c) { return !state.modules.length || state.modules.indexOf(String(c.module)) >= 0; });
  }
  function visibleUnits() {
    return D.units.filter(function (u) {
      var chapterKey = u.module + "-" + u.chapterNo;
      if (state.chapters.length) return state.chapters.indexOf(chapterKey) >= 0;
      return !state.modules.length || state.modules.indexOf(String(u.module)) >= 0;
    });
  }

  function summaryText(n, all, one, many) { return n ? n + " " + (n === 1 ? one : many) + " ticked" : all; }

  function buildMulti() {
    // Drop ticks that are no longer offered (e.g. a chapter whose module was just unticked).
    var chKeys = visibleChapters().map(function (c) { return c.key; });
    state.chapters = state.chapters.filter(function (k) { return chKeys.indexOf(k) >= 0; });
    var unitIds = visibleUnits().map(function (u) { return u.id; });
    state.units = state.units.filter(function (k) { return unitIds.indexOf(k) >= 0; });

    var mods = Array.from(new Set(D.units.map(function (u) { return u.module; }))).sort();
    var lm = $("l-module"); lm.textContent = "";
    mods.forEach(function (m) {
      lm.appendChild(multiItem(String(m), "Module " + m, state.modules.indexOf(String(m)) >= 0, function (v, on) { toggleValue(state.modules, v, on); afterPick(true); }));
    });
    var lc = $("l-chapter"); lc.textContent = "";
    visibleChapters().forEach(function (c) {
      lc.appendChild(multiItem(c.key, c.no + ". " + c.name, state.chapters.indexOf(c.key) >= 0, function (v, on) { toggleValue(state.chapters, v, on); afterPick(true); }));
    });
    var lu = $("l-unit"); lu.textContent = "";
    var lastChapter = null;
    visibleUnits().forEach(function (u) {
      var key = u.module + "-" + u.chapterNo;
      if (key !== lastChapter) { lu.appendChild(el("div", "ms-group", "Chapter " + u.chapterNo + " · " + u.chapter)); lastChapter = key; }
      lu.appendChild(multiItem(u.id, unitLabel(u), state.units.indexOf(u.id) >= 0, function (v, on) { toggleValue(state.units, v, on); afterPick(false); }));
    });
    updateSummaries();
  }

  function updateSummaries() {
    $("ms-module").textContent = state.modules.length ? "Module " + state.modules.slice().sort().join(", ") + " ticked" : "All modules";
    $("ms-chapter").textContent = summaryText(state.chapters.length, "All chapters", "chapter", "chapters");
    $("ms-unit").textContent = summaryText(state.units.length, "All units", "unit", "units");
  }

  // A tick in a parent list changes which children are offered, so rebuild; a unit tick only re-renders.
  function afterPick(rebuild) {
    if (rebuild) {
      var lists = ["l-module", "l-chapter", "l-unit"], tops = lists.map(function (id) { return $(id).scrollTop; });
      buildMulti();
      lists.forEach(function (id, i) { $(id).scrollTop = tops[i]; });
    } else {
      updateSummaries();
    }
    render();
  }

  function wireMulti() {
    [["module", "modules", function () { return D.units.map(function (u) { return String(u.module); }); }],
     ["chapter", "chapters", function () { return visibleChapters().map(function (c) { return c.key; }); }],
     ["unit", "units", function () { return visibleUnits().map(function (u) { return u.id; }); }]].forEach(function (cfg) {
      $("m-" + cfg[0]).addEventListener("click", function (e) {
        var act = e.target && e.target.dataset && e.target.dataset.act;
        if (!act) return;
        e.preventDefault();
        state[cfg[1]] = act === "all" ? Array.from(new Set(cfg[2]())) : [];
        afterPick(true);
      });
    });
  }

  function syncControls() {
    buildPresets(); buildFilters(); buildMulti();
    $("f-search").value = state.q;
    $("f-sort").value = state.sort;
    $("f-limit").value = String(state.limit);
    $("reverse").setAttribute("aria-pressed", String(state.reverse));
  }

  function changed() { state.preset = ""; buildPresets(); buildFilters(); render(); }

  function wire() {
    wireMulti();
    $("f-search").addEventListener("input", function (e) { state.q = e.target.value; render(); });
    $("f-sort").addEventListener("change", function (e) { state.sort = e.target.value; state.reverse = false; $("reverse").setAttribute("aria-pressed", "false"); render(); });
    $("f-limit").addEventListener("change", function (e) { state.limit = Number(e.target.value); render(); });
    $("reverse").addEventListener("click", function () { state.reverse = !state.reverse; $("reverse").setAttribute("aria-pressed", String(state.reverse)); render(); });
    $("reset").addEventListener("click", function () { state = JSON.parse(JSON.stringify(DEFAULTS)); syncControls(); render(); });
    Array.prototype.forEach.call(document.querySelectorAll(".t-table thead button"), function (b) {
      b.addEventListener("click", function () {
        var k = b.dataset.sort;
        if (state.sort === k) state.reverse = !state.reverse; else { state.sort = k; state.reverse = false; }
        $("f-sort").value = state.sort; $("reverse").setAttribute("aria-pressed", String(state.reverse)); render();
      });
    });
  }
  // Choosing where to look (module/chapter/unit) narrows the current view; it does not turn a preset off.

  // ------------------------------------------------------------------ downloads
  var xlsxPromise = null;
  function loadXlsx() {
    if (window.XLSX) return Promise.resolve(window.XLSX);
    if (xlsxPromise) return xlsxPromise;
    xlsxPromise = new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = "https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js";
      s.integrity = "sha512-r22gChDnGvBylk90+2e/ycr3RVrDi8DIOkIGNhJlKfuyQM4tIRAI062MaV8sfjQKYVGjOBaZBOA87z+IhZE9DA==";
      s.crossOrigin = "anonymous"; s.referrerPolicy = "no-referrer";
      s.onload = function () { resolve(window.XLSX); };
      s.onerror = function () { xlsxPromise = null; reject(new Error("The Excel helper could not be loaded. Check your connection and try again.")); };
      document.head.appendChild(s);
    });
    return xlsxPromise;
  }

  function stamp() { var d = new Date(); return d.getFullYear() + String(d.getMonth() + 1).padStart(2, "0") + String(d.getDate()).padStart(2, "0"); }

  function saveXlsx(sheetName, header, rows, filename) {
    return loadXlsx().then(function (X) {
      var ws = X.utils.aoa_to_sheet([header].concat(rows));
      var widths = header.map(function (h, c) {
        var w = String(h).length;
        for (var r = 0; r < Math.min(rows.length, 200); r++) { var v = rows[r][c]; if (v != null) w = Math.max(w, String(v).length); }
        return { wch: Math.min(Math.max(w + 2, 8), 60) };
      });
      ws["!cols"] = widths;
      var wb = X.utils.book_new();
      X.utils.book_append_sheet(wb, ws, sheetName.slice(0, 31));
      // Every workbook carries its provenance on a second sheet, leaving the data sheet untouched.
      var about = X.utils.aoa_to_sheet([
        ["Powered by 1LAVYA"],
        ["This analysis is built from the 1LAVYA data repository."],
        ["Source page: https://capranav.com/topics/  ·  https://1lavya.com/?utm_source=capranav&utm_medium=referral&utm_campaign=powered_by&utm_content=excel_download"],
        ["Generated on " + new Date().toISOString().slice(0, 10)],
        ["Marks: a question's marks are split equally across the topics it tests. RTP questions carry no printed marks."]
      ]);
      about["!cols"] = [{ wch: 90 }];
      X.utils.book_append_sheet(wb, about, "Powered by 1LAVYA");
      X.writeFile(wb, filename);
    });
  }

  function csvCell(v) { var s = v == null ? "" : String(v); return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; }
  function saveCsv(header, rows, filename) {
    var text = "﻿" + [header].concat(rows).map(function (r) { return r.map(csvCell).join(","); }).join("\r\n");
    var url = URL.createObjectURL(new Blob([text], { type: "text/csv;charset=utf-8" }));
    var a = el("a"); a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
    return Promise.resolve();
  }

  function viewTable(list, res) {
    var word = res.onlyRtp ? "Questions" : "Marks";
    var header = ["Rank", "Priority", "Topic", "Chapter", "Unit", "Module", word, "Times asked", "Papers it appeared in", "Last asked", "Study Material page", "Topic ID"];
    var rows = list.map(function (a) {
      var u = D.units[a.t.unit];
      return [a.rank || "", band(a).text, a.t.name, u.chapter, u.single ? "" : u.unit, "Module " + u.module,
        a.count ? a.measure : 0, a.count,
        Array.from(a.sit).sort(function (x, y) { return y - x; }).map(function (i) { return D.sittings[i].label; }).join("; "),
        a.lastSitting ? a.lastSitting.label : "", a.t.page || "", a.t.id];
    });
    return { header: header, rows: rows };
  }

  function busy(btn, on) { if (btn) btn.disabled = on; }
  function message(text) { $("dl-msg").textContent = text || ""; }

  function runDownload(btn, task) {
    busy(btn, true); message("Preparing your file…");
    task().then(function () { message("Done — check your downloads."); })
      .catch(function (e) { message(e && e.message ? e.message : "Something went wrong. Please try again."); })
      .then(function () { busy(btn, false); });
  }

  function generatedList(papers) {
    var res = compute({ papers: papers, years: [], months: [] });
    var list = res.ranked.filter(function (a) { return a.count > 0; });
    return { list: list, res: res };
  }

  function buildDownloads(sheets) {
    var grid = $("dl-grid"); grid.textContent = "";
    function add(title, note, task) {
      var b = el("button", "btn"); b.type = "button";
      b.appendChild(el("strong", null, title)); b.appendChild(el("span", null, note));
      b.addEventListener("click", function () { runDownload(b, task); });
      grid.appendChild(b);
    }
    function sheetTask(item) {
      return function () {
        return fetch("/topics/data/sheets/" + item.slug + ".json").then(function (r) { if (!r.ok) throw new Error("That list could not be loaded."); return r.json(); })
          .then(function (s) { return saveXlsx(s.title, s.header, s.rows, "capranav-" + item.slug + ".xlsx"); });
      };
    }
    var byslug = {}; sheets.forEach(function (s) { byslug[s.slug] = s; });
    if (byslug["top-100-pyq"]) add("Top 100 topics", "Ranked by marks in past exam papers", sheetTask(byslug["top-100-pyq"]));
    add("MTP-wise topic list", "Every topic the mock tests asked, most marks first", function () {
      var g = generatedList(["MTP"]), t = viewTable(g.list, g.res); return saveXlsx("MTP topics", t.header, t.rows, "capranav-mtp-topics.xlsx");
    });
    add("RTP-wise topic list", "Every topic the revision tests asked, by times asked", function () {
      var g = generatedList(["RTP"]), t = viewTable(g.list, g.res); return saveXlsx("RTP topics", t.header, t.rows, "capranav-rtp-topics.xlsx");
    });
    add("PYQ-wise topic list", "Every topic past exams asked, most marks first", function () {
      var g = generatedList(["PYQ"]), t = viewTable(g.list, g.res); return saveXlsx("PYQ topics", t.header, t.rows, "capranav-pyq-topics.xlsx");
    });
    ["chapter-priority", "topic-attempts", "question-topic-map", "abcd-questions", "study-topics"].forEach(function (slug) {
      if (byslug[slug]) add(byslug[slug].title, byslug[slug].use, sheetTask(byslug[slug]));
    });
  }

  function wireDownloads() {
    $("dl-view-xlsx").addEventListener("click", function () {
      var o = currentList(), t = viewTable(o.shown, o.res);
      runDownload($("dl-view-xlsx"), function () { return saveXlsx("My topic list", t.header, t.rows, "capranav-my-topic-list-" + stamp() + ".xlsx"); });
    });
    $("dl-view-csv").addEventListener("click", function () {
      var o = currentList(), t = viewTable(o.shown, o.res);
      runDownload($("dl-view-csv"), function () { return saveCsv(t.header, t.rows, "capranav-my-topic-list-" + stamp() + ".csv"); });
    });
  }

  // ------------------------------------------------------------------ ID decoder
  function decode(input) {
    var raw = String(input || "").trim();
    var m = /^m(\d+)[-_ ]?c(\d+)(?:[-_ ]?u(\d+))?(?:[-_ ]?t(\d+(?:\.\d+)?))?/i.exec(raw);
    if (!m) return { ok: false, text: "That does not look like a topic ID. They start like M2-C5-U2-T2.6: M (module), C (chapter), U (unit), T (topic)." };
    var mod = Number(m[1]), ch = Number(m[2]), un = m[3] != null ? Number(m[3]) : null, tp = m[4] || null;
    var chapterUnits = D.units.filter(function (u) { return u.module === mod && u.chapterNo === ch; });
    if (!chapterUnits.length) {
      var elsewhere = D.units.filter(function (u) { return u.chapterNo === ch; });
      var mods = Array.from(new Set(D.units.filter(function (u) { return u.module === mod; }).map(function (u) { return u.chapterNo; }))).sort(function (a, b) { return a - b; });
      var msg = "There is no Chapter " + ch + " in Module " + mod + ".";
      if (mods.length) msg += " Module " + mod + " has chapters " + mods[0] + "–" + mods[mods.length - 1] + ".";
      else msg += " The modules are 1, 2 and 3.";
      if (elsewhere.length) msg += " Chapter " + ch + " is in Module " + elsewhere[0].module + " (" + elsewhere[0].chapter + ") — did you mean M" + elsewhere[0].module + "-C" + ch + "?";
      return { ok: false, text: msg };
    }
    var unit = un == null ? null : chapterUnits.filter(function (u) { return Number(u.id.split("-U")[1]) === un; })[0];
    if (un != null && !unit) {
      return { ok: false, text: "Chapter " + ch + " (" + chapterUnits[0].chapter + ") has units " + chapterUnits.map(function (u) { return u.id.split("-U")[1]; }).join(", ") + " — there is no Unit " + un + "." };
    }
    if (!unit) {
      return { ok: true, text: "Module " + mod + " · Chapter " + ch + " — " + chapterUnits[0].chapter + ". It has " + chapterUnits.length + " unit" + (chapterUnits.length === 1 ? "" : "s") + ": " +
        chapterUnits.map(function (u) { return (u.standard || u.unit); }).join(", ") + "." };
    }
    var head = "Module " + mod + " · Chapter " + ch + " (" + unit.chapter + ")" + (unit.single ? " · a one-unit chapter" : " · Unit " + un + " (" + unit.unit + ")");
    if (!tp) return { ok: true, text: head + "." };
    var topic = topicById[unit.id + "-T" + tp];
    if (!topic) return { ok: false, text: head + ", but there is no topic " + tp + " in it. Topic numbers in this unit run " + unitTopicRange(unit) + "." };
    return { ok: true, text: head + " · Topic " + tp + " — " + topic.name + ". ICAI Study Material page " + topic.page + " (chapter " + String(topic.page).split(".")[0] + ", page " + String(topic.page).split(".")[1] + ")." };
  }
  function unitTopicRange(unit) {
    var nos = D.topics.filter(function (t) { return D.units[t.unit].id === unit.id; }).map(function (t) { return t.no; });
    return nos[0] + " to " + nos[nos.length - 1];
  }

  function buildIdExample() {
    var id = "M2-C5-U2-T2.6", d = decode(id), t = topicById[id];
    var u = D.units[t.unit];
    var segs = [
      ["m", "M2", "Module 2"],
      ["c", "C5", "Chapter 5: " + u.chapter],
      ["u", "U2", "Unit 2: " + u.unit],
      ["t", "T2.6", "Topic 6 of Unit 2: " + t.name]
    ];
    var host = $("id-example"); host.textContent = "";
    segs.forEach(function (s, i) {
      if (i) host.appendChild(el("span", "sep", "–"));
      var box = el("div", "seg " + s[0]); box.appendChild(el("b", null, s[1])); box.appendChild(el("small", null, s[2])); host.appendChild(box);
    });
    var pg = el("div", "seg"); pg.appendChild(el("b", null, t.page)); pg.appendChild(el("small", null, "Study Material page: chapter " + t.page.split(".")[0] + ", page " + t.page.split(".")[1]));
    host.appendChild(el("span", "sep", "→")); host.appendChild(pg);
  }

  function wireDecoder() {
    var input = $("decode-in"), out = $("decode-out");
    input.addEventListener("input", function () {
      out.textContent = "";
      if (!input.value.trim()) return;
      var r = decode(input.value);
      out.appendChild(el("div", r.ok ? "ok" : "bad", r.text));
    });
  }

  // ------------------------------------------------------------------ start
  function scope() {
    var counts = { PYQ: new Set(), MTP: new Set(), RTP: new Set() };
    D.sittings.forEach(function (s, i) { counts[s.type].add(i); });
    var first = D.sittings.slice().sort(function (a, b) { return (a.year * 100 + a.monthNo) - (b.year * 100 + b.monthNo); });
    $("scope").textContent = counts.PYQ.size + " PYQ papers, " + counts.MTP.size + " MTP sets and " + counts.RTP.size + " RTP papers, from " +
      first[0].month + " " + first[0].year + " to " + first[first.length - 1].month + " " + first[first.length - 1].year + " — " + D.rows.length +
      " question-to-topic links across the 400 topics of the Study Material. Only descriptive questions are counted (MCQs are practised on the Telegram bot).";
  }

  function init() {
    Promise.all([
      fetch("/topics/data/topics.json").then(function (r) { if (!r.ok) throw new Error("topics"); return r.json(); }),
      fetch("/topics/data/sheets/index.json").then(function (r) { return r.ok ? r.json() : []; }).catch(function () { return []; })
    ]).then(function (res) {
      D = res[0];
      D.units.forEach(function (u) { unitById[u.id] = u; });
      D.topics.forEach(function (t) { topicById[t.id] = t; });
      var seen = {};
      D.units.forEach(function (u) {
        var key = u.module + "-" + u.chapterNo;
        if (!seen[key]) { seen[key] = { key: key, module: u.module, no: u.chapterNo, name: u.chapter, units: [] }; chapters.push(seen[key]); }
        seen[key].units.push(u);
      });
      chapters.sort(function (a, b) { return (a.module - b.module) || (a.no - b.no); });
      $("status").hidden = true;
      syncControls(); wire(); wireDownloads(); buildDownloads(res[1]); buildIdExample(); wireDecoder(); scope();
      applyDeepLink();
      render();
    }).catch(function () {
      $("status").textContent = "The topic list could not be loaded. Please refresh the page.";
    });
  }

  function applyDeepLink() {
    var q = new URLSearchParams(location.search), p = q.get("view");
    var preset = PRESETS.filter(function (x) { return x.id === p; })[0];
    if (preset) applyPreset(preset);
    var wanted = (q.get("unit") || "").split(",").filter(function (id) { return unitById[id]; });
    if (wanted.length) { state.units = wanted; syncControls(); }
  }

  init();
})();
