from pathlib import Path
root=Path(r"G:\Vertex_Project\Development\vertex_works")
app=(root/"ui/app.js").read_text(encoding="utf-8",errors="replace")
sx=(root/"ui/scoped-xray.js").read_text(encoding="utf-8",errors="replace")
checks={
 "EXACT_RENDERER":"function xrayBuildFolderRow" in app,
 "EXACT_ROW_MARKER":"VERTEX_WORKS_EXPLORER_EXACT_ROW_BINDING_063" in app,
 "EXACT_PATH_BINDING":"row.dataset.xrayPath = f.path;" in app,
 "EXACT_ID_BINDING":"row.dataset.xrayId = f.id;" in app,
 "EXACT_RELATIVE_BINDING":"row.dataset.xrayRelativePath = f.relative_path;" in app,
 "SCOPED_AUTHORITATIVE_ONLY":"resolveAuthoritativeScope" in sx,
 "NO_LABEL_INFERENCE":"candidateLabelsFromPoint" not in sx,
 "NO_BACKEND_LABEL_RESOLVE":'invoke("xray_resolve_scope"' not in sx,
 "FAIL_CLOSED":"Development-root fallback is forbidden" in sx,
}
bad=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(f"{k}={'PASS' if v else 'FAIL'}")
if bad:
    raise SystemExit("VERTEX_WORKS_EXPLORER_EXACT_ROW_063_VERIFY FAIL: "+", ".join(bad))
print("VERTEX_WORKS_EXPLORER_EXACT_ROW_063_VERIFY PASS")
