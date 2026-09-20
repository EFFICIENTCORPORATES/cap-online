@echo off
cd /d "%~dp0"
python ca_retriever.py --interactive
if errorlevel 1 (
  echo.
  echo Python could not start. Install Python 3.10+ and ensure "python" is in PATH.
)
pause
