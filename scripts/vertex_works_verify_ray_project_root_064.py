from pathlib import Path

ROOT=Path(r"G:\Vertex_Project\Development\vertex_works")
app=(ROOT/"ui/app.js").read_text(encoding="utf-8",errors="replace")
sx=(ROOT/"ui/scoped-xray.js").read_text(encoding="utf-8",errors="replace")

checks={
 "EXPLORER_RENDERER":"function xrayBuildFolderRow" in app,
 "PROJECT_ROOT_BINDING_MARKER":"VERTEX_WORKS_RAY_PROJECT_ROOT_BINDING_064" in app,
 "RELATIVE_PATH_SOURCE":"String(f.relative_path" in app,
 "TOP_SEGMENT_ONLY":'vxRel.split("/")' in app,
 "PROJECT_ROOT_DATASET":"row.dataset.xrayProjectRoot" in app,
 "PROJECT_NAME_DATASET":"row.dataset.xrayProjectName" in app,
 "SCOPED_RESET_MARKER":"VERTEX_WORKS_RAY_PROJECT_ROOT_SCOPE_RESET_064" in sx,
 "PROJECT_ROOT_RESOLVER":"resolveProjectRootScope" in sx,
 "AUTHORITATIVE_ROW_SELECTOR":"[data-xray-project-root]" in sx,
 "NO_POINTER_TEXT_INFERENCE":"candidateLabelsFromPoint" not in sx,
 "NO_SCOPE_LABEL_BACKEND":'invoke("xray_resolve_scope"' not in sx,
 "NO_SELECTION_HEURISTIC":'aria-selected="true"' not in sx,
 "WHOLE_ROOT_FORBIDDEN":"Whole-Development fallback is forbidden" in sx,
 "GLOBAL_PROJECT_XRAY_PRESERVED":"PROJECT X-RAY" in sx or "Project X-Ray" in sx or "xray_scope" in sx,
 "VERA_HANDOFF_PRESERVED":"CLIP TO VERA" in sx,
}
bad=[k for k,v in checks.items() if not v]
for k,v in checks.items():
    print(f"{k}={'PASS' if v else 'FAIL'}")
if bad:
    raise SystemExit("VERTEX_WORKS_RAY_PROJECT_ROOT_065_VERIFY FAIL: "+", ".join(bad))
print("VERTEX_WORKS_RAY_PROJECT_ROOT_065_VERIFY PASS")
