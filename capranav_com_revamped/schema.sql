-- capranav.com (revamped) — D1 schema
-- Run once: wrangler d1 execute capranav-platform --remote --file=schema.sql

CREATE TABLE IF NOT EXISTS otp_codes (
  email      TEXT NOT NULL,
  code       TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  consumed   INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_otp_email ON otp_codes(email);

CREATE TABLE IF NOT EXISTS sessions (
  token      TEXT PRIMARY KEY,
  user_email TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sessions_email ON sessions(user_email);

-- One row per checkout attempt. Amount is always looked up server-side from
-- the product catalogue in worker code — never trusted from the client.
CREATE TABLE IF NOT EXISTS orders (
  id                   TEXT PRIMARY KEY,
  razorpay_order_id    TEXT UNIQUE NOT NULL,
  razorpay_payment_id  TEXT,
  product_id           TEXT NOT NULL,
  product_type         TEXT NOT NULL, -- course | book_physical | book_pdf
  amount_rupees        INTEGER NOT NULL,
  buyer_name           TEXT,
  buyer_email          TEXT,
  buyer_phone          TEXT,
  shipping_json        TEXT,          -- only for product_type = book_physical
  status                TEXT NOT NULL DEFAULT 'pending', -- pending | paid | failed
  created_at           TEXT NOT NULL DEFAULT (datetime('now')),
  paid_at              TEXT
);

-- A student's persistent profile — independent of any one order, so it's
-- there before/after any purchase, viewable/editable from the dashboard.
-- Falls back to the most recent order's buyer_name/buyer_phone when no row
-- exists yet (handled in worker code, not here).
CREATE TABLE IF NOT EXISTS student_profiles (
  email      TEXT PRIMARY KEY,
  name       TEXT,
  phone      TEXT,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Who can open the locked-down reader for which PDF product.
CREATE TABLE IF NOT EXISTS entitlements (
  user_email TEXT NOT NULL,
  product_id TEXT NOT NULL,
  order_id   TEXT,
  granted_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (user_email, product_id)
);

-- Dedupes Razorpay webhook deliveries. Razorpay can legitimately send the
-- same event more than once; the primary key on event_id (from the
-- X-Razorpay-Event-Id header) is what makes re-processing a no-op.
CREATE TABLE IF NOT EXISTS webhook_events (
  event_id   TEXT PRIMARY KEY,
  event_type TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS contact_messages (
  id         TEXT PRIMARY KEY,
  name       TEXT,
  email      TEXT,
  message    TEXT,
  ip         TEXT,  -- CF-Connecting-IP at submission time; used for rate-limiting only
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_contact_ip ON contact_messages(ip);
