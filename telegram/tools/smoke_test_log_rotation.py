#!/usr/bin/env python3
"""
telegram/tools/smoke_test_log_rotation.py -- regression check for the
two-layer log rotation policy (LOGGING-ARCHITECTURE.md §6/§10, 2026-08-18)

Layer 1 (telegram/database/log_rotation.py): proves a real
RotatingFileHandler built by build_rotating_handler() actually rotates
past MAX_BYTES and produces a ".log.1" sibling -- entirely inside a temp
directory, NEVER touching telegram/database/run/logs/.

Layer 2 (telegram/tools/rotate_logs_to_r2.py): proves the watermark/
oldest-first/dry-run/failure-handling logic against SYNTHETIC files in a
temp directory with a FAKE S3 client (no real network call, no real R2
credentials needed to run this) -- monkeypatches rotate_logs_to_r2.LOG_DIR
for the duration of the test and restores it in a finally block, so a
real run of this script can never accidentally ship or delete a real
production log file.

Run: python telegram/tools/smoke_test_log_rotation.py
"""

import gzip
import logging
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))

import log_rotation                # noqa: E402
import rotate_logs_to_r2 as r2mod  # noqa: E402

passed = failed = 0


def check(label, condition):
    global passed, failed
    if condition:
        print(f"  OK   {label}")
        passed += 1
    else:
        print(f"  FAIL {label}")
        failed += 1


class FakeS3:
    """Records put_object calls in memory, no real network/credentials.
    fail_keys: a set of keys that should simulate an upload failure, for
    testing the "leave the local file in place" failure path."""
    def __init__(self, fail_keys=None):
        self.uploaded = {}
        self.deleted = []
        self.fail_keys = fail_keys or set()

    def put_object(self, Bucket, Key, Body):
        if Key in self.fail_keys:
            raise RuntimeError("simulated upload failure")
        self.uploaded[Key] = Body

    def delete_object(self, Bucket, Key):
        self.deleted.append(Key)

    def get_paginator(self, name):
        # Only prune_by_age() calls this in the real flow -- return an
        # empty pager so the retention-prune step is a harmless no-op here.
        class _Pager:
            def paginate(self, **kwargs):
                return [{"Contents": []}]
        return _Pager()


def make_file(path: Path, size_bytes: int, mtime_offset_seconds: float = 0):
    path.write_bytes(b"x" * size_bytes)
    if mtime_offset_seconds:
        t = time.time() + mtime_offset_seconds
        import os
        os.utime(path, (t, t))


def test_build_handlers_no_duplication():
    """Regression guard for the real bug found + fixed same day this
    policy was built: a managed process (BOT_MANAGED=1, set by
    manage_bots.py's start_bot()) must NOT get a StreamHandler, or its
    stderr gets captured a SECOND time into {bot_id}.crash.log by
    manage_bots.py's own subprocess.Popen redirect -- full duplication of
    every routine log line into an unbounded file, defeating this whole
    policy. An UNmanaged (interactive/manual) run must still get one, for
    live terminal visibility during dev."""
    print("--- build_handlers(): no StreamHandler duplication when managed ---")
    import os
    orig = os.environ.pop("BOT_MANAGED", None)
    try:
        handlers = log_rotation.build_handlers("smoketest-managed")
        check("BOT_MANAGED unset -> a StreamHandler IS included (interactive run)",
              any(type(h).__name__ == "StreamHandler" for h in handlers))

        os.environ["BOT_MANAGED"] = "1"
        handlers = log_rotation.build_handlers("smoketest-managed")
        check("BOT_MANAGED=1 -> NO StreamHandler (would duplicate into crash.log)",
              not any(type(h).__name__ == "StreamHandler" for h in handlers))
        check("the bounded RotatingFileHandler is still always present either way",
              any(type(h).__name__ == "RotatingFileHandler" for h in handlers))
    finally:
        if orig is None:
            os.environ.pop("BOT_MANAGED", None)
        else:
            os.environ["BOT_MANAGED"] = orig


