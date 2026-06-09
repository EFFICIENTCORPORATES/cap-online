#!/usr/bin/env python3
"""gsheet_sync.py - sync the content calendar between local Markdown and a Google Sheet.

Two-way bridge so the editing team can collaborate in a shared Google Sheet while the
repo keeps a versioned Markdown copy of the calendar.

    pull :  Google Sheet           -> content/calendar/*.md
    push :  content/calendar/*.md   -> Google Sheet

STATUS: STUB / TODO. Planned implementation uses `gspread` + a Google service-account
credential (keep the JSON key OUT of git). Each calendar maps to one worksheet/tab:
    personal-private.md  <-> tab "personal"
    vc-gurukul-shared.md <-> tab "vc-gurukul"

Usage (planned):
    python content/scripts/gsheet_sync.py pull
    python content/scripts/gsheet_sync.py push
"""
import argparse
import sys

CALENDARS = {
    "personal": "content/calendar/personal-private.md",
    "vc-gurukul": "content/calendar/vc-gurukul-shared.md",
}


def pull():
    raise NotImplementedError("TODO: read Google Sheet tabs -> write calendar .md tables")


def push():
    raise NotImplementedError("TODO: parse calendar .md tables -> write Google Sheet tabs")


def main():
    ap = argparse.ArgumentParser(description="Sync content calendar with Google Sheets.")
    ap.add_argument("direction", choices=["pull", "push"])
    args = ap.parse_args()
    print("gsheet_sync is a stub. Configure gspread + service account first.")
    (pull if args.direction == "pull" else push)()


if __name__ == "__main__":
    sys.exit(main())
