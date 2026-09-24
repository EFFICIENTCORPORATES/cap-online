-- Per-IP OTP rate limiting (security hardening, 2026-09-24).
-- Apply BEFORE deploying the Worker that writes/reads this column:
--   npx wrangler d1 execute capranav-platform --remote --file=migrations/0003_otp_ip_rate_limit.sql
ALTER TABLE otp_codes ADD COLUMN ip TEXT;
CREATE INDEX IF NOT EXISTS idx_otp_ip ON otp_codes(ip);