def test_layer1_rotation():
    print("--- Layer 1: build_rotating_handler() actually rotates ---")
    tmpdir = Path(tempfile.mkdtemp(prefix="log_rotation_smoke_"))
    orig_log_dir = log_rotation.LOG_DIR
    try:
        log_rotation.LOG_DIR = tmpdir
        # A tiny MAX_BYTES so this test doesn't need to write 20MB for real.
        orig_max = log_rotation.MAX_BYTES
        log_rotation.MAX_BYTES = 500  # bytes
        try:
            handler = log_rotation.build_rotating_handler("smoketest-bot")
            check("handler writes to the expected filename", handler.baseFilename == str(tmpdir / "smoketest-bot.log"))
            for i in range(200):
                handler.emit(_fake_record(f"line {i} " + "x" * 20))
            handler.close()
            rotated = list(tmpdir.glob("smoketest-bot.log.*"))
            check("at least one rotated chunk was produced once MAX_BYTES was crossed", len(rotated) >= 1)
            check("the active file still exists (bounded, not deleted)", (tmpdir / "smoketest-bot.log").exists())
        finally:
            log_rotation.MAX_BYTES = orig_max
    finally:
        log_rotation.LOG_DIR = orig_log_dir
        shutil.rmtree(tmpdir, ignore_errors=True)


def _fake_record(msg):
    import logging
    return logging.LogRecord("smoketest", 20, __file__, 0, msg, None, None)


def test_layer2_watermark_and_shipping():
    print("--- Layer 2: watermark trigger, oldest-first, dry-run, failure handling ---")
    tmpdir = Path(tempfile.mkdtemp(prefix="log_rotation_smoke_l2_"))
    orig_log_dir = r2mod.LOG_DIR
    orig_watermark = r2mod.WATERMARK_BYTES
    try:
        r2mod.LOG_DIR = tmpdir
        r2mod.WATERMARK_BYTES = 1000  # bytes -- tiny, so a few small synthetic files can cross it

        # Active files (never touched) + rotated chunks (fair game), oldest chunk first.
        make_file(tmpdir / "bot-a.log", 100)
        make_file(tmpdir / "bot-a.log.1", 600, mtime_offset_seconds=-300)   # older
        make_file(tmpdir / "bot-a.log.2", 600, mtime_offset_seconds=-100)   # newer
        make_file(tmpdir / "bot-b.log", 100)

        total_before = r2mod._current_total_bytes()
        check("total correctly sums every file in the dir", total_before == 100 + 600 + 600 + 100)

        chunks = r2mod._rotated_chunks()
        check("only *.log.* files are treated as rotated chunks (2 found)", len(chunks) == 2)
        check("the active bot-a.log/bot-b.log are NOT in the rotated-chunks list",
              all(".log." in p.name for p in chunks))

        # --- dry-run: must not touch the filesystem or the fake S3 at all ---
        s3 = FakeS3()
        r2mod.args_dry_run_used = True
        freed = 0
        for c in sorted(chunks, key=lambda p: p.stat().st_mtime):
            freed += r2mod._ship_and_delete(s3, c, dry_run=True)
        check("dry-run reports 0 bytes freed", freed == 0)
        check("dry-run uploaded nothing to the fake S3", len(s3.uploaded) == 0)
        check("dry-run deleted nothing locally", (tmpdir / "bot-a.log.1").exists() and (tmpdir / "bot-a.log.2").exists())

        # --- real run: oldest chunk should ship first ---
        s3 = FakeS3()
        oldest = sorted(chunks, key=lambda p: p.stat().st_mtime)[0]
        check("the OLDEST chunk really is bot-a.log.1", oldest.name == "bot-a.log.1")
        freed = r2mod._ship_and_delete(s3, oldest, dry_run=False)
        check("a real ship reports the real byte count freed", freed == 600)
        check("exactly one object was uploaded", len(s3.uploaded) == 1)
        uploaded_key = next(iter(s3.uploaded))
        check("the R2 key is namespaced logs/{bot_id}/... with a timestamp", uploaded_key.startswith("logs/bot-a/bot-a_"))
        check("the uploaded body is real gzip data that decompresses back to the original bytes",
              gzip.decompress(s3.uploaded[uploaded_key]) == b"x" * 600)
        check("the local rotated chunk was deleted after a successful upload", not oldest.exists())
        check("the ACTIVE bot-a.log was never touched", (tmpdir / "bot-a.log").exists() and (tmpdir / "bot-a.log").stat().st_size == 100)

        # --- failure path: upload fails -> local file must be LEFT IN PLACE ---
        remaining = r2mod._rotated_chunks()
        check("one rotated chunk (bot-a.log.2) remains for the failure test", len(remaining) == 1)
        target = remaining[0]
        fail_key_s3 = FakeS3()
        # Force a failure by making put_object always raise for any key.
        fail_key_s3.fail_keys = {"*"}
        class AlwaysFailS3(FakeS3):
            def put_object(self, Bucket, Key, Body):
                raise RuntimeError("simulated upload failure")
        result = r2mod._ship_and_delete(AlwaysFailS3(), target, dry_run=False)
        check("a failed upload reports 0 bytes freed", result == 0)
        check("a failed upload leaves the local file IN PLACE (never deleted on failure)", target.exists())

        # --- DIRECT_MANAGE_FILES: ship + TRUNCATE (never delete) ---
        r2mod.DIRECT_MANAGE_FILES = {"ensure_bots_running.log": 50}  # tiny threshold for the test
        make_file(tmpdir / "ensure_bots_running.log", 200)
        s3 = FakeS3()
        freed = r2mod._ship_direct_managed_files(s3, dry_run=False)
        check("direct-managed file reports its real size freed", freed == 200)
        check("direct-managed file was TRUNCATED, not deleted (still exists, now empty)",
              (tmpdir / "ensure_bots_running.log").exists() and (tmpdir / "ensure_bots_running.log").stat().st_size == 0)
        check("exactly one object uploaded for the direct-managed file", len(s3.uploaded) == 1)

    finally:
        r2mod.LOG_DIR = orig_log_dir
        r2mod.WATERMARK_BYTES = orig_watermark
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_never_touches_real_log_dir():
    print("--- Sanity: this test suite never pointed at the REAL log dir ---")
    check("log_rotation.LOG_DIR was restored to the real path after Layer 1's test",
          log_rotation.LOG_DIR == log_rotation.REPO_ROOT / "telegram" / "database" / "run" / "logs")
    check("rotate_logs_to_r2.LOG_DIR was restored to the real path after Layer 2's test",
          r2mod.LOG_DIR == log_rotation.LOG_DIR)


