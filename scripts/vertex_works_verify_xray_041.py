from pathlib import Path
root=Path.cwd()
html=(root/'ui/index.html').read_text(encoding='utf-8')
js=(root/'ui/app.js').read_text(encoding='utf-8')
css=(root/'ui/style.css').read_text(encoding='utf-8')
rust=(root/'src-tauri/src/main.rs').read_text(encoding='utf-8')
scan=rust[rust.index('fn xray_scan_project'):rust.index('fn main()')]
checks={
 'X_RAY_WORKSPACE':'id="xrayWorkspace"' in html,
 'FULL_FOLDER_SCHEMA':'struct XrayFolder' in rust and 'folders: Vec<XrayFolder>' in rust,
 'RECURSIVE_SCAN':'fn xray_scan_dir' in rust,
 'NESTED_MANIFESTS_NOT_SKIPPED':'if xray_manifest_kind(&p).is_some() { continue; }' not in rust,
 'VISIBLE_IGNORED_BOUNDARIES':'IGNORED_GENERATED' in rust,
 'LARGE_SCAN_BUDGET':'500_000usize' in rust,
 'TREE_EXPLORER':'xrayFolderChildren' in js and 'xrayBuildFolderRow' in js,
 'FOLDER_METRIC':'<span>FOLDERS</span>' in html,
 'VERA_CLIP':'id="xrayClipBtn"' in html and 'CLIP TO VERA' in html,
 'SUCCESS_ERROR_ANALYSIS':all(x in html for x in ['xraySuccessCount','xrayErrorCount','xrayAnalysisCount']),
 'READ_ONLY_XRAY':'fs::write' not in scan,
 'MOCK_REFERENCE_ABSENT':'MOCK_REFERENCE' not in html and 'mock' not in css.lower(),
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): raise SystemExit(2)
print('VERTEX_WORKS_PROJECT_XRAY_041_FULL_TREE_VERIFY PASS')
