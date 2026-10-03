# -*- coding: utf-8 -*-
"""
COA-Guard QA Agent Standalone Launcher
Cross-platform, portable, automatic port allocation, dependency resolution & auto browser startup.
"""

import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "utf-8"
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

REQUIRED_PACKAGES = [
    ("streamlit", "streamlit"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("plotly", "plotly"),
    ("pypdf", "pypdf"),
    ("pymupdf", "pymupdf"),
    ("openpyxl", "openpyxl"),
    ("PIL", "Pillow"),
    ("dotenv", "python-dotenv"),
    ("requests", "requests")
]

print("=" * 68)
print("  [COA-Guard QA Agent] Auto Inspection System Initializing...")
print("=" * 68)

missing_pkgs = []
for import_name, pip_name in REQUIRED_PACKAGES:
    try:
        __import__(import_name)
    except ImportError:
        missing_pkgs.append(pip_name)

if missing_pkgs:
    print(f"  [Auto-Installer] Missing packages detected: {', '.join(missing_pkgs)}")
    print("  Installing dependencies via pip (approx. 15~40s)...")
    print("-" * 68)
    try:
        res = subprocess.run([
            sys.executable, "-m", "pip", "install", "--prefer-binary", *missing_pkgs
        ])
        if res.returncode == 0:
            print("  [Success] All packages installed successfully!")
        else:
            print("  [Warning] Some packages returned warnings, proceeding anyway.")
    except Exception as e:
        print(f"  [Notice] Exception during auto-install: {e}")

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

def find_available_port(start_port=8501, max_attempts=20):
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port

port = find_available_port(8501)

base_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(base_dir, "src", "app", "main.py")):
    app_dir = base_dir
elif os.path.exists(os.path.join(base_dir, "03.개발 및 데이터", "src", "app", "main.py")):
    app_dir = os.path.join(base_dir, "03.개발 및 데이터")
else:
    app_dir = base_dir

app_main = os.path.join(app_dir, "src", "app", "main.py")

if not os.path.exists(app_main):
    print(f"\n[Fatal Error] Cannot locate main.py: {app_main}")
    input("\nPress Enter to exit...")
    sys.exit(1)

target_url = f"http://localhost:{port}"

print("-" * 68)
print("  [Dashboard Ready]")
print(f"  * Entrypoint  : {app_main}")
print(f"  * Web URL     : {target_url}")
print("  * Notice      : Web browser is opening automatically.")
print("                  Please do NOT close this console window.")
print("=" * 68)

def open_browser_delayed(url):
    time.sleep(2.5)
    try:
        webbrowser.open(url)
    except Exception:
        pass

threading.Thread(target=open_browser_delayed, args=(target_url,), daemon=True).start()

cmd = [
    sys.executable, "-m", "streamlit", "run", "src/app/main.py",
    "--server.address", "0.0.0.0",
    "--server.port", str(port),
    "--server.headless", "false",
    "--browser.gatherUsageStats", "false"
]

try:
    proc = subprocess.run(cmd, cwd=app_dir)
    sys.exit(proc.returncode)
except KeyboardInterrupt:
    print("\nApplication closed safely.")
    sys.exit(0)