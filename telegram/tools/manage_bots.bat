@echo off
REM telegram/tools/manage_bots.bat -- thin wrapper for manage_bots.py.
REM Usage: manage_bots.bat start|stop|restart|status [bot_id]
python "%~dp0manage_bots.py" %*
