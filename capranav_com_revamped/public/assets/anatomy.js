const $ = (id) => document.getElementById(id);
const state = { hierarchy: null, selectedTopic: "", topics: [], sortKey: null, sortDirection: "asc" };

async function api(path) {
  const response = await fetch(path, { headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error("The database could not be loaded.");
  return response.json();
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}

function option(value, label) { return `<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`; }

function documentActions(documentId, label) {
  if (!documentId) return '<span class="not-available">Not available</span>';
  const base = `/api/anatomy/document?doc=${encodeURIComponent(documentId)}`;
  return `<span class="doc-actions"><a class="doc-link" href="${base}" target="_blank" rel="noopener">Open ${escapeHtml(label)}</a><a class="doc-link secondary" href="${base}&amp;download=1">Download</a></span>`;
}

function populateHierarchy() {
  const { modules } = state.hierarchy;
  $("module-filter").innerHTML = option("", "All modules") + modules.map((x) => option(x.module_id, x.name)).join("");
  refreshChapters();
}

function refreshChapters() {
  const moduleId = $("module-filter").value;
  const chapters = state.hierarchy.chapters.filter((x) => !moduleId || x.module_id === moduleId);
  $("chapter-filter").innerHTML = option("", "All chapters") + chapters.map((x) => option(x.chapter_id, `${x.chapter_no}. ${x.name}`)).join("");
  refreshUnits();
}

function refreshUnits() {
  const chapterId = $("chapter-filter").value;
  const allowedChapters = new Set(Array.from($("chapter-filter").options).map((x) => x.value));
  const units = state.hierarchy.units.filter((x) => (!chapterId || x.chapter_id === chapterId) && allowedChapters.has(x.chapter_id));
  $("unit-filter").innerHTML = option("", "All units") + units.map((x) => option(x.unit_id, x.accounting_standard || x.name)).join("");
}

function compareTopics(a, b) {
  const direction = state.sortDirection === "asc" ? 1 : -1;
  const left = a[state.sortKey];
  const right = b[state.sortKey];
  if (left == null && right == null) return 0;
  if (left == null) return 1;
  if (right == null) return -1;
  if (["overall_rank", "question_count", "linked_marks"].includes(state.sortKey)) return (Number(left) - Number(right)) * direction;
  return String(left).localeCompare(String(right), undefined, { numeric: true, sensitivity: "base" }) * direction;
}

function updateSortIndicators() {
  document.querySelectorAll(".sort-heading").forEach((button) => {
    const active = button.dataset.sort === state.sortKey;
    button.classList.toggle("active", active);
    button.querySelector("span").textContent = active ? (state.sortDirection === "asc" ? "↑" : "↓") : "↕";
    button.setAttribute("aria-sort", active ? (state.sortDirection === "asc" ? "ascending" : "descending") : "none");
  });
}

function renderTopics() {
  const topics = state.sortKey ? [...state.topics].sort(compareTopics) : state.topics;
  $("topic-count").textContent = `${topics.length} topic${topics.length === 1 ? "" : "s"} shown`;
  $("topic-rows").innerHTML = topics.length ? topics.map((t) => `
    <tr data-topic="${escapeHtml(t.topic_id)}">
      <td><span class="topic-name">${escapeHtml(t.topic_no)}. ${escapeHtml(t.name)}</span><span class="topic-id">${escapeHtml(t.topic_id)}</span></td>
      <td>${escapeHtml(t.accounting_standard || t.unit_name)}</td><td>${escapeHtml(t.chapter_name)}</td>
      <td>${escapeHtml(t.page_number || "—")}</td><td>${t.overall_rank ?? "—"}</td>
      <td>${t.priority_band ? `<span class="priority">${escapeHtml(t.priority_band)}</span>` : "—"}</td>
      <td>${t.question_count}</td><td>${t.linked_marks || 0}</td><td>${documentActions(t.study_document_id, "PDF")}</td>
    </tr>`).join("") : '<tr><td colspan="9">No topics match these filters.</td></tr>';
  $("topic-rows").querySelectorAll("tr[data-topic]").forEach((row) => row.addEventListener("click", (event) => {
    if (event.target.closest("a")) return;
    state.selectedTopic = row.dataset.topic;
    loadQuestions();
    $("question-list").scrollIntoView({ behavior: "smooth", block: "start" });
  }));
  updateSortIndicators();
}

async function loadTopics() {
  const params = new URLSearchParams();
  for (const [id, key] of [["module-filter", "module"], ["chapter-filter", "chapter"], ["unit-filter", "unit"], ["priority-filter", "priorityBand"]]) {
    if ($(id).value) params.set(key, $(id).value);
  }
  if ($("topic-search").value.trim()) params.set("q", $("topic-search").value.trim());
  const { topics } = await api(`/api/anatomy/topics?${params}`);
  state.topics = topics;
  renderTopics();
}

async function loadQuestions() {
  const params = new URLSearchParams({ limit: "100" });
  if (state.selectedTopic) params.set("topic", state.selectedTopic);
  if ($("unit-filter").value && !state.selectedTopic) params.set("unit", $("unit-filter").value);
  if ($("paper-filter").value) params.set("paperType", $("paper-filter").value);
  const { questions } = await api(`/api/anatomy/questions?${params}`);
  $("question-list").innerHTML = questions.length ? questions.map((q) => `
    <article class="question"><div class="question-top"><h3>${escapeHtml(q.sitting_label)} · Q${escapeHtml(q.question_no)}${q.sub_part ? `(${escapeHtml(q.sub_part)})` : ""}</h3><strong>${q.marks ?? "—"} marks</strong></div>
    <div class="chips"><span class="chip">${escapeHtml(q.final_unit_name || "Unit mapping pending")}</span><span class="chip">${escapeHtml(q.question_type || "Unclassified")}</span>${q.similarity_percent != null ? `<span class="chip score">${q.similarity_percent}% study-material similarity</span>` : ""}${q.topic_mapping_review ? '<span class="chip">Mapping review required</span>' : ""}</div>
    <div class="question-documents">${documentActions(q.question_document_id, "question PDF")}${documentActions(q.answer_document_id, "answer PDF")}${documentActions(q.comments_document_id, "examiner comments")}</div></article>`).join("") : "<p>No questions match the selected filters.</p>";
}

async function resetExplorer() {
  $("module-filter").value = "";
  refreshChapters();
  $("priority-filter").value = "";
  $("topic-search").value = "";
  $("paper-filter").value = "";
  state.selectedTopic = "";
  state.sortKey = null;
  state.sortDirection = "asc";
  $("question-list").innerHTML = "<p>Select filters above, or open a topic from the syllabus table.</p>";
  await loadTopics();
}

async function start() {
  try {
    const [overview, hierarchy] = await Promise.all([api("/api/anatomy/overview"), api("/api/anatomy/hierarchy")]);
    const values = [overview.counts.modules, overview.counts.units, overview.counts.topics, overview.counts.questions];
    $("stats").querySelectorAll("strong").forEach((node, index) => { node.textContent = values[index].toLocaleString("en-IN"); });
    $("data-note").textContent = `${overview.coverage.mapped_questions} of ${overview.counts.questions} questions currently have topic mappings. ${overview.counts.verified_similarity_rows} PYQ matches have a reviewed similarity score.`;
    if (overview.coverage.questions_missing_marks) $("data-note").classList.add("warning");
    state.hierarchy = hierarchy;
    populateHierarchy();
    await loadTopics();
  } catch (error) {
    $("data-note").textContent = error.message;
    $("data-note").classList.add("warning");
  }
}

$("module-filter").addEventListener("change", () => { state.selectedTopic = ""; refreshChapters(); loadTopics(); });
$("chapter-filter").addEventListener("change", () => { state.selectedTopic = ""; refreshUnits(); loadTopics(); });
$("unit-filter").addEventListener("change", () => { state.selectedTopic = ""; loadTopics(); });
$("priority-filter").addEventListener("change", () => { state.selectedTopic = ""; loadTopics(); });
$("topic-search").addEventListener("input", () => { clearTimeout(window.topicTimer); window.topicTimer = setTimeout(loadTopics, 220); });
$("reset-topics").addEventListener("click", resetExplorer);
document.querySelectorAll(".sort-heading").forEach((button) => button.addEventListener("click", () => {
  if (state.sortKey === button.dataset.sort) state.sortDirection = state.sortDirection === "asc" ? "desc" : "asc";
  else { state.sortKey = button.dataset.sort; state.sortDirection = "asc"; }
  renderTopics();
}));
$("show-questions").addEventListener("click", () => { state.selectedTopic = ""; loadQuestions(); });
$("paper-filter").addEventListener("change", loadQuestions);
start();
