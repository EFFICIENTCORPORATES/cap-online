@echo off
setlocal

:: ============================================================================
:: 1LAVYA Telegram Bots -- Restart/Start Launcher  (added 2026-08-12)
:: ------------------------------------------------------------------------
:: Double-click this file anytime, from anywhere, to bring every `active`
:: bot in telegram\config\bots.json up to date in one shot:
::   - already running  -> gracefully stopped, then started fresh
::   - not running      -> started fresh
:: Safe to run repeatedly / at every Windows login (see below) -- it never
:: errors just because a bot happens to already be down or already be up.
::
:: This is a thin wrapper around telegram\tools\manage_bots.py's own
:: `restart` action -- ALL the actual process logic (graceful CTRL_BREAK
:: stop with a bounded force-terminate fallback, PID tracking, per-bot
:: logs) lives there and is already tested; this .bat does not duplicate
:: any of it. See that script's own docstring for exactly what "graceful"
:: means here.
::
:: TO RUN AUTOMATICALLY AT WINDOWS LOGIN:
::   Copy (or shortcut) this file into your Startup folder:
::     %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
::   (Win+R -> shell:startup opens that folder directly.) Anything placed
::   there runs automatically, unattended, every time you log in -- which
::   means every login will briefly restart your live bots. That's exactly
::   what was asked for here (auto-recover after a reboot/crash without
::   having to remember to start anything by hand), just flagging it plainly
::   since it's a real behavior change once copied there, not only when
::   double-clicked by hand.
::
:: IF THIS REPO EVER MOVES to a different path or drive: this file lives
:: OUTSIDE the repo once copied into your Startup folder, so it can't
:: locate the repo relative to itself the way every script inside
:: telegram/ does (see FIRST_PROMPT.md's portability notes) -- it has to
:: know the repo's absolute path some other way. Update the ONE line below
:: (REPO_ROOT) and re-copy this file to Startup again.
:: ============================================================================

set "REPO_ROOT=D:\EffCorp_Projects\cap-online"
set "MANAGE_BOTS=%REPO_ROOT%\telegram\tools\manage_bots.py"
set "VENV_PY=%REPO_ROOT%\.venv\Scripts\python.exe"

title 1LAVYA Bots -- Restart / Start

echo ============================================================
echo  1LAVYA Telegram Bots -- Restart / Start
echo  %DATE% %TIME%
echo ============================================================
echo.

if not exist "%MANAGE_BOTS%" (
    echo [ERROR] manage_bots.py not found at:
    echo   %MANAGE_BOTS%
    echo.
    echo This usually means REPO_ROOT at the top of this .bat is out of
    echo date -- edit it to point at your current clone of cap-online,
    echo then re-copy this file to your Startup folder if you use one.
    echo.
    ping -n 21 127.0.0.1 >nul
    endlocal
    exit /b 1
)

if exist "%VENV_PY%" (
    set "PYEXE=%VENV_PY%"
) else (
    echo [WARN] Repo .venv not found at %VENV_PY% -- falling back to the
    echo        "python" on PATH. If bot dependencies aren't installed
    echo        there, this will fail below.
    echo.
    set "PYEXE=python"
)

echo Using Python: %PYEXE%
echo.
echo --- Restarting every active bot (graceful stop if running, then start) ---
"%PYEXE%" "%MANAGE_BOTS%" restart
set "RESTART_RC=%ERRORLEVEL%"
if not "%RESTART_RC%"=="0" (
    echo.
    echo [ERROR] manage_bots.py restart exited with code %RESTART_RC% -- see the output above.
)

echo.
echo --- Current status ---
"%PYEXE%" "%MANAGE_BOTS%" status

echo.
echo ============================================================
echo  Done. Per-bot logs: %REPO_ROOT%\telegram\database\run\logs\
echo  This window closes automatically in 20 seconds.
echo ============================================================
:: ping-based sleep instead of `timeout`/`pause` -- both of those can error
:: out ("Input redirection is not supported") when this .bat is launched
:: unattended at login rather than from an interactive double-click, which
:: would leave it looking like a crash. This works either way.
ping -n 21 127.0.0.1 >nul

endlocal
exit /b 0
