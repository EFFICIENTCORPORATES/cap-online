@echo off
cd /d "%~dp0"
python ca_gui.py
if errorlevel 1 (
  echo.
  echo Python could not start. Install Python 3.10+ with Tkinter support.
)
