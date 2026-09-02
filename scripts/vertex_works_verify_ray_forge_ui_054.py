from pathlib import Path
css=Path(r"G:\Vertex_Project\Development\vertex_works\ui\scoped-xray.css")
js=Path(r"G:\Vertex_Project\Development\vertex_works\ui\scoped-xray.js")
if not css.exists(): raise SystemExit("scoped-xray.css missing")
if not js.exists(): raise SystemExit("scoped-xray.js missing")
c=css.read_text(encoding="utf-8",errors="replace")
j=js.read_text(encoding="utf-8",errors="replace")
checks={
 "FORGE_UNIFIED_MARKER":"FORGE UNIFIED DARK UI / 000054" in c,
 "FORGE_VOID":"--vx-forge-void:#010305" in c,
 "LOW_LUMINANCE_REPORT":"#010407" in c and "rgba(0,2,4,.84)" in c,
 "SCOPED_MENU":".vx-sx-menu" in c,
 "SCOPED_REPORT":"#vxSxReport" in c,
 "FORGE_DENSITY":"border-radius:3px" in c and "box-shadow:none" in c,
 "CYAN_AS_SIGNAL":"--vx-forge-cyan:#38bde8" in c,
 "GLOBAL_RAY_NORMALIZATION":'[data-workspace="xray"]' in c,
 "RIGHT_CLICK_PRESERVED":"onExplorerContextMenu" in j and "contextmenu" in j,
 "VERA_HANDOFF_PRESERVED":"CLIP TO VERA" in j,
}
bad=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(f"{k}={'PASS' if v else 'FAIL'}")
if bad: raise SystemExit("VERTEX_WORKS_RAY_FORGE_UI_054_VERIFY FAIL: "+", ".join(bad))
print("VERTEX_WORKS_RAY_FORGE_UI_054_VERIFY PASS")
