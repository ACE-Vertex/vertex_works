from pathlib import Path
import re, sys
ROOT=Path(r"G:\Vertex_Project\Development\vertex_works")
main=(ROOT/"src-tauri/src/main.rs").read_text(encoding="utf-8",errors="replace")
cargo=(ROOT/"src-tauri/Cargo.toml").read_text(encoding="utf-8",errors="replace")
index=(ROOT/"ui/index.html").read_text(encoding="utf-8",errors="replace")
scoped_js=(ROOT/"ui/scoped-xray.js").read_text(encoding="utf-8",errors="replace")
scoped_css=(ROOT/"ui/scoped-xray.css").read_text(encoding="utf-8",errors="replace")
ui_all=index+"\n"+(ROOT/"ui/app.js").read_text(encoding="utf-8",errors="replace")

checks={
 "SCOPED_RUST_MARKER":"VERTEX_WORKS_SCOPED_XRAY_050_BEGIN" in main,
 "SCOPED_COMMAND":"fn xray_scope(" in main and "xray_scope," in main,
 "RESOLVE_COMMAND":"fn xray_resolve_scope(" in main and "xray_resolve_scope," in main,
 "READ_ONLY_CONTRACT":"mutation: false" in main and "Authority: READ ONLY" in main,
 "INDEX_JS":"scoped-xray.js" in index,
 "INDEX_CSS":"scoped-xray.css" in index,
 "RIGHT_CLICK":"contextmenu" in scoped_js,
 "WINDOW_CAPTURE":"window.addEventListener(\"contextmenu\",onExplorerContextMenu,true)" in scoped_js,
 "EXPLORER_GEOMETRY_FALLBACK":"findExplorerRoot" in scoped_js and "explorerHit" in scoped_js,
 "RIGHT_BUTTON_FALLBACK":"pointerup" in scoped_js and "e.button!==2" in scoped_js,
 "VERA_CLIP":"CLIP TO VERA" in scoped_js and "navigator.clipboard.writeText" in scoped_js,
 "FORGE_PRESERVED":"forge" in ui_all.lower(),
 "PROJECT_XRAY_PRESERVED":"x-ray" in ui_all.lower() or "xray" in ui_all.lower(),
 "V050":bool(re.search(r'(?m)^version\s*=\s*"0\.5\.0"\s*$',cargo)),
 "CSS_PRESENT":bool(scoped_css.strip()),
}
bad=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(f"{k}={'PASS' if v else 'FAIL'}")
if bad:
    raise SystemExit("VERTEX_WORKS_SCOPED_XRAY_050_VERIFY FAIL: "+", ".join(bad))
print("VERTEX_WORKS_SCOPED_XRAY_050_VERIFY PASS")
