@echo off
chcp 65001 >nul
title [칼퇴보증] 성적서 분석 에이전트 (※ 이 창을 닫지 마시고 최소화하세요)

echo ======================================================================
echo   [칼퇴보증] 성적서 분석 에이전트 원클릭 실행기
echo   ※ 주의: 이 검은색 창을 닫으면 프로그램(웹화면)도 즉시 종료됩니다!
echo            사용 중에는 끄지 마시고 최소화(_)해 두세요.
echo ======================================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [알림] 본 컴퓨터에 Python(파이썬)이 설치되어 있지 않거나 환경변수에 등록되지 않았습니다.
    echo.
    echo 해결 방법:
    echo 1. https://www.python.org/downloads/ 에서 Python(3.10~3.12 권장)을 다운로드하여 설치하세요.
    echo 2. 설치 창 맨 아래 [Add python.exe to PATH] 체크박스를 반드시 체크해주세요!
    echo 3. 설치 완료 후 본 배치파일을 다시 더블클릭하시면 모든 라이브러리가 자동 설치되고 실행됩니다.
    echo.
    pause
    exit /b
)

echo [안내] 파이썬 환경 감지 완료. 필수 패키지 자동 점검 및 프로그램 실행 중...
echo (최초 1회 실행 시 라이브러리 자동 설치로 약 10~20초 소요될 수 있습니다)
echo.

python "%~dp0run.py"

if %errorlevel% neq 0 (
    echo.
    echo [종료] 프로그램이 종료되었습니다.
    pause
)
