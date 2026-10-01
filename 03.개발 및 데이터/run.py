import os
import subprocess
import sys

# 1. 필수 핵심 패키지 자동 설치/검사 (심사위원 및 다른 PC 무인 자동 실행 보장)
REQUIRED_PACKAGES = [
    ("streamlit", "streamlit"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("plotly", "plotly"),
    ("pypdf", "pypdf"),
    ("fitz", "pymupdf"),
    ("openpyxl", "openpyxl"),
    ("dotenv", "python-dotenv"),
    ("google.genai", "google-genai"),
    ("google.generativeai", "google-generativeai")
]

missing_pkgs = []
for import_name, pip_name in REQUIRED_PACKAGES:
    try:
        __import__(import_name)
    except ImportError:
        missing_pkgs.append(pip_name)

if missing_pkgs:
    print("=" * 65)
    print(f"  [환경 감지] 필수 라이브러리 자동 설치 중: {', '.join(missing_pkgs)}")
    print("  (최초 1회만 약 10~20초 소요됩니다. 잠시만 기다려주세요...)")
    print("=" * 65)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_pkgs])
        print("  [완료] 모든 패키지가 정상 설치되었습니다!")
    except Exception as e:
        print(f"  [경고] 자동 설치 실패: {e}")

# 2. Streamlit 초기 온보딩 질문 무인 패스 설정
try:
    home = os.path.expanduser('~')
    st_dir = os.path.join(home, '.streamlit')
    os.makedirs(st_dir, exist_ok=True)
    cred_file = os.path.join(st_dir, 'credentials.toml')
    if not os.path.exists(cred_file):
        with open(cred_file, 'w', encoding='utf-8') as f:
            f.write('[general]\nemail = ""\n')
except Exception:
    pass

# 3. 앱 실행
base_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(base_dir, "src", "app", "main.py")):
    app_dir = base_dir
elif os.path.exists(os.path.join(base_dir, "03.개발 및 데이터", "src", "app", "main.py")):
    app_dir = os.path.join(base_dir, "03.개발 및 데이터")
else:
    app_dir = base_dir
app_main = os.path.join(app_dir, "src", "app", "main.py")

print("=" * 65)
print("  [칼퇴보증] 성적서 분석 에이전트 가동 중...")
print("  [안내] 이 검은색 콘솔 창이 프로그램 엔진입니다.")
print("         사용 중 창을 닫지 마시고 최소화(_)해 두세요!")
print(f"  앱 경로: {app_main}")
print("  브라우저 주소: http://localhost:8501")
print("=" * 65)

cmd = [
    sys.executable, "-m", "streamlit", "run", "src/app/main.py",
    "--server.address", "0.0.0.0",
    "--server.port", "8501",
    "--server.headless", "false",
    "--browser.gatherUsageStats", "false"
]
subprocess.run(cmd, cwd=app_dir)
