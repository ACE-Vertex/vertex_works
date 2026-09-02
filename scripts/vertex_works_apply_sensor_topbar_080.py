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
SENSOR_JS = UI / "vertex-works-sensors.js"
SENSOR_CSS = UI / "vertex-works-sensors.css"
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

required = [INDEX, SENSOR_JS, SENSOR_CSS, CURRENT, CARGO]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("REQUIRED_MISSING " + " | ".join(missing))

index = INDEX.read_text(encoding="utf-8")
if 'vertex-works-sensors.js' not in index or 'vertex-works-sensors.css' not in index:
    raise RuntimeError("SENSOR_079_LINK_CONTRACT_MISSING")
if 'id="vertexModeBar"' not in index:
    raise RuntimeError("TOPBAR_HOST_MISSING")
if 'id="settingsBtn"' not in index:
    raise RuntimeError("SETTINGS_BUTTON_ANCHOR_MISSING")
if 'id="rayNavBtn"' not in index or 'id="forgeNavBtn"' not in index:
    raise RuntimeError("WORKSPACE_NAV_CONTRACT_MISSING")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = ROOT / "MIGRATION_BACKUPS" / "SENSOR_TOPBAR_080" / stamp
backup.mkdir(parents=True, exist_ok=True)
shutil.copy2(CURRENT, backup / "current.json")

emit("VERTEX WORKS SENSOR BUS TOPBAR INTEGRATION 000080")
emit("HOST=vertexModeBar")
emit("INSERTION=BEFORE settingsBtn")
emit("BOTTOM_OVERLAY=PROHIBITED")
emit("BACKUP=" + str(backup))

js = SENSOR_JS.read_text(encoding="utf-8")
css = SENSOR_CSS.read_text(encoding="utf-8")

source_checks = {
    "TOPBAR_HOST_SOURCE": 'const host = $("#vertexModeBar")' in js,
    "SETTINGS_INSERT_ANCHOR": 'host.insertBefore(dock, settingsButton)' in js,
    "TOPBAR_PARENT_INSPECTION": '"SENSOR_TOPBAR_HOST"' in js,
    "NO_FIXED_DOCK": ".vw-sensor-dock {\n  position: relative;" in css,
    "BODY_OVERLAY_GUARD": "body > .vw-sensor-dock" in css,
    "CLIP_CLEARANCE_CONTRACT": "lower-right work surface" in css,
    "SENSOR_VERSION_080": 'const SENSOR_VERSION = "000080"' in js,
    "RAY_FORGE_PRESERVED": 'id="rayNavBtn"' in index and 'id="forgeNavBtn"' in index,
}
for name, ok in source_checks.items():
    emit(f"{name}={'PASS' if ok else 'FAIL'}")
failed = [name for name, ok in source_checks.items() if not ok]
if failed:
    raise RuntimeError("SOURCE_CONTRACT_FAIL " + ",".join(failed))

try:
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
    current["sensor_bus"] = {
        "version": "000080",
        "mode": "REAL_OBSERVATION",
        "sample_ms": 1500,
        "inspection_gate": True,
        "fake_telemetry": False,
        "host": "vertexModeBar",
        "placement": "TOPBAR_BEFORE_SETTINGS",
        "bottom_overlay": False,
        "clip_to_vera_clearance": True,
    }
    current["ui_phase"] = "SENSOR_BUS_TOPBAR_INTEGRATION_000080"

    write_lf(CURRENT, json.dumps(current, ensure_ascii=False, indent=2) + "\n")

    emit("BUILD_TEST=PASS")
    emit("NEW_IMMUTABLE_RELEASE=" + str(immutable))
    emit("NEW_RELEASE_SHA256=" + release_hash)
    emit("PREVIOUS_RELEASE=" + str(previous))
    emit("CURRENT_JSON_UPDATED=PASS")
    emit("SENSOR_BUS_TOPBAR=ACTIVE")
    emit("CLIP_TO_VERA_CLEARANCE=PASS")
    emit("VERTEX_WORKS_SENSOR_TOPBAR_080 PASS")

except Exception:
    shutil.copy2(backup / "current.json", CURRENT)
    emit("MIGRATION_RESTORED=" + str(backup))
    raise
