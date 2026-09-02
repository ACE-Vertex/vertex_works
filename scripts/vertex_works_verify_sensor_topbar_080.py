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
sensor = cur.get("sensor_bus") or {}
release_value = cur.get("release_exe") or cur.get("executable") or ""
release = Path(release_value) if release_value else Path("__missing__")

checks = [
    emit("ROOT_ENTRY_EXISTS", ENTRY.exists()),
    emit("TOPBAR_EXISTS", 'id="vertexModeBar"' in index),
    emit("SETTINGS_ANCHOR_EXISTS", 'id="settingsBtn"' in index),
    emit("SENSOR_VERSION_080", 'const SENSOR_VERSION = "000080"' in js),
    emit("TOPBAR_HOST_SOURCE", 'const host = $("#vertexModeBar")' in js),
    emit("INSERT_BEFORE_SETTINGS", 'host.insertBefore(dock, settingsButton)' in js),
    emit("TOPBAR_HOST_RUNTIME_CHECK", '"SENSOR_TOPBAR_HOST"' in js),
    emit("DOCK_POSITION_RELATIVE", ".vw-sensor-dock {\n  position: relative;" in css),
    emit("BOTTOM_OVERLAY_GUARD", "body > .vw-sensor-dock" in css),
    emit("CLIP_CLEARANCE_COMMENT", "lower-right work surface" in css),
    emit("RAY_PRESERVED", 'id="rayNavBtn"' in index),
    emit("FORGE_PRESERVED", 'id="forgeNavBtn"' in index),
    emit("ORANGE_PRESERVED", 'vertex-works-orange.css' in index),
    emit("CURRENT_SENSOR_080", sensor.get("version") == "000080"),
    emit("CURRENT_TOPBAR_HOST", sensor.get("host") == "vertexModeBar"),
    emit("CURRENT_BOTTOM_OVERLAY_FALSE", sensor.get("bottom_overlay") is False),
    emit("CURRENT_VERA_CLEARANCE", sensor.get("clip_to_vera_clearance") is True),
    emit("CURRENT_RELEASE_EXISTS", release.exists()),
    emit("IMMUTABLE_RELEASE", "\\versions\\0.5.0\\builds\\" in str(release).lower()),
]

if not all(checks):
    raise SystemExit("VERTEX_WORKS_SENSOR_TOPBAR_080_VERIFY FAIL")

print("VERTEX_WORKS_SENSOR_TOPBAR_080_VERIFY PASS")
