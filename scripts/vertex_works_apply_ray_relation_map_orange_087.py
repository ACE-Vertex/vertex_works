from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
UI = ROOT / "ui"
INDEX = UI / "index.html"
APP = UI / "app.js"
SCOPED_JS = UI / "scoped-xray.js"
SCOPED_CSS = UI / "scoped-xray.css"
ORANGE = UI / "vertex-works-orange.css"
RAY_JS = UI / "vertex-works-ray-contract.js"
RAY_CSS = UI / "vertex-works-ray-orange.css"
CURRENT = ROOT / "current.json"
CARGO = ROOT / "src-tauri" / "Cargo.toml"
BUILT_EXE = ROOT / "src-tauri" / "target" / "release" / "vertex-receiver.exe"
VERSION = "0.5.0"

EXPECTED = {
    INDEX: "0bd1f69754457ec03e442042182add585185c3901d5155d84b149d0c516ad10e",
    APP: "42f13606d7071ce5593e8bbf8c0c0bf3016bdde70b8fa21e437457aa2c233f51",
    SCOPED_JS: "0fe43e67323268f79b0d1b84b5616b11cd5e2f0863fec1dd9d113632bcd6d40f",
    SCOPED_CSS: "d2988185bda74f20e4a5cb242722be916366dd0ee935c83c15d80adbb23315db",
    ORANGE: "d5c29aba9c14ba7c061e38fb7baa0c74c293af7ef9209d46503a89104abc448b",
}

def emit(value=""):
    text = str(value)
    sys.stdout.write(text.encode("ascii", "backslashreplace").decode("ascii") + "\n")

def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def write_lf(path: Path, text: str):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def run(args):
    emit("RUN " + " ".join(map(str, args)))
    cp = subprocess.run(args, text=True, capture_output=True)
    if cp.stdout:
        emit(cp.stdout)
    if cp.stderr:
        emit(cp.stderr)
    if cp.returncode != 0:
        raise RuntimeError("COMMAND_FAILED " + " ".join(map(str, args)))

for path in list(EXPECTED) + [RAY_JS, RAY_CSS, CURRENT, CARGO]:
    if not path.exists():
        raise SystemExit("REQUIRED_MISSING " + str(path))

emit("VERTEX WORKS RAY RELATION MAP / ORANGE CONTRACT 000087")
emit("MODE=MUTATION")
emit("FORGE_SOURCE_MUTATION=FALSE")
emit("BLUEPRINT_EDITOR=DISABLED_BY_CAPABILITY_GATE")
emit("RELATION_ENGINE=PRESERVE_AND_OBSERVE")
emit("RAY_THEME=VW_ORANGE_CHROME")

for path, expected in EXPECTED.items():
    actual = sha256(path)
    ok = actual == expected
    emit(f"SOURCE_HASH_{path.name}={'PASS' if ok else 'FAIL'}")
    if not ok:
        raise RuntimeError(f"STALE_SOURCE {path} expected={expected} actual={actual}")

index = INDEX.read_text(encoding="utf-8")
required_ids = [
    'id="xrayWorkspace"',
    'id="xrayMap"',
    'id="blueprintAddRelationBtn"',
    'id="blueprintCancelLinkBtn"',
    'id="relationEditor"',
    'id="relationFrom"',
    'id="relationTo"',
    'id="relationSaveBtn"',
    'id="relationDeleteBtn"',
]
for marker in required_ids:
    if marker not in index:
        raise RuntimeError("UI_CONTRACT_MISSING " + marker)

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = ROOT / "MIGRATION_BACKUPS" / "RAY_RELATION_MAP_ORANGE_087" / stamp
backup.mkdir(parents=True, exist_ok=True)
shutil.copy2(INDEX, backup / "index.html")
shutil.copy2(CURRENT, backup / "current.json")

css_link = '<link rel="stylesheet" href="vertex-works-ray-orange.css" />'
js_link = '<script src="vertex-works-ray-contract.js"></script>'

