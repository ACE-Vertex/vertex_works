from pathlib import Path
root=Path(r"G:\Vertex_Project\Development\vertex_works")
js=(root/"ui/scoped-xray.js").read_text(encoding="utf-8",errors="replace")
checks={
 "POINTER_FIRST":"candidateLabelsFromPoint" in js and "document.elementsFromPoint" in js,
 "DIRECT_TEXT":"function ownText" in js,
 "NO_PANEL_PATH_TRUST":"Never trust an Explorer-carried absolute path" in js,
 "BASENAME_MATCH":"winBaseName(resolved).toLowerCase()===c.label.toLowerCase()" in js,
 "ROOT_LAST":"Prefer every more-specific candidate ahead of it" in js,
 "COORDINATES_FROZEN":"const clickX=e.clientX" in js and "const clickY=e.clientY" in js,
 "RIGHT_CLICK_PRESERVED":"onExplorerContextMenu" in js and "contextmenu" in js,
 "VERA_HANDOFF_PRESERVED":"CLIP TO VERA" in js,
}
bad=[k for k,v in checks.items() if not v]
for k,v in checks.items():
    print(f"{k}={'PASS' if v else 'FAIL'}")
if bad:
    raise SystemExit("VERTEX_WORKS_SCOPED_SCOPE_057_VERIFY FAIL: "+", ".join(bad))
print("VERTEX_WORKS_SCOPED_SCOPE_057_VERIFY PASS")
