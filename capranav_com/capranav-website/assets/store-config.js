/*
  Public Razorpay Key ID only. This value is SAFE to expose in client-side
  code — Razorpay's Key ID is designed to be public (unlike the Key Secret,
  which must never appear in any file the browser can read, and isn't used
  by this site yet — see .env.example).

  To activate live checkout:
    1. Copy .env.example to .env (in this same capranav-website/ folder) and
       paste your real Razorpay Key ID into RAZORPAY_KEY_ID.
    2. Run, from this folder:  python tools/apply_store_config.py
       It copies the Key ID from .env into this file. .env itself is
       gitignored and never committed; this file only ever holds the public
       Key ID, so it's fine to commit once populated.
    3. Upload the updated capranav-website/ folder to Cloudflare Pages.

  Until step 1–2 is done, every Buy button shows a "payment isn't switched
  on yet" message instead of failing silently.
*/
window.RAZORPAY_KEY_ID = "RAZORPAY_KEY_ID_NOT_SET";
