import zipfile
import py_compile
import os

zname = r"2026_AX공모전_칼퇴보증_최종제출패키지.zip"
with zipfile.ZipFile(zname, "r") as zf:
    code = zf.read("03.개발 및 데이터/src/core/audit_manager.py").decode("utf-8")
code = code.replace("\r\n", "\n")

# 모듈 레벨 함수 sync_to_google_sheet 및 sync_all_to_google_sheet 추가
top_sync_functions = '''def sync_to_google_sheet(record: dict, webhook_url: str = None) -> (bool, str):
    """단일 검사 기록을 구글 스프레드시트에 전송 (모듈 레벨 래퍼)"""
    mgr = AuditManager()
    return mgr.sync_to_google_sheet(record, webhook_url)

def sync_all_to_google_sheet(history: list = None, webhook_url: str = None) -> dict:
    """누적된 전체 이력을 구글 시트에 일괄 동기화 (모듈 레벨 래퍼)"""
    mgr = AuditManager()
    if not webhook_url:
        cfg = get_sheet_config()
        webhook_url = cfg.get("webhook_url", "")
    
    if not webhook_url:
        return {"status": "error", "message": "구글 웹훅 URL이 설정되지 않았습니다.", "count": 0}
    
    target_list = history if history is not None else mgr.load_all()
    if not target_list:
        return {"status": "warning", "message": "동기화할 검사 이력이 없습니다.", "count": 0}
        
    cnt = 0
    for item in reversed(target_list):
        ok, _ = mgr.sync_to_google_sheet(item, webhook_url)
        if ok:
            cnt += 1
    return {"status": "success", "count": cnt, "message": f"{cnt}건 동기화 성공"}
'''

code = code.replace("def save_sheet_config(webhook_url: str, sheet_url: str = \"\") -> bool:", top_sync_functions + "\ndef save_sheet_config(webhook_url: str, sheet_url: str = \"\") -> bool:")

# AuditManager 클래스 내부에 fetch_sheet_data_via_csv 메소드 추가
fetch_csv_method = '''
    def fetch_sheet_data_via_csv(self) -> List[Dict[str, Any]]:
        """구글 스프레드시트 발행(pub) CSV 엔드포인트에서 라이브 데이터 추출"""
        cfg = get_sheet_config()
        sheet_url = cfg.get("sheet_url", "")
        if not sheet_url:
            return []
            
        csv_url = sheet_url
        if "pubhtml" in sheet_url:
            csv_url = sheet_url.replace("pubhtml", "pub?output=csv")
        elif "docs.google.com/spreadsheets/d/" in sheet_url and "/edit" in sheet_url:
            doc_id = sheet_url.split("/d/")[1].split("/")[0]
            csv_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv"
            
        try:
            import urllib.request
            import csv
            import io
            req = urllib.request.Request(csv_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    raw_text = resp.read().decode("utf-8")
                    reader = csv.DictReader(io.StringIO(raw_text))
                    return list(reader)
        except Exception as e:
            print(f"Error fetching sheet data via CSV: {e}")
            
        return []
'''

code = code + "\n" + fetch_csv_method

target = r"03.개발 및 데이터/src/core/audit_manager.py"
with open(target, "w", encoding="utf-8") as f:
    f.write(code)
    f.flush()
    os.fsync(f.fileno())

print(f"Written complete audit_manager.py! Length: {len(code)}, FileSize: {os.path.getsize(target)}")
py_compile.compile(target, doraise=True)
print("COMPILATION_PASSED_SUCCESSFULLY")
