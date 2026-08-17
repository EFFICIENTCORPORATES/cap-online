@echo off
REM telegram/tools/ensure_bots_running.bat -- unattended entry point for
REM Windows Startup (shell:startup) and Task Scheduler (added 2026-08-15).
REM
REM Calls manage_bots.py's "ensure-running" action: starts any `active`
REM bot (bots.json) that isn't running at all, and RESTARTS any bot that
REM IS running but whose heartbeat has gone stale past
REM HEARTBEAT_STALE_AFTER_SECONDS (a hung process, not just a dead one) --
REM see manage_bots.py's own module docstring ("ENSURE-RUNNING") for the
REM full reasoning. Safe to run repeatedly and concurrently -- an already-
REM healthy bot is left completely untouched on every run, so this same
REM script is used BOTH at Windows logon (shell:startup, one-shot) AND by
REM a recurring Task Scheduler job (every 30 minutes, the "safer side"
REM self-healing check) -- one implementation, two triggers, never two
REM copies of the same logic to keep in sync.
REM
REM Uses the repo's own .venv interpreter EXPLICITLY (not "python" off
REM PATH) -- a Startup-folder or Task Scheduler process does not inherit
REM an interactive terminal's PATH/venv activation, so this must be
REM spelled out to reliably find psutil/python-telegram-bot/Flask/etc.
REM A short pause at the start gives Windows networking a moment to be
REM ready right after boot/logon (harmless overhead on the 30-min
REM recurring runs, where it's obviously already up). Uses the classic
REM ping-based delay, NOT timeout.exe -- timeout.exe hard-refuses to run
REM ("Input redirection is not supported") whenever it has no real
REM interactive console attached, which is exactly the case for BOTH a
REM Task Scheduler run and a Startup-folder run with output redirected to
REM a log file (confirmed by testing, not assumed) -- ping has no such
REM requirement and is the standard unattended-batch-script substitute.

set REPO_ROOT=D:\EffCorp_Projects\cap-online
set PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe
set LOG_FILE=%REPO_ROOT%\telegram\database\run\logs\ensure_bots_running.log

if not exist "%REPO_ROOT%\telegram\database\run\logs" mkdir "%REPO_ROOT%\telegram\database\run\logs"

echo ---- %date% %time% ---- >> "%LOG_FILE%"
ping 127.0.0.1 -n 21 >nul
"%PYTHON_EXE%" "%REPO_ROOT%\telegram\tools\manage_bots.py" ensure-running >> "%LOG_FILE%" 2>&1
echo ---- done ---- >> "%LOG_FILE%"
