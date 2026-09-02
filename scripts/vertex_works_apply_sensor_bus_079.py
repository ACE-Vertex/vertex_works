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

def out(value=""):
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
    out("RUN " + " ".join(map(str, args)))
    cp = subprocess.run(args, text=True, capture_output=True)
    if cp.stdout:
        out(cp.stdout)
    if cp.stderr:
        out(cp.stderr)
    if cp.returncode != 0:
        raise RuntimeError("COMMAND_FAILED " + " ".join(map(str, args)))

required = [INDEX, SENSOR_JS, SENSOR_CSS, CURRENT, CARGO]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("REQUIRED_MISSING " + " | ".join(missing))

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = ROOT / "MIGRATION_BACKUPS" / "SENSOR_BUS_079" / stamp
backup.mkdir(parents=True, exist_ok=True)
shutil.copy2(INDEX, backup / "index.html")
shutil.copy2(CURRENT, backup / "current.json")

out("VERTEX WORKS SENSOR BUS / INSPECTION GATE 000079")
out("MODE=REAL_OBSERVATION")
out("SAMPLE_MS=1500")
out("BACKUP=" + str(backup))

index = INDEX.read_text(encoding="utf-8")
original = index

if 'vertex-works-orange.css' not in index:
    raise RuntimeError("ORANGE_WORKSPACE_CONTRACT_MISSING")
if 'id="rayNavBtn"' not in index or 'id="forgeNavBtn"' not in index:
    raise RuntimeError("WORKSPACE_NAV_CONTRACT_MISSING")

sensor_css_link = '<link rel="stylesheet" href="vertex-works-sensors.css" />'
if sensor_css_link not in index:
    anchor = '<link rel="stylesheet" href="vertex-works-orange.css" />'
    index = index.replace(anchor, anchor + "\n  " + sensor_css_link, 1)

sensor_js_link = '<script src="vertex-works-sensors.js"></script>'
if sensor_js_link not in index:
    if "</body>" not in index:
        raise RuntimeError("BODY_END_MISSING")
    index = index.replace("</body>", "  " + sensor_js_link + "\n</body>", 1)

try:
    write_lf(INDEX, index)

    check = INDEX.read_text(encoding="utf-8")
    static = {
        "SENSOR_CSS_LINKED": sensor_css_link in check,
        "SENSOR_JS_LINKED": sensor_js_link in check,
        "RAY_PRESERVED": 'id="rayNavBtn"' in check,
        "FORGE_PRESERVED": 'id="forgeNavBtn"' in check,
        "ORANGE_PRESERVED": 'vertex-works-orange.css' in check,
        "ENGLISH_CONTRACT_PRESERVED": '<html lang="en"' in check,
        "VW_PRODUCT_PRESERVED": 'data-product="VW"' in check,
    }
    for k,v in static.items():
        out(f"{k}={'PASS' if v else 'FAIL'}")
    failed = [k for k,v in static.items() if not v]
    if failed:
        raise RuntimeError("STATIC_CONTRACT_FAIL " + ",".join(failed))

    js = SENSOR_JS.read_text(encoding="utf-8")
    css = SENSOR_CSS.read_text(encoding="utf-8")
    sensor_checks = {
        "NO_FAKE_TELEMETRY_MARKER": "NO FAKE TELEMETRY" in js,
        "REAL_FRAME_SENSOR": "requestAnimationFrame" in js,
        "REAL_LOOP_SENSOR": "loopDriftMs" in js,
        "VISIBLE_JAPANESE_INSPECTION": "visibleJapaneseNodes" in js,
        "DUPLICATE_ID_INSPECTION": "duplicateIds" in js,
        "BROKEN_IMAGE_INSPECTION": "brokenImages" in js,
        "RUNTIME_ERROR_CAPTURE": "unhandledrejection" in js,
        "VERA_HANDOFF_CHECK": "veraHandoffPresent" in js,
        "LOW_FREQUENCY_SAMPLE": "const SAMPLE_MS = 1500" in js,
        "RESPONSIVE_SENSOR_UI": "@media (max-width: 900px)" in css,
    }
    for k,v in sensor_checks.items():
        out(f"{k}={'PASS' if v else 'FAIL'}")
    failed = [k for k,v in sensor_checks.items() if not v]
    if failed:
        raise RuntimeError("SENSOR_CONTRACT_FAIL " + ",".join(failed))

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
        "version": "000079",
        "mode": "REAL_OBSERVATION",
        "sample_ms": 1500,
        "inspection_gate": True,
        "fake_telemetry": False,
    }
    current["ui_phase"] = "SENSOR_BUS_INSPECTION_GATE_000079"

    write_lf(CURRENT, json.dumps(current, ensure_ascii=False, indent=2) + "\n")

    out("BUILD_TEST=PASS")
    out("NEW_IMMUTABLE_RELEASE=" + str(immutable))
    out("NEW_RELEASE_SHA256=" + release_hash)
    out("PREVIOUS_RELEASE=" + str(previous))
    out("CURRENT_JSON_UPDATED=PASS")
    out("SENSOR_BUS=ACTIVE")
    out("INSPECTION_GATE=ACTIVE")
    out("VERTEX_WORKS_SENSOR_BUS_079 PASS")

except Exception:
    shutil.copy2(backup / "index.html", INDEX)
    shutil.copy2(backup / "current.json", CURRENT)
    out("MIGRATION_RESTORED=" + str(backup))
    raise
