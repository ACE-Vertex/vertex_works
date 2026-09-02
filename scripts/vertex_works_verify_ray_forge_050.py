from pathlib import Path
root=Path.cwd()
html=(root/'ui/index.html').read_text(encoding='utf-8')
js=(root/'ui/app.js').read_text(encoding='utf-8')
css=(root/'ui/style.css').read_text(encoding='utf-8')
rust=(root/'src-tauri/src/main.rs').read_text(encoding='utf-8')
checks={
 'PERSISTENT_RAY_FORGE_SWITCH': all(x in html for x in ['vertexModeBar','rayNavBtn','forgeNavBtn']),
 'RAY_WORKSPACE': 'id="xrayWorkspace"' in html and 'VERTEX RAY' in html,
 'FORGE_WORKSPACE': 'id="forgeWorkspace"' in html and 'id="applyBtn"' in html and 'FORGE' in html,
 'VERTEX_COLOR_UNIFIED': all(x in css for x in ['--vertex-accent','vertex-mode-bar','var(--vertex-bg-panel)']),
 'FME_LINEAGE_BLUEPRINT': 'FME LINEAGE / PROJECT BLUEPRINT' in html and 'bp-port' in js and 'bp-edge-mid' in js,
 'RELATION_TYPES': all(x in html for x in ['DEPENDENCY','RUNTIME','CORRELATION','SUPERIORITY','LINEAGE']),
 'RELATION_INSPECTOR': all(x in html for x in ['relationStrength','relationConfidence','relationCorrelation','relationSuperiority','relationDependency']),
 'MANUAL_RELATION_LINK': 'startBlueprintLink' in js and 'manual:${Date.now()}' in js,
 'BLUEPRINT_LOCAL_ONLY': 'VERTEX_BP_STORE' in js and 'Project Source remains untouched' in js,
 'DEFAULT_JAPANESE': '<html lang="ja"' in html and '||"ja"' in js,
 'LANGUAGE_GEAR': all(x in html for x in ['settingsBtn','langJaBtn','langEnBtn']),
 'VERA_CLIP': 'id="xrayClipBtn"' in html and 'CLIP TO VERA' in html,
 'SUCCESS_ERROR_ANALYSIS': all(x in html for x in ['xraySuccessCount','xrayErrorCount','xrayAnalysisCount']),
 'RECURSIVE_XRAY_PRESERVED': 'fn xray_scan_dir' in rust and '500_000usize' in rust,
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): raise SystemExit(2)
print('VERTEX_WORKS_RAY_FORGE_BLUEPRINT_050_UI_VERIFY PASS')
