from pathlib import Path
import json

ROOT=Path(r"G:\Vertex_Project\Development\vertex_works")
MAIN=ROOT/"src-tauri"/"src"/"main.rs"
CURRENT=ROOT/"current.json"
NEW=Path(r"G:\Vertex_Project\Development\_incoming")
OLD=Path(r"G:\Vertex_Project\_incoming\vertex_works")

NEW_LITERAL=r'const DEFAULT_INBOX: &str = r"G:\Vertex_Project\Development\_incoming";'
OLD_LITERAL=r'const DEFAULT_INBOX: &str = r"G:\Vertex_Project\_incoming\vertex_works";'

main=MAIN.read_text(encoding="utf-8",errors="replace")
data=json.loads(CURRENT.read_text(encoding="utf-8"))

checks={
 "SOURCE_ROOT_EXISTS": ROOT.is_dir(),
 "NEW_INBOX_EXISTS": NEW.is_dir(),
 "NEW_LITERAL": NEW_LITERAL in main,
 "OLD_LITERAL_REMOVED": OLD_LITERAL not in main,
 "SCAN_INBOX_USES_DEFAULT": "fs::read_dir(DEFAULT_INBOX)" in main,
 "RECEIVER_INFO_EXPOSES_DEFAULT": '"inbox": DEFAULT_INBOX' in main,
 "CURRENT_PRODUCT": data.get("product")=="VERTEX WORKS",
 "CURRENT_RECEIVING_BAY": data.get("receiving_bay")==str(NEW),
 "SOURCE_ROOT_JUDGE": data.get("source_root_judge")=="PASS_EXACT_CONTRACT",
 "IMMUTABLE_RELEASE": Path(data.get("release_exe","")).exists(),
}
bad=[k for k,v in checks.items() if not v]
for k,v in checks.items():
    print(f"{k}={'PASS' if v else 'FAIL'}")
if bad:
    raise SystemExit("VERTEX_WORKS_RECEIVING_BAY_070_VERIFY FAIL: "+", ".join(bad))
print("VERTEX_WORKS_RECEIVING_BAY_070_VERIFY PASS")
