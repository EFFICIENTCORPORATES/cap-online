PRAGMA foreign_keys = ON;

ALTER TABLE aa_topics ADD COLUMN overall_rank INTEGER;
ALTER TABLE aa_topics ADD COLUMN priority_band TEXT;

CREATE TABLE IF NOT EXISTS aa_documents (
  document_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  document_type TEXT NOT NULL CHECK (document_type IN ('study_material', 'question_paper', 'answer', 'examiner_comments')),
  r2_key TEXT NOT NULL UNIQUE,
  filename TEXT NOT NULL,
  byte_size INTEGER NOT NULL,
  content_type TEXT NOT NULL DEFAULT 'application/pdf',
  published INTEGER NOT NULL DEFAULT 1 CHECK (published IN (0, 1)),
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS aa_unit_documents (
  unit_id TEXT NOT NULL REFERENCES aa_units(unit_id) ON DELETE CASCADE,
  document_id TEXT NOT NULL REFERENCES aa_documents(document_id) ON DELETE CASCADE,
  PRIMARY KEY (unit_id, document_id)
);

CREATE TABLE IF NOT EXISTS aa_sitting_documents (
  sitting_id TEXT NOT NULL REFERENCES aa_sittings(sitting_id) ON DELETE CASCADE,
  document_id TEXT NOT NULL REFERENCES aa_documents(document_id) ON DELETE CASCADE,
  PRIMARY KEY (sitting_id, document_id)
);

CREATE INDEX IF NOT EXISTS idx_aa_topics_rank ON aa_topics(overall_rank);
CREATE INDEX IF NOT EXISTS idx_aa_topics_band ON aa_topics(priority_band);
CREATE INDEX IF NOT EXISTS idx_aa_unit_docs_unit ON aa_unit_documents(unit_id);
CREATE INDEX IF NOT EXISTS idx_aa_sitting_docs_sitting ON aa_sitting_documents(sitting_id);
