@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo [COA-Guard] 자동화 테스트 스위트 실행 중...
python run_tests.py
pause
