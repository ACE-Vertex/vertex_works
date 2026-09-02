from pathlib import Path
root=Path(r"G:\Vertex_Project\Development\vertex_works")
js=(root/"ui/scoped-xray.js").read_text(encoding="utf-8",errors="replace")
checks={
 "ROW_FIRST_RESOLVER":"findExplorerRow" in js and "rowLabelAndHints" in js,
 "ROW_ONLY_DIRECT_PATH":"pathFromRow" in js,
 "ROOT_CAPTURE_GUARD":'developmentRoot="g:\\\\vertex_project\\\\development"' in js,
 "OLD_ANCESTOR_PATH_SCAN_REMOVED":"function pathFromChain" not in js,
 "SCOPED_COMMAND_PRESERVED":'invoke("xray_resolve_scope"' in js,
 "RIGHT_CLICK_PRESERVED":"onExplorerContextMenu" in js and "contextmenu" in js,
 "VERA_HANDOFF_PRESERVED":"CLIP TO VERA" in js,
}
bad=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(f"{k}={'PASS' if v else 'FAIL'}")
if bad:
    raise SystemExit("VERTEX_WORKS_SCOPED_SCOPE_055_VERIFY FAIL: "+", ".join(bad))
print("VERTEX_WORKS_SCOPED_SCOPE_055_VERIFY PASS")