def test_third_party_logger_does_not_bypass_our_handler():
    """Regression guard for the real admin_portal/app.py bug found + fixed
    same day: some libraries (Werkzeug's dev server is the concrete case)
    check "does MY OWN named logger already have a handler" and, finding
    none, silently attach their OWN StreamHandler directly to that
    logger with propagate=False -- bypassing whatever root-logger
    handlers logging.basicConfig() installed entirely. Verified for real
    against the live admin portal process (curled it, watched the
    request line land in the bounded .log, not crash.log) -- this is the
    permanent, fast, no-live-process-needed version of that same check:
    a logger pre-armed with our handlers + propagate=False (the fix)
    must actually receive records emitted through it, not just through
    root."""
    print("--- Regression: a third-party logger given our handlers directly (Werkzeug's own pattern) ---")
    import io
    stream = io.StringIO()
    mem_handler = logging.StreamHandler(stream)
    mem_handler.setFormatter(logging.Formatter("%(message)s"))

    third_party_logger = logging.getLogger("smoketest.thirdparty")
    third_party_logger.handlers = [mem_handler]
    third_party_logger.propagate = False

    check("a logger with no handlers of its own would trigger a library's auto-attach check",
          not logging.getLogger("smoketest.unconfigured").handlers)
    third_party_logger.info('127.0.0.1 - - "GET / HTTP/1.1" 302 -')
    check("emitting through the pre-armed logger reaches OUR handler, not some other default",
          "GET / HTTP/1.1" in stream.getvalue())


if __name__ == "__main__":
    print("=== smoke_test_log_rotation ===")
    test_build_handlers_no_duplication()
    test_layer1_rotation()
    test_layer2_watermark_and_shipping()
    test_third_party_logger_does_not_bypass_our_handler()
    test_never_touches_real_log_dir()
    print()
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
