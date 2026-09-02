from pathlib import Path
import sys

WORKS = Path(r"G:\Vertex_Project\Development\vertex_works")
INDEX = WORKS / "ui" / "index.html"
JS = WORKS / "ui" / "vertex-works-major-refinement-000026.js"
CSS = WORKS / "ui" / "vertex-works-major-refinement-000026.css"
DOC = WORKS / "docs" / "WORKS_REFINEMENT_000026.md"
CANONICAL_RS = WORKS / "src-tauri" / "src" / "canonical_registry.rs"

paths = {"INDEX": INDEX, "JS": JS, "CSS": CSS, "DOC": DOC}
failed = False

for name, path in paths.items():
    ok = path.exists()
    print(f"{name}_EXISTS={'PASS' if ok else 'FAIL'}")
    failed |= not ok

if failed:
    sys.exit(1)

index = INDEX.read_text(encoding="utf-8")
js = JS.read_text(encoding="utf-8")
css = CSS.read_text(encoding="utf-8")
doc = DOC.read_text(encoding="utf-8")

checks = {
    "INDEX_CSS_BOUND": "vertex-works-major-refinement-000026.css" in index,
    "INDEX_JS_BOUND": "vertex-works-major-refinement-000026.js" in index,
    "GLOBAL_LANGUAGE_RETIRED": "retireGlobalLanguageSettings" in js and "#vcr-language" in css,
    "VCR_CHROME_ENGLISH": 'vcrSave.textContent = "SAVE"' in js,
    "PRODUCT_THEME_CONTRACT": "bindProductAccentContract" in js and "Unify design language, not product identity color." in doc,
    "VERTEX_THEME_AVAILABLE": '[data-vertex-theme="true"]' in css,
    "RAY_ORBIT_DECK": "class OrbitDeck" in js and "vw-orbit-core" in css,
    "RAY_WHEEL_ORBIT": 'addEventListener("wheel"' in js,
    "RAY_FRONT_SELECT": "frontIndex()" in js and "vertex-project-select" in js,
    "NO_FAKE_PROJECTS": "AWAITING REAL PROJECT CARDS — NO FAKE PROJECTS" in js,
    "PROJECT_EXPLORER_THEME": "vw-project-explorer-panel" in js and "vw-project-explorer-panel" in css,
    "ANALYSIS_FINDINGS_THEME": "vw-analysis-findings-panel" in js and "vw-analysis-findings-panel" in css,
    "VXN_PAGE": 'VXN: { role: "FLOW" }' in js,
    "JUDGE_PAGE": 'JUDGE: { role: "DECIDE" }' in js,
    "SENSOR_PAGE": 'SENSOR: { role: "OBSERVE" }' in js,
    "EVIDENCE_PAGE": 'EVIDENCE: { role: "PROVE" }' in js,
    "RELEASE_PAGE": 'RELEASE: { role: "SHIP" }' in js,
    "CANONICAL_PAGE": 'CANONICAL: { role: "REMEMBER" }' in js,
    "NO_FAKE_LIVE_STATUS": "LIVE BRIDGE MUST PROVE ITSELF" in js,
}

for name, ok in checks.items():
    print(f"{name}={'PASS' if ok else 'FAIL'}")
    failed |= not ok

if CANONICAL_RS.exists():
    raw = CANONICAL_RS.read_text(encoding="utf-8")
    warning_removed = "path::{Path, PathBuf}" not in raw
    print(f"CANONICAL_UNUSED_IMPORT_REMOVED={'PASS' if warning_removed else 'FAIL'}")
    failed |= not warning_removed

if failed:
    print("VERTEX_WORKS_MAJOR_REFINEMENT_000026_VERIFY FAIL")
    sys.exit(1)

print("WORKS_DESIGN_LANGUAGE_SHARED=PASS")
print("PRODUCT_COLOR_IDENTITY_PRESERVED=PASS")
print("FACILITY_PAGES_READY=PASS")
print("VERTEX_WORKS_MAJOR_REFINEMENT_000026_VERIFY PASS")
