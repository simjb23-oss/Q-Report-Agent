@echo off
setlocal
cd /d "%~dp0"
title COA-Guard QA Agent Launcher

echo ======================================================================
echo   [COA-Guard] Quality Certificate QA Agent System Launcher
echo   * Info: Please do not close this console window while running.
echo ======================================================================
echo.

set PYTHON_CMD=

:: 1. Search portable python
if exist "%~dp0python_env\Scripts\python.exe" (
    set PYTHON_CMD="%~dp0python_env\Scripts\python.exe"
    goto PYTHON_FOUND
)
if exist "%~dp0python_env\python.exe" (
    set PYTHON_CMD="%~dp0python_env\python.exe"
    goto PYTHON_FOUND
)

:: 2. Search python / py in PATH
where python >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto PYTHON_FOUND
)
where py >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    goto PYTHON_FOUND
)

:: 3. Search default User AppData Python installation
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto PYTHON_FOUND
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto PYTHON_FOUND
)
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    goto PYTHON_FOUND
)

:: 4. Search Program Files Python installation
if exist "%ProgramFiles%\Python312\python.exe" (
    set PYTHON_CMD="%ProgramFiles%\Python312\python.exe"
    goto PYTHON_FOUND
)
if exist "%ProgramFiles%\Python311\python.exe" (
    set PYTHON_CMD="%ProgramFiles%\Python311\python.exe"
    goto PYTHON_FOUND
)
if exist "%ProgramFiles%\Python310\python.exe" (
    set PYTHON_CMD="%ProgramFiles%\Python310\python.exe"
    goto PYTHON_FOUND
)

:PYTHON_NOT_FOUND
echo [ERROR] Python environment not detected on this PC.
echo.
echo ----------------------------------------------------------------------
echo [Quick Solution Guide]
echo 1. Open official download page: https://www.python.org/downloads/
echo 2. Run the installer and check '[v] Add python.exe to PATH'.
echo 3. After installation, double-click this file again to start.
echo ----------------------------------------------------------------------
echo.
echo Press any key to exit...
pause >nul
exit /b 1

:PYTHON_FOUND
echo [1/3] Python Engine detected: %PYTHON_CMD%
echo [2/3] Checking dependencies and preparing dashboard...
echo.

set PYTHONIOENCODING=utf-8
%PYTHON_CMD% "%~dp0run.py"

if %errorlevel% neq 0 (
    echo.
    echo ======================================================================
    echo [EXIT] Program stopped with error code: %errorlevel%
    echo ======================================================================
    echo.
    echo Press any key to exit...
    pause >nul
) else (
    echo.
    echo [OK] Program closed safely.
    pause >nul
)
