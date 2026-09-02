from pathlib import Path
import hashlib, json

ROOT=Path(r"G:\Vertex_Project\Development\vertex_works")
CURRENT=ROOT/"current.json"
ENTRY=ROOT/"VertexWorks.exe"
APP_ICON=ROOT/"ui"/"assets"/"brand"/"vertex-works-app-icon.png"
WORDMARK=ROOT/"ui"/"assets"/"brand"/"vertex-works-wordmark.png"
ICON_ICO=ROOT/"src-tauri"/"icons"/"icon.ico"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

data=json.loads(CURRENT.read_text(encoding="utf-8"))
release=Path(data.get("release_exe",""))
brand=data.get("brand",{})
single=data.get("single_entry",{})

checks={
 "ROOT_ENTRY_EXISTS": ENTRY.is_file(),
 "NEW_RELEASE_EXISTS": release.is_file(),
 "APP_ICON_EXISTS": APP_ICON.is_file(),
 "WORDMARK_EXISTS": WORDMARK.is_file(),
 "TAURI_ICON_EXISTS": ICON_ICO.is_file(),
 "PRODUCT_CODE_VW": brand.get("product_code")=="VW",
 "THEME_ORANGE_CONTRACT": brand.get("theme")=="ORANGE",
 "BRAND_PHASE": brand.get("phase")=="BRAND_FOUNDATION",
 "SINGLE_ENTRY_MODE": single.get("mode")=="FIXED_LAUNCHER_CURRENT_POINTER",
 "LAUNCHER_HASH_MATCH": ENTRY.is_file() and single.get("launcher_sha256")==sha(ENTRY),
}
for k,v in checks.items():
    print(f"{k}={'PASS' if v else 'FAIL'}")
bad=[k for k,v in checks.items() if not v]
if bad:
    raise SystemExit("VERTEX_WORKS_BRAND_FOUNDATION_074_VERIFY FAIL: "+", ".join(bad))

print("VISIBLE_ENTRY=", ENTRY)
print("ACTIVE_RELEASE=", release)
print("BRAND_FOUNDATION=PASS")
print("NEXT_PHASE=UI ORANGE THEME + ENGLISH-ONLY SOURCE REMOVAL")
print("VERTEX_WORKS_BRAND_FOUNDATION_074_VERIFY PASS")
