from pathlib import Path
import json

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
UI = ROOT / "ui"
INDEX = UI / "index.html"
JS = UI / "vertex-works-sensors.js"
CSS = UI / "vertex-works-sensors.css"
CURRENT = ROOT / "current.json"
ENTRY = ROOT / "VertexWorks.exe"

def emit(name, ok):
    print(f"{name}={'PASS' if ok else 'FAIL'}")
    return ok

index = INDEX.read_text(encoding="utf-8", errors="replace") if INDEX.exists() else ""
js = JS.read_text(encoding="utf-8", errors="replace") if JS.exists() else ""
css = CSS.read_text(encoding="utf-8", errors="replace") if CSS.exists() else ""
cur = json.loads(CURRENT.read_text(encoding="utf-8")) if CURRENT.exists() else {}
release_value = cur.get("release_exe") or cur.get("executable") or ""
release = Path(release_value) if release_value else Path("__missing__")
sensor = cur.get("sensor_bus") or {}

checks = [
    emit("ROOT_ENTRY_EXISTS", ENTRY.exists()),
    emit("SENSOR_JS_EXISTS", JS.exists()),
    emit("SENSOR_CSS_EXISTS", CSS.exists()),
    emit("SENSOR_JS_LINKED", 'vertex-works-sensors.js' in index),
    emit("SENSOR_CSS_LINKED", 'vertex-works-sensors.css' in index),
    emit("REAL_FRAME_SENSOR", "requestAnimationFrame" in js),
    emit("REAL_EVENT_LOOP_SENSOR", "loopDriftMs" in js),
    emit("DOM_SENSOR", "domNodes" in js),
    emit("HEAP_SENSOR_OPTIONAL", "performance.memory" in js),
    emit("VISIBLE_JAPANESE_INSPECTION", "visibleJapaneseNodes" in js),
    emit("DUPLICATE_ID_INSPECTION", "duplicateIds" in js),
    emit("OVERFLOW_INSPECTION", "HORIZONTAL_OVERFLOW" in js),
    emit("BROKEN_IMAGE_INSPECTION", "brokenImages" in js),
    emit("RUNTIME_ERROR_CAPTURE", "unhandledrejection" in js),
    emit("VERA_HANDOFF_CHECK", "veraHandoffPresent" in js),
    emit("NO_FAKE_TELEMETRY", "NO FAKE TELEMETRY" in js),
    emit("SAMPLE_INTERVAL_1500", "const SAMPLE_MS = 1500" in js),
    emit("RAY_PRESERVED", 'id="rayNavBtn"' in index),
    emit("FORGE_PRESERVED", 'id="forgeNavBtn"' in index),
    emit("ORANGE_PRESERVED", 'vertex-works-orange.css' in index),
    emit("CURRENT_SENSOR_VERSION", sensor.get("version") == "000079"),
    emit("CURRENT_REAL_OBSERVATION", sensor.get("mode") == "REAL_OBSERVATION"),
    emit("CURRENT_FAKE_TELEMETRY_FALSE", sensor.get("fake_telemetry") is False),
    emit("CURRENT_RELEASE_EXISTS", release.exists()),
    emit("IMMUTABLE_RELEASE", "\\versions\\0.5.0\\builds\\" in str(release).lower()),
]

if not all(checks):
    raise SystemExit("VERTEX_WORKS_SENSOR_BUS_079_VERIFY FAIL")

print("VERTEX_WORKS_SENSOR_BUS_079_VERIFY PASS")
