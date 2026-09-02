from pathlib import Path
import json
import hashlib
import shutil
import subprocess
import sys
from datetime import datetime

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
UI = ROOT / "ui"
INDEX = UI / "index.html"
KERNEL_JS = UI / "vertex-works-factory-kernel.js"
KERNEL_CSS = UI / "vertex-works-factory-kernel.css"
CURRENT = ROOT / "current.json"
CARGO = ROOT / "src-tauri" / "Cargo.toml"
BUILT_EXE = ROOT / "src-tauri" / "target" / "release" / "vertex-receiver.exe"
VERSION = "0.5.0"

def emit(value=""):
    text = str(value)
    sys.stdout.write(text.encode("ascii", "backslashreplace").decode("ascii") + "\n")

def write_lf(path: Path, text: str):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def run(args):
    emit("RUN " + " ".join(map(str, args)))
    cp = subprocess.run(args, text=True, capture_output=True)
    if cp.stdout:
        emit(cp.stdout)
    if cp.stderr:
        emit(cp.stderr)
    if cp.returncode != 0:
        raise RuntimeError("COMMAND_FAILED " + " ".join(map(str, args)))

required = [INDEX, KERNEL_JS, KERNEL_CSS, CURRENT, CARGO]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("REQUIRED_MISSING " + " | ".join(missing))

index = INDEX.read_text(encoding="utf-8")
anchors = [
    'id="vertexModeBar"',
    'id="rayNavBtn"',
    'id="forgeNavBtn"',
    'vertex-works-orange.css',
    'vertex-works-sensors.js',
    'vertex-works-sensors.css',
]
for anchor in anchors:
    if anchor not in index:
        raise RuntimeError("SOURCE_CONTRACT_MISSING " + anchor)

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = ROOT / "MIGRATION_BACKUPS" / "FACTORY_KERNEL_081" / stamp
backup.mkdir(parents=True, exist_ok=True)
shutil.copy2(INDEX, backup / "index.html")
shutil.copy2(CURRENT, backup / "current.json")

emit("VERTEX WORKS FACTORY KERNEL / MULTI-FACILITY CHASSIS 000081")
emit("FACILITIES=RAY,FORGE,JUDGE,SENSOR,EVIDENCE,RELEASE")
emit("ONE_PRODUCT_ICON=TOP_LEFT")
emit("FACTORY_BACKGROUND=JUDGE+EVIDENCE+RELEASE_GATE")
emit("BACKUP=" + str(backup))

css_link = '<link rel="stylesheet" href="vertex-works-factory-kernel.css" />'
js_link = '<script src="vertex-works-factory-kernel.js"></script>'

if css_link not in index:
    anchor = '<link rel="stylesheet" href="vertex-works-sensors.css" />'
    index = index.replace(anchor, anchor + "\n  " + css_link, 1)

if js_link not in index:
    anchor = '<script src="vertex-works-sensors.js"></script>'
    index = index.replace(anchor, anchor + "\n  " + js_link, 1)

try:
    write_lf(INDEX, index)

    check = INDEX.read_text(encoding="utf-8")
    static = {
        "FACTORY_CSS_LINKED": css_link in check,
        "FACTORY_JS_LINKED": js_link in check,
        "RAY_PRESERVED": 'id="rayNavBtn"' in check,
        "FORGE_PRESERVED": 'id="forgeNavBtn"' in check,
        "SENSOR_PRESERVED": 'vertex-works-sensors.js' in check,
        "ORANGE_PRESERVED": 'vertex-works-orange.css' in check,
        "ENGLISH_PRESERVED": '<html lang="en"' in check,
    }
    for k,v in static.items():
        emit(f"{k}={'PASS' if v else 'FAIL'}")
    failed = [k for k,v in static.items() if not v]
    if failed:
        raise RuntimeError("STATIC_CONTRACT_FAIL " + ",".join(failed))

    js = KERNEL_JS.read_text(encoding="utf-8")
    css = KERNEL_CSS.read_text(encoding="utf-8")
    kernel_checks = {
        "FACILITY_RAY": '["RAY", "FORGE", "JUDGE", "SENSOR", "EVIDENCE", "RELEASE"]' in js,
        "JUDGE_ENGINE": "function judgeNow()" in js,
        "EVIDENCE_STORE": 'localStorage.setItem(EVIDENCE_KEY' in js,
        "RELEASE_GATE": "function releaseGate()" in js,
        "NO_FAKE_NATIVE_BUILD": "Native Cargo/build evidence bridge is not connected" in js,
        "SENSOR_INTEGRATION": "window.VertexWorksSensors" in js,
        "VERA_HANDOFF": "CLIP TO VERA" in js,
        "ONE_PRODUCT_ICON_CSS": ".vw-duplicate-product-icon" in css,
        "TOP_OFFSET_COMPACT": "height: 52px !important;" in css,
        "NO_MAX_WIDTH_FACTORY": "max-width: none !important;" in css,
    }
    for k,v in kernel_checks.items():
        emit(f"{k}={'PASS' if v else 'FAIL'}")
    failed = [k for k,v in kernel_checks.items() if not v]
    if failed:
        raise RuntimeError("KERNEL_CONTRACT_FAIL " + ",".join(failed))

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
    current["factory_kernel"] = {
        "version": "000081",
        "facilities": ["RAY", "FORGE", "JUDGE", "SENSOR", "EVIDENCE", "RELEASE"],
        "judge_engine": True,
        "sensor_bridge": "UI_RUNTIME_CONNECTED",
        "evidence_store": "LOCAL_KERNEL_STORE",
        "release_gate": "CONNECTED_TO_JUDGE",
        "native_build_gate": "UNAVAILABLE_PENDING_NATIVE_BRIDGE",
        "single_product_icon": True,
        "top_chassis_px": 52,
    }
    current["ui_phase"] = "FACTORY_KERNEL_MULTI_FACILITY_000081"

    write_lf(CURRENT, json.dumps(current, ensure_ascii=False, indent=2) + "\n")

    emit("BUILD_TEST=PASS")
    emit("NEW_IMMUTABLE_RELEASE=" + str(immutable))
    emit("NEW_RELEASE_SHA256=" + release_hash)
    emit("PREVIOUS_RELEASE=" + str(previous))
    emit("CURRENT_JSON_UPDATED=PASS")
    emit("FACTORY_KERNEL=ACTIVE")
    emit("VERTEX_WORKS_FACTORY_KERNEL_081 PASS")

except Exception:
    shutil.copy2(backup / "index.html", INDEX)
    shutil.copy2(backup / "current.json", CURRENT)
    emit("MIGRATION_RESTORED=" + str(backup))
    raise
