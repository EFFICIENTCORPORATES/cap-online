"""
apply_store_config.py — copy RAZORPAY_KEY_ID from .env into assets/store-config.js.

Run from capranav-website/ (or anywhere; paths are resolved relative to this
script's own location, matching the other tools/ scripts in this folder):

    python tools/apply_store_config.py

Only the public Key ID moves into store-config.js — that value is safe to
ship to the browser. RAZORPAY_KEY_SECRET is read from .env for validation
only (so a pasted-in-the-wrong-place mistake is caught) and is never written
anywhere else.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
CONFIG_FILE = ROOT / "assets" / "store-config.js"


def parse_env(path: Path) -> dict:
    values = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def main() -> int:
    if not ENV_FILE.exists():
        print(f"No .env found at {ENV_FILE}.")
        print("Copy .env.example to .env first, then paste your Razorpay Key ID into it.")
        return 1

    env = parse_env(ENV_FILE)
    key_id = env.get("RAZORPAY_KEY_ID", "")
    key_secret = env.get("RAZORPAY_KEY_SECRET", "")

    if not key_id:
        print("RAZORPAY_KEY_ID is empty in .env — nothing to apply.")
        print("Paste your Key ID (starts rzp_live_ or rzp_test_) into .env and re-run.")
        return 1

    if key_id.startswith("rzp_") is False:
        print(f"Warning: '{key_id}' doesn't look like a Razorpay Key ID (expected it to start with 'rzp_'). Continuing anyway.")

    if key_secret and key_secret.startswith("rzp_"):
        print("Warning: RAZORPAY_KEY_SECRET looks like it might actually be a Key ID.")
        print("Double check you haven't pasted the same value into both fields — the")
        print("Key Secret is the OTHER value shown next to the Key ID in the Razorpay")
        print("Dashboard, and this script never writes it anywhere.")

    if not CONFIG_FILE.exists():
        print(f"Expected to find {CONFIG_FILE} but it's missing.")
        return 1

    text = CONFIG_FILE.read_text(encoding="utf-8")
    new_text, count = re.subn(
        r'window\.RAZORPAY_KEY_ID = ".*?";',
        f'window.RAZORPAY_KEY_ID = "{key_id}";',
        text,
        count=1,
    )
    if count == 0:
        print(f"Could not find the window.RAZORPAY_KEY_ID line in {CONFIG_FILE}. File format changed?")
        return 1

    CONFIG_FILE.write_text(new_text, encoding="utf-8")
    print(f"Applied Key ID to {CONFIG_FILE.relative_to(ROOT)}.")
    print("Remember: this file is safe to commit (Key ID is public), but .env never is.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
