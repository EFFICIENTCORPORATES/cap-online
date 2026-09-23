-- The Anatomy of Advanced Accounts: relational syllabus and exam-intelligence schema.
-- Additive only: the existing commerce, login, order, and entitlement tables are untouched.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS aa_subjects (
  subject_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  short_name TEXT NOT NULL,
  course_level TEXT NOT NULL,
  active_edition TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS aa_modules (
  module_id TEXT PRIMARY KEY,
  subject_id TEXT NOT NULL REFERENCES aa_subjects(subject_id),
  module_no INTEGER NOT NULL,
  name TEXT NOT NULL,
  display_order INTEGER NOT NULL,
  UNIQUE(subject_id, module_no)
);

CREATE TABLE IF NOT EXISTS aa_chapters (
  chapter_id TEXT PRIMARY KEY,
  module_id TEXT NOT NULL REFERENCES aa_modules(module_id),
  chapter_no TEXT NOT NULL,
  name TEXT NOT NULL,
  short_name TEXT,
  display_order INTEGER NOT NULL,
  UNIQUE(module_id, chapter_no)
);

CREATE TABLE IF NOT EXISTS aa_units (
  unit_id TEXT PRIMARY KEY,
  chapter_id TEXT NOT NULL REFERENCES aa_chapters(chapter_id),
  unit_no TEXT,
  name TEXT NOT NULL,
  accounting_standard TEXT,
  teaching_sequence INTEGER,
  display_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS aa_topics (
  topic_id TEXT PRIMARY KEY,
  unit_id TEXT NOT NULL REFERENCES aa_units(unit_id),
  topic_no TEXT NOT NULL,
  name TEXT NOT NULL,
  short_name TEXT,
  page_number TEXT,
  display_order INTEGER NOT NULL,
  UNIQUE(unit_id, topic_no)
);

CREATE TABLE IF NOT EXISTS aa_sittings (
  sitting_id TEXT PRIMARY KEY,
  paper_type TEXT NOT NULL CHECK (paper_type IN ('PYQ', 'MTP', 'RTP')),
  attempt_month TEXT NOT NULL,
  attempt_month_no INTEGER NOT NULL,
  exam_year INTEGER NOT NULL,
  set_no INTEGER,
  label TEXT NOT NULL UNIQUE,
  expected_required_marks REAL,
  expected_offered_marks REAL
);

CREATE TABLE IF NOT EXISTS aa_questions (
  question_id TEXT PRIMARY KEY,
  sitting_id TEXT NOT NULL REFERENCES aa_sittings(sitting_id),
  question_no TEXT NOT NULL,
  sub_part TEXT,
  alternative_code TEXT,
  alternative_group TEXT,
  marks REAL,
  count_in_offered_total INTEGER NOT NULL DEFAULT 1 CHECK (count_in_offered_total IN (0, 1)),
  marks_issue TEXT,
  question_type TEXT,
  final_unit_id TEXT REFERENCES aa_units(unit_id),
  source_file TEXT NOT NULL,
  topic_mapping_review TEXT
);

CREATE TABLE IF NOT EXISTS aa_question_units (
  question_id TEXT NOT NULL REFERENCES aa_questions(question_id) ON DELETE CASCADE,
  unit_id TEXT NOT NULL REFERENCES aa_units(unit_id),
  is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
  PRIMARY KEY (question_id, unit_id)
);

CREATE TABLE IF NOT EXISTS aa_question_topics (
  question_id TEXT NOT NULL REFERENCES aa_questions(question_id) ON DELETE CASCADE,
  topic_id TEXT NOT NULL REFERENCES aa_topics(topic_id),
  is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
  mapping_status TEXT NOT NULL DEFAULT 'source-mapped',
  PRIMARY KEY (question_id, topic_id)
);

CREATE TABLE IF NOT EXISTS aa_study_items (
  study_item_id TEXT PRIMARY KEY,
  item_type TEXT NOT NULL,
  item_no TEXT,
  source_file TEXT NOT NULL,
  question_excerpt TEXT,
  scope_level TEXT NOT NULL DEFAULT 'unit' CHECK (scope_level IN ('topic', 'unit', 'chapter', 'multi-topic')),
  unit_id TEXT REFERENCES aa_units(unit_id),
  chapter_id TEXT REFERENCES aa_chapters(chapter_id),
  UNIQUE(source_file, item_type, item_no)
);

CREATE TABLE IF NOT EXISTS aa_study_item_topics (
  study_item_id TEXT NOT NULL REFERENCES aa_study_items(study_item_id) ON DELETE CASCADE,
  topic_id TEXT NOT NULL REFERENCES aa_topics(topic_id),
  mapping_status TEXT NOT NULL DEFAULT 'reviewed',
  PRIMARY KEY (study_item_id, topic_id)
);

CREATE TABLE IF NOT EXISTS aa_pyq_study_matches (
  question_id TEXT PRIMARY KEY REFERENCES aa_questions(question_id) ON DELETE CASCADE,
  study_item_id TEXT REFERENCES aa_study_items(study_item_id),
  match_status TEXT NOT NULL,
  similarity_percent REAL CHECK (similarity_percent IS NULL OR (similarity_percent >= 0 AND similarity_percent <= 100)),
  match_note TEXT,
  review_status TEXT NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS aa_import_runs (
  import_id TEXT PRIMARY KEY,
  source_topics_file TEXT NOT NULL,
  source_questions_file TEXT NOT NULL,
  source_matches_file TEXT,
  topics_count INTEGER NOT NULL,
  questions_count INTEGER NOT NULL,
  topic_links_count INTEGER NOT NULL,
  imported_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_aa_units_chapter ON aa_units(chapter_id);
CREATE INDEX IF NOT EXISTS idx_aa_topics_unit ON aa_topics(unit_id);
CREATE INDEX IF NOT EXISTS idx_aa_sittings_order ON aa_sittings(exam_year, attempt_month_no, paper_type, set_no);
CREATE INDEX IF NOT EXISTS idx_aa_questions_sitting ON aa_questions(sitting_id);
CREATE INDEX IF NOT EXISTS idx_aa_questions_unit ON aa_questions(final_unit_id);
CREATE INDEX IF NOT EXISTS idx_aa_qtopics_topic ON aa_question_topics(topic_id);
CREATE INDEX IF NOT EXISTS idx_aa_qunits_unit ON aa_question_units(unit_id);

CREATE VIEW IF NOT EXISTS aa_v_sitting_validation AS
SELECT
  s.sitting_id,
  s.label,
  s.paper_type,
  s.exam_year,
  s.attempt_month_no,
  s.set_no,
  s.expected_offered_marks,
  ROUND(SUM(CASE WHEN q.count_in_offered_total = 1 THEN COALESCE(q.marks, 0) ELSE 0 END), 2) AS imported_offered_marks,
  COUNT(q.question_id) AS question_rows,
  SUM(CASE WHEN q.marks IS NULL THEN 1 ELSE 0 END) AS missing_marks,
  SUM(CASE WHEN q.marks_issue IS NOT NULL AND q.marks_issue <> '' THEN 1 ELSE 0 END) AS marks_issues
FROM aa_sittings s
LEFT JOIN aa_questions q ON q.sitting_id = s.sitting_id
GROUP BY s.sitting_id;

CREATE VIEW IF NOT EXISTS aa_v_topic_exam_summary AS
SELECT
  t.topic_id,
  t.name AS topic_name,
  u.unit_id,
  u.name AS unit_name,
  c.chapter_id,
  c.name AS chapter_name,
  COUNT(DISTINCT qt.question_id) AS question_count,
  COUNT(DISTINCT q.sitting_id) AS sitting_count,
  ROUND(SUM(COALESCE(q.marks, 0)), 2) AS linked_marks
FROM aa_topics t
JOIN aa_units u ON u.unit_id = t.unit_id
JOIN aa_chapters c ON c.chapter_id = u.chapter_id
LEFT JOIN aa_question_topics qt ON qt.topic_id = t.topic_id
LEFT JOIN aa_questions q ON q.question_id = qt.question_id
GROUP BY t.topic_id;
