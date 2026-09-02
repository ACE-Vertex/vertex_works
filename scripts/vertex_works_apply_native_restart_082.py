from pathlib import Path
import json
import hashlib
import re
import shutil
import subprocess
import sys
from datetime import datetime

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
UI = ROOT / "ui"
INDEX = UI / "index.html"
MAIN = ROOT / "src-tauri" / "src" / "main.rs"
CURRENT = ROOT / "current.json"
CARGO = ROOT / "src-tauri" / "Cargo.toml"
BUILT_EXE = ROOT / "src-tauri" / "target" / "release" / "vertex-receiver.exe"
ROOT_ENTRY = ROOT / "VertexWorks.exe"
VERSION = "0.5.0"
RUST_COMMAND = 'fn vertex_works_project_root() -> Result<PathBuf, String> {\n    let exe = std::env::current_exe().map_err(|e| format!("resolve current exe: {e}"))?;\n    let mut cursor = exe\n        .parent()\n        .map(Path::to_path_buf)\n        .ok_or_else(|| "current executable has no parent directory".to_string())?;\n\n    for _ in 0..16 {\n        let current = cursor.join("current.json");\n        let entry = cursor.join("VertexWorks.exe");\n        if current.is_file() && entry.is_file() {\n            return Ok(cursor);\n        }\n        if !cursor.pop() {\n            break;\n        }\n    }\n\n    Err("Vertex Works project root could not be resolved from the active release".into())\n}\n\n#[tauri::command]\nfn restart_vertex_works(app: tauri::AppHandle) -> Result<(), String> {\n    let root = vertex_works_project_root()?;\n    let entry = root.join("VertexWorks.exe");\n\n    let mut command = Command::new(&entry);\n    command.current_dir(&root);\n    suppress_child_console(&mut command);\n    command\n        .spawn()\n        .map_err(|e| format!("restart root launcher {}: {e}", entry.display()))?;\n\n    app.exit(0);\n    Ok(())\n}\n\n'

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

required = [INDEX, MAIN, CURRENT, CARGO, ROOT_ENTRY]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("REQUIRED_MISSING " + " | ".join(missing))

index = INDEX.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")

for anchor in ['id="vertexModeBar"', 'vertex-works-factory-kernel.js', 'vertex-works-factory-kernel.css']:
    if anchor not in index:
        raise RuntimeError("UI_CONTRACT_MISSING " + anchor)

if "tauri::Builder::default()" not in main or "tauri::generate_handler![" not in main:
    raise RuntimeError("TAURI_HANDLER_CONTRACT_MISSING")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = ROOT / "MIGRATION_BACKUPS" / "NATIVE_RESTART_082" / stamp
backup.mkdir(parents=True, exist_ok=True)
shutil.copy2(INDEX, backup / "index.html")
shutil.copy2(MAIN, backup / "main.rs")
shutil.copy2(CURRENT, backup / "current.json")

emit("VERTEX WORKS NATIVE RESTART CONTROL 000082")
emit("POSITION=BOTTOM_LEFT")
emit("RESTART_TARGET=ROOT VertexWorks.exe")
emit("CURRENT_POINTER_AWARE=YES")
emit("ACCIDENT_GUARD=TWO_CLICK_ARM")
emit("BACKUP=" + str(backup))

css_link = '<link rel="stylesheet" href="vertex-works-restart.css" />'
js_link = '<script src="vertex-works-restart.js"></script>'

if css_link not in index:
    anchor = '<link rel="stylesheet" href="vertex-works-factory-kernel.css" />'
    if anchor not in index:
        raise RuntimeError("FACTORY_CSS_LINK_ANCHOR_MISSING")
    index = index.replace(anchor, anchor + "\n  " + css_link, 1)

if js_link not in index:
    anchor = '<script src="vertex-works-factory-kernel.js"></script>'
    if anchor not in index:
        raise RuntimeError("FACTORY_JS_LINK_ANCHOR_MISSING")
    index = index.replace(anchor, anchor + "\n  " + js_link, 1)

if "fn restart_vertex_works(" not in main:
    anchor = "#[tauri::command]\nfn receiver_info()"
    if anchor not in main:
        raise RuntimeError("RUST_INSERT_ANCHOR_MISSING receiver_info")
    main = main.replace(anchor, RUST_COMMAND + anchor, 1)

if not re.search(r"generate_handler!\[[\s\S]*?\brestart_vertex_works\s*,", main):
    anchor = "            receiver_info,"
    if anchor not in main:
        raise RuntimeError("HANDLER_INSERT_ANCHOR_MISSING receiver_info")
    main = main.replace(anchor, "            restart_vertex_works,\n" + anchor, 1)

try:
    write_lf(INDEX, index)
    write_lf(MAIN, main)

    ui_check = INDEX.read_text(encoding="utf-8")
    rust_check = MAIN.read_text(encoding="utf-8")

    checks = {
        "RESTART_CSS_LINKED": css_link in ui_check,
        "RESTART_JS_LINKED": js_link in ui_check,
        "RUST_COMMAND_PRESENT": "fn restart_vertex_works(app: tauri::AppHandle)" in rust_check,
        "ROOT_RESOLVER_PRESENT": "fn vertex_works_project_root()" in rust_check,
        "ROOT_ENTRY_TARGET": 'cursor.join("VertexWorks.exe")' in rust_check,
        "CURRENT_JSON_ROOT_PROBE": 'cursor.join("current.json")' in rust_check,
        "NATIVE_HANDLER_REGISTERED": bool(re.search(r"generate_handler!\[[\s\S]*?\brestart_vertex_works\s*,", rust_check)),
        "APP_EXIT_USED": "app.exit(0);" in rust_check,
        "RAY_PRESERVED": 'id="rayNavBtn"' in ui_check,
        "FORGE_PRESERVED": 'id="forgeNavBtn"' in ui_check,
    }
    for name, ok in checks.items():
        emit(f"{name}={'PASS' if ok else 'FAIL'}")
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise RuntimeError("STATIC_CONTRACT_FAIL " + ",".join(failed))

    run(["cargo", "fmt", "--manifest-path", str(CARGO)])
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
    current["restart_control"] = {
        "version": "000082",
        "position": "BOTTOM_LEFT",
        "native_command": "restart_vertex_works",
        "restart_target": "ROOT_LAUNCHER",
        "current_pointer_aware": True,
        "accident_guard": "TWO_CLICK_ARM_2400MS",
    }
    current["ui_phase"] = "NATIVE_RESTART_CONTROL_000082"

    write_lf(CURRENT, json.dumps(current, ensure_ascii=False, indent=2) + "\n")

    emit("BUILD_TEST=PASS")
    emit("NEW_IMMUTABLE_RELEASE=" + str(immutable))
    emit("NEW_RELEASE_SHA256=" + release_hash)
    emit("PREVIOUS_RELEASE=" + str(previous))
    emit("CURRENT_JSON_UPDATED=PASS")
    emit("RESTART_CONTROL=ACTIVE")
    emit("VERTEX_WORKS_NATIVE_RESTART_082 PASS")

except Exception:
    shutil.copy2(backup / "index.html", INDEX)
    shutil.copy2(backup / "main.rs", MAIN)
    shutil.copy2(backup / "current.json", CURRENT)
    emit("MIGRATION_RESTORED=" + str(backup))
    raise
