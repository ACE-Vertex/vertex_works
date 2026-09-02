from pathlib import Path
import json

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
UI = ROOT / "ui"
INDEX = UI / "index.html"
JS = UI / "vertex-works-factory-kernel.js"
CSS = UI / "vertex-works-factory-kernel.css"
CURRENT = ROOT / "current.json"
ENTRY = ROOT / "VertexWorks.exe"

def emit(name, ok):
    print(f"{name}={'PASS' if ok else 'FAIL'}")
    return ok

index = INDEX.read_text(encoding="utf-8", errors="replace") if INDEX.exists() else ""
js = JS.read_text(encoding="utf-8", errors="replace") if JS.exists() else ""
css = CSS.read_text(encoding="utf-8", errors="replace") if CSS.exists() else ""
cur = json.loads(CURRENT.read_text(encoding="utf-8")) if CURRENT.exists() else {}
kernel = cur.get("factory_kernel") or {}
release_value = cur.get("release_exe") or cur.get("executable") or ""
release = Path(release_value) if release_value else Path("__missing__")

checks = [
    emit("ROOT_ENTRY_EXISTS", ENTRY.exists()),
    emit("FACTORY_JS_EXISTS", JS.exists()),
    emit("FACTORY_CSS_EXISTS", CSS.exists()),
    emit("FACTORY_JS_LINKED", 'vertex-works-factory-kernel.js' in index),
    emit("FACTORY_CSS_LINKED", 'vertex-works-factory-kernel.css' in index),
    emit("RAY_PRESERVED", 'id="rayNavBtn"' in index),
    emit("FORGE_PRESERVED", 'id="forgeNavBtn"' in index),
    emit("SENSOR_BRIDGE_CODE", "window.VertexWorksSensors" in js),
    emit("JUDGE_ENGINE_CODE", "function judgeNow()" in js),
    emit("EVIDENCE_STORE_CODE", "localStorage.setItem(EVIDENCE_KEY" in js),
    emit("RELEASE_GATE_CODE", "function releaseGate()" in js),
    emit("VERA_HANDOFF_CODE", "CLIP TO VERA" in js),
    emit("NATIVE_BUILD_NOT_FAKED", "Native Cargo/build evidence bridge is not connected" in js),
    emit("ONE_ICON_RULE", ".vw-duplicate-product-icon" in css),
    emit("TOP_CHASSIS_52", "height: 52px !important;" in css),
    emit("LARGE_SCREEN_UNCAPPED", "max-width: none !important;" in css),
    emit("CURRENT_KERNEL_VERSION", kernel.get("version") == "000081"),
    emit("CURRENT_JUDGE_ENGINE", kernel.get("judge_engine") is True),
    emit("CURRENT_SINGLE_ICON", kernel.get("single_product_icon") is True),
    emit("CURRENT_NATIVE_GATE_UNAVAILABLE", kernel.get("native_build_gate") == "UNAVAILABLE_PENDING_NATIVE_BRIDGE"),
    emit("CURRENT_RELEASE_EXISTS", release.exists()),
    emit("IMMUTABLE_RELEASE", "\\versions\\0.5.0\\builds\\" in str(release).lower()),
]

if not all(checks):
    raise SystemExit("VERTEX_WORKS_FACTORY_KERNEL_081_VERIFY FAIL")

print("VERTEX_WORKS_FACTORY_KERNEL_081_VERIFY PASS")
