from pathlib import Path
import json

ROOT=Path(r"G:\Vertex_Project\Development\vertex_works")
MAIN=ROOT/"src-tauri"/"src"/"main.rs"
CURRENT=ROOT/"current.json"
NEW=Path(r"G:\Vertex_Project\Development\_incoming")

NEW_LITERAL=r'const DEFAULT_INBOX: &str = r"G:\Vertex_Project\Development\_incoming";'
OLD_LITERAL=r'const DEFAULT_INBOX: &str = r"G:\Vertex_Project\_incoming\vertex_works";'

text=MAIN.read_text(encoding="utf-8", errors="replace")
data=json.loads(CURRENT.read_text(encoding="utf-8"))

checks={
    "NEW_INBOX_EXISTS": NEW.is_dir(),
    "NEW_LITERAL": NEW_LITERAL in text,
    "OLD_LITERAL_REMOVED": OLD_LITERAL not in text,
    "CURRENT_RECEIVING_BAY": data.get("receiving_bay")==str(NEW),
    "SOURCE_ROOT_JUDGE": data.get("source_root_judge")=="PASS_EXACT_CONTRACT",
    "BUILD_CACHE_RESET": data.get("build_cache_reset")=="PASS",
    "IMMUTABLE_RELEASE": Path(data.get("release_exe","")).exists(),
}
for k,v in checks.items():
    print(f"{k}={'PASS' if v else 'FAIL'}")
bad=[k for k,v in checks.items() if not v]
if bad:
    raise SystemExit("VERTEX_WORKS_RECEIVING_BAY_071_VERIFY FAIL: "+", ".join(bad))

print("VERTEX_WORKS_RECEIVING_BAY_071_VERIFY PASS")
print("RESTART_NEW_VERIFIED_EXE=YES")
print("NEW_RECEIVING_BAY=", NEW)
print("RELEASE_EXE=", data.get("release_exe"))
