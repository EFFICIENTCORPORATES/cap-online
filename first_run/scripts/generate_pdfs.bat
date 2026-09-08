@echo off
setlocal EnableExtensions
title CA Pranav - VC Gurukul Test Paper PDF Generator

rem ============================================================
rem generate_pdfs.bat
rem
rem Installs the required Python packages and converts the
rem student chapter-test Markdown files into watermarked PDFs.
rem
rem Safe to run by double-clicking from ANY location, or from
rem any folder in a command prompt - every path below is worked
rem out from this .bat file's own folder (%~dp0), never from
rem whatever folder you happened to launch it from.
rem ============================================================

set "SCRIPT_DIR=%~dp0"
set "REPO_VENV_PY=%SCRIPT_DIR%..\..\.venv\Scripts\python.exe"
set "PYTHON_EXE="
set "PYTHON_ARG="

echo.
echo === Locating Python ===

if exist "%REPO_VENV_PY%" (
    set "PYTHON_EXE=%REPO_VENV_PY%"
    echo Using this repo's own virtual environment.
    goto :found_python
)

where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_EXE=py"
    set "PYTHON_ARG=-3"
    echo Using the Python launcher ^(py -3^).
    goto :found_python
)

where python >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_EXE=python"
    echo Using system Python.
    goto :found_python
)

echo.
echo ERROR: No Python installation was found on this computer.
echo Install Python 3.9 or later from https://www.python.org/downloads/
echo During setup, tick "Add python.exe to PATH" - then run this file again.
echo.
pause
exit /b 1

:found_python
echo Python: %PYTHON_EXE% %PYTHON_ARG%
echo.

echo === Installing required packages (this may take a minute the first time) ===
"%PYTHON_EXE%" %PYTHON_ARG% -m pip install -r "%SCRIPT_DIR%requirements.txt" --quiet
if errorlevel 1 (
    echo.
    echo ERROR: Could not install the required packages.
    echo Check your internet connection and try again.
    echo.
    pause
    exit /b 1
)

echo.
echo === Generating watermarked PDFs ===
"%PYTHON_EXE%" %PYTHON_ARG% "%SCRIPT_DIR%convert_tests_to_pdf.py"
if errorlevel 1 (
    echo.
    echo ERROR: PDF generation failed - see the messages above for details.
    echo.
    pause
    exit /b 1
)

echo.
echo === All done! ===
echo Your PDFs are ready in:
echo   %SCRIPT_DIR%..\TESTS\second phase\student-edition\pdf
echo.
pause
