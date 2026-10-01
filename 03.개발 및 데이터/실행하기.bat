@echo off
title COA-Guard Launcher
cd /d "%~dp0"
python -m streamlit run src/app/main.py
pause