try:
    if css_link not in index:
        if "</head>" not in index:
            raise RuntimeError("HEAD_END_MISSING")
        index = index.replace("</head>", "  " + css_link + "\n</head>", 1)

    if js_link not in index:
        if "</body>" not in index:
            raise RuntimeError("BODY_END_MISSING")
        index = index.replace("</body>", "  " + js_link + "\n</body>", 1)

    write_lf(INDEX, index)

    check = INDEX.read_text(encoding="utf-8")
    static = {
        "RAY_ORANGE_CSS_LINKED": css_link in check,
        "RAY_CONTRACT_JS_LINKED": js_link in check,
        "RELATION_ADD_PRESERVED": 'id="blueprintAddRelationBtn"' in check,
        "RELATION_SAVE_PRESERVED": 'id="relationSaveBtn"' in check,
        "RELATION_DELETE_PRESERVED": 'id="relationDeleteBtn"' in check,
        "FORGE_NAV_PRESERVED": 'id="forgeNavBtn"' in check,
        "RAY_MAP_PRESERVED": 'id="xrayMap"' in check,
    }
    for name, ok in static.items():
        emit(f"{name}={'PASS' if ok else 'FAIL'}")
    failed = [n for n, ok in static.items() if not ok]
    if failed:
        raise RuntimeError("STATIC_CONTRACT_FAIL " + ",".join(failed))

    ray_js = RAY_JS.read_text(encoding="utf-8")
    ray_css = RAY_CSS.read_text(encoding="utf-8")
    feature = {
        "EDITOR_GATE_EXPLICIT": 'blueprintEditor: "DISABLED_BY_CAPABILITY_GATE"' in ray_js,
        "NO_DRAG_CLAIM": "grid: false" in ray_js and "snap: false" in ray_js and "drag: false" in ray_js,
        "LINK_RUNTIME_TEST": "async function testLinkMode()" in ray_js,
        "RELATION_SAVE_OBSERVER": 'state.saveDispatch = "OBSERVED"' in ray_js,
        "RELATION_DELETE_OBSERVER": 'state.deleteDispatch = "OBSERVED"' in ray_js,
        "RELATION_MAP_MODE": 'map.dataset.mode = "relation-map"' in ray_js,
        "ORANGE_SCOPE": "#xrayWorkspace" in ray_css and "--vw-ray-accent: #ff8a2a" in ray_css,
        "SCOPED_XRAY_ORANGE": ".vx-sx-menu" in ray_css and "--vx-forge-cyan: #ff8a2a" in ray_css,
        "SEMANTIC_DANGER_NOT_OVERRIDDEN": ".xray-button.danger" not in ray_css,
    }
    for name, ok in feature.items():
        emit(f"{name}={'PASS' if ok else 'FAIL'}")
    failed = [n for n, ok in feature.items() if not ok]
    if failed:
        raise RuntimeError("FEATURE_CONTRACT_FAIL " + ",".join(failed))

    run(["cargo", "fmt", "--manifest-path", str(CARGO), "--", "--check"])
    run(["cargo", "test", "--manifest-path", str(CARGO)])
    run(["cargo", "build", "--release", "--manifest-path", str(CARGO)])

    if not BUILT_EXE.exists():
        raise RuntimeError("BUILT_EXE_MISSING " + str(BUILT_EXE))

    release_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    release_dir = ROOT / "versions" / VERSION / "builds" / release_stamp
    release_dir.mkdir(parents=True, exist_ok=False)
    immutable = release_dir / f"VertexWorks_{VERSION}.exe"
    shutil.copy2(BUILT_EXE, immutable)
    release_hash = sha256(immutable)

    current = json.loads(CURRENT.read_text(encoding="utf-8"))
    previous = current.get("release_exe") or current.get("executable")
    if "release_exe" in current:
        current["release_exe"] = str(immutable)
    elif "executable" in current:
        current["executable"] = str(immutable)
    else:
        current["release_exe"] = str(immutable)

    current["sha256"] = release_hash
    current["updated_at"] = datetime.now().isoformat(timespec="seconds")
    current["ray_contract"] = {
        "version": "000087",
        "theme": "VW_ORANGE_CHROME",
        "blueprint_role": "RELATION_MAP",
        "layout_editor": False,
        "grid_editor": False,
        "snap": False,
        "drag": False,
        "relation_controls_preserved": True,
        "relation_runtime_diagnostic": True,
        "semantic_colors_preserved": True,
        "forge_mutated": False,
    }
    current["ui_phase"] = "RAY_RELATION_MAP_ORANGE_CONTRACT_000087"
    write_lf(CURRENT, json.dumps(current, ensure_ascii=False, indent=2) + "\n")

    emit("BUILD_TEST=PASS")
    emit("NEW_IMMUTABLE_RELEASE=" + str(immutable))
    emit("NEW_RELEASE_SHA256=" + release_hash)
    emit("PREVIOUS_RELEASE=" + str(previous))
    emit("CURRENT_JSON_UPDATED=PASS")
    emit("RAY_RELATION_MAP_CONTRACT=ACTIVE")
    emit("VERTEX_WORKS_RAY_RELATION_MAP_ORANGE_087 PASS")

except Exception:
    shutil.copy2(backup / "index.html", INDEX)
    shutil.copy2(backup / "current.json", CURRENT)
    emit("MIGRATION_RESTORED=" + str(backup))
    raise
