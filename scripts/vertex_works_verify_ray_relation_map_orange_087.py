from pathlib import Path
import json

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
UI = ROOT / "ui"
INDEX = UI / "index.html"
JS = UI / "vertex-works-ray-contract.js"
CSS = UI / "vertex-works-ray-orange.css"
CURRENT = ROOT / "current.json"
ENTRY = ROOT / "VertexWorks.exe"

def emit(name, ok):
    print(f"{name}={'PASS' if ok else 'FAIL'}")
    return ok

index = INDEX.read_text(encoding="utf-8", errors="replace") if INDEX.exists() else ""
js = JS.read_text(encoding="utf-8", errors="replace") if JS.exists() else ""
css = CSS.read_text(encoding="utf-8", errors="replace") if CSS.exists() else ""
cur = json.loads(CURRENT.read_text(encoding="utf-8")) if CURRENT.exists() else {}
ray = cur.get("ray_contract") or {}
release_value = cur.get("release_exe") or cur.get("executable") or ""
release = Path(release_value) if release_value else Path("__missing__")

checks = [
    emit("ROOT_ENTRY_EXISTS", ENTRY.exists()),
    emit("RAY_JS_EXISTS", JS.exists()),
    emit("RAY_CSS_EXISTS", CSS.exists()),
    emit("RAY_JS_LINKED", "vertex-works-ray-contract.js" in index),
    emit("RAY_CSS_LINKED", "vertex-works-ray-orange.css" in index),
    emit("RELATION_ADD_PRESENT", 'id="blueprintAddRelationBtn"' in index),
    emit("RELATION_SAVE_PRESENT", 'id="relationSaveBtn"' in index),
    emit("RELATION_DELETE_PRESENT", 'id="relationDeleteBtn"' in index),
    emit("RELATION_MAP_PRESENT", 'id="xrayMap"' in index),
    emit("NO_LAYOUT_EDITOR_CLAIM", 'blueprintEditor: "DISABLED_BY_CAPABILITY_GATE"' in js),
    emit("GRID_FALSE", "grid: false" in js),
    emit("SNAP_FALSE", "snap: false" in js),
    emit("DRAG_FALSE", "drag: false" in js),
    emit("LINK_TEST_PRESENT", "async function testLinkMode()" in js),
    emit("SAVE_OBSERVER_PRESENT", 'state.saveDispatch = "OBSERVED"' in js),
    emit("DELETE_OBSERVER_PRESENT", 'state.deleteDispatch = "OBSERVED"' in js),
    emit("ORANGE_RAY_SCOPE", "#xrayWorkspace" in css and "#ff8a2a" in css),
    emit("SCOPED_RAY_ORANGE", ".vx-sx-menu" in css and "--vx-forge-cyan: #ff8a2a" in css),
    emit("SEMANTIC_DANGER_UNTOUCHED", ".xray-button.danger" not in css),
    emit("CURRENT_RAY_VERSION", ray.get("version") == "000087"),
    emit("CURRENT_ROLE_RELATION_MAP", ray.get("blueprint_role") == "RELATION_MAP"),
    emit("CURRENT_LAYOUT_EDITOR_FALSE", ray.get("layout_editor") is False),
    emit("CURRENT_RELATION_PRESERVED", ray.get("relation_controls_preserved") is True),
    emit("CURRENT_FORGE_UNMUTATED", ray.get("forge_mutated") is False),
    emit("CURRENT_RELEASE_EXISTS", release.exists()),
    emit("IMMUTABLE_RELEASE", "\\versions\\0.5.0\\builds\\" in str(release).lower()),
]

if not all(checks):
    raise SystemExit("VERTEX_WORKS_RAY_RELATION_MAP_ORANGE_087_VERIFY FAIL")

print("RAY_THEME=VW_ORANGE_CHROME")
print("BLUEPRINT_ROLE=RELATION_MAP")
print("LAYOUT_EDITOR=OFF")
print("RELATION_RUNTIME_DIAGNOSTIC=ACTIVE")
print("FORGE_MUTATION=FALSE")
print("VERTEX_WORKS_RAY_RELATION_MAP_ORANGE_087_VERIFY PASS")
