from pathlib import Path
import json
import re

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
UI = ROOT / "ui"
INDEX = UI / "index.html"
JS = UI / "vertex-works-restart.js"
CSS = UI / "vertex-works-restart.css"
MAIN = ROOT / "src-tauri" / "src" / "main.rs"
CURRENT = ROOT / "current.json"
ENTRY = ROOT / "VertexWorks.exe"

def emit(name, ok):
    print(f"{name}={'PASS' if ok else 'FAIL'}")
    return ok

index = INDEX.read_text(encoding="utf-8", errors="replace") if INDEX.exists() else ""
js = JS.read_text(encoding="utf-8", errors="replace") if JS.exists() else ""
css = CSS.read_text(encoding="utf-8", errors="replace") if CSS.exists() else ""
main = MAIN.read_text(encoding="utf-8", errors="replace") if MAIN.exists() else ""
cur = json.loads(CURRENT.read_text(encoding="utf-8")) if CURRENT.exists() else {}
restart = cur.get("restart_control") or {}
release_value = cur.get("release_exe") or cur.get("executable") or ""
release = Path(release_value) if release_value else Path("__missing__")

checks = [
    emit("ROOT_ENTRY_EXISTS", ENTRY.exists()),
    emit("RESTART_JS_EXISTS", JS.exists()),
    emit("RESTART_CSS_EXISTS", CSS.exists()),
    emit("RESTART_JS_LINKED", "vertex-works-restart.js" in index),
    emit("RESTART_CSS_LINKED", "vertex-works-restart.css" in index),
    emit("BOTTOM_LEFT_CSS", "left: 10px;" in css and "bottom: 10px;" in css),
    emit("TWO_CLICK_GUARD", "const ARM_MS = 2400" in js and 'data-state="armed"' in js),
    emit("TAURI_INVOKE", 'invoke("restart_vertex_works")' in js),
    emit("ROOT_RESOLVER", "fn vertex_works_project_root()" in main),
    emit("ROOT_LAUNCHER_PROBE", 'cursor.join("VertexWorks.exe")' in main),
    emit("CURRENT_JSON_PROBE", 'cursor.join("current.json")' in main),
    emit("NATIVE_RESTART_COMMAND", "fn restart_vertex_works(app: tauri::AppHandle)" in main),
    emit("HANDLER_REGISTERED", bool(re.search(r"generate_handler!\[[\s\S]*?\brestart_vertex_works\s*,", main))),
    emit("APP_EXIT", "app.exit(0);" in main),
    emit("CURRENT_RESTART_VERSION", restart.get("version") == "000082"),
    emit("CURRENT_BOTTOM_LEFT", restart.get("position") == "BOTTOM_LEFT"),
    emit("CURRENT_ROOT_LAUNCHER", restart.get("restart_target") == "ROOT_LAUNCHER"),
    emit("CURRENT_POINTER_AWARE", restart.get("current_pointer_aware") is True),
    emit("CURRENT_RELEASE_EXISTS", release.exists()),
    emit("IMMUTABLE_RELEASE", "\\versions\\0.5.0\\builds\\" in str(release).lower()),
]

if not all(checks):
    raise SystemExit("VERTEX_WORKS_NATIVE_RESTART_082_VERIFY FAIL")

print("VERTEX_WORKS_NATIVE_RESTART_082_VERIFY PASS")
