from pathlib import Path
root=Path.cwd()
html=(root/"ui/index.html").read_text(encoding="utf-8")
js=(root/"ui/app.js").read_text(encoding="utf-8")
css=(root/"ui/style.css").read_text(encoding="utf-8")
rust=(root/"src-tauri/src/main.rs").read_text(encoding="utf-8")
checks={
"X_RAY_WORKSPACE":"id=\"xrayWorkspace\"" in html,
"SUCCESS_LANE":"id=\"xraySuccessCount\"" in html,
"ERROR_LANE":"id=\"xrayErrorCount\"" in html,
"ANALYSIS_LANE":"id=\"xrayAnalysisCount\"" in html,
"VERA_CLIP":"id=\"xrayClipBtn\"" in html and "CLIP TO VERA" in html,
"READ_ONLY_XRAY":"fn xray_scan_project" in rust and "fs::write" not in rust[rust.index("fn xray_scan_project"):rust.index("fn main()")],
"X_RAY_COMMAND_REGISTERED":"xray_scan_project" in rust[rust.index("generate_handler!"):],
"MOCK_REFERENCE_ABSENT":"MOCK_REFERENCE" not in html and "mock" not in css.lower(),
}
for k,v in checks.items(): print(f"{k}={'PASS' if v else 'FAIL'}")
if not all(checks.values()): raise SystemExit(2)
print("VERTEX_WORKS_PROJECT_XRAY_040_UI_VERIFY PASS")
