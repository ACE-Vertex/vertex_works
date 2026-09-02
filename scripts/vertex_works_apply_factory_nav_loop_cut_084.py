from pathlib import Path
import json
import hashlib
import shutil
import subprocess
import sys
from datetime import datetime

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
JS = ROOT / "ui" / "vertex-works-factory-kernel.js"
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

for p in [JS, CURRENT, CARGO]:
    if not p.exists():
        raise SystemExit("REQUIRED_MISSING " + str(p))

src = JS.read_text(encoding="utf-8")

ray_click = '      clickExisting("rayNavBtn");\n'
forge_click = '      clickExisting("forgeNavBtn");\n'

if ray_click not in src or forge_click not in src:
    raise RuntimeError("000081_SELF_CLICK_PATTERN_NOT_FOUND")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = ROOT / "MIGRATION_BACKUPS" / "FACTORY_NAV_LOOP_CUT_084" / stamp
backup.mkdir(parents=True, exist_ok=True)
shutil.copy2(JS, backup / "vertex-works-factory-kernel.js")
shutil.copy2(CURRENT, backup / "current.json")

emit("VERTEX WORKS FACTORY NAV LOOP CUT 000084")
emit("FAULT=PROGRAMMATIC NAV BUTTON SELF-CLICK REENTRY")
emit("CUT=RAY/FORGE SELF-CLICK")
emit("BACKUP=" + str(backup))

try:
    src = src.replace(ray_click, "", 1)
    src = src.replace(forge_click, "", 1)

    anchor = "  let lastRecordedSensorTimestamp = null;\n"
    contract = (
        "\n"
        "  // FACTORY_NAV_LOOP_CUT_000084\n"
        "  // Facility switching is a state transition only.\n"
        "  // RAY/FORGE navigation controls must never be programmatically self-clicked.\n"
        "  const FACTORY_NAV_SELF_CLICK = false;\n"
    )
    if "FACTORY_NAV_LOOP_CUT_000084" not in src:
        if anchor not in src:
            raise RuntimeError("CONTRACT_INSERT_ANCHOR_MISSING")
        src = src.replace(anchor, anchor + contract, 1)

    write_lf(JS, src)

    check = JS.read_text(encoding="utf-8")
    source_checks = {
        "RAY_SELF_CLICK_REMOVED": 'clickExisting("rayNavBtn");' not in check,
        "FORGE_SELF_CLICK_REMOVED": 'clickExisting("forgeNavBtn");' not in check,
        "NO_SELF_CLICK_CONTRACT": "const FACTORY_NAV_SELF_CLICK = false;" in check,
        "SWITCH_FUNCTION_PRESERVED": "function switchFacility(name)" in check,
        "RAY_BRANCH_PRESERVED": 'activeFacility === "RAY"' in check,
        "FORGE_BRANCH_PRESERVED": 'activeFacility === "FORGE"' in check,
        "JUDGE_PRESERVED": 'data-facility="JUDGE"' in check,
        "SENSOR_PRESERVED": 'data-facility="SENSOR"' in check,
        "EVIDENCE_PRESERVED": 'data-facility="EVIDENCE"' in check,
        "RELEASE_PRESERVED": 'data-facility="RELEASE"' in check,
    }
    for name, ok in source_checks.items():
        emit(f"{name}={'PASS' if ok else 'FAIL'}")
    failed = [n for n, ok in source_checks.items() if not ok]
    if failed:
        raise RuntimeError("SOURCE_CHECK_FAIL " + ",".join(failed))

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
    current["factory_navigation"] = {
        "version": "000084",
        "mode": "NON_REENTRANT",
        "programmatic_self_click": False,
        "ray_forge_state_transition_only": True,
        "boot_nav_reentry": False
    }
    current["ui_phase"] = "FACTORY_NAV_LOOP_CUT_000084"
    write_lf(CURRENT, json.dumps(current, ensure_ascii=False, indent=2) + "\n")

    emit("BUILD_TEST=PASS")
    emit("NEW_IMMUTABLE_RELEASE=" + str(immutable))
    emit("NEW_RELEASE_SHA256=" + release_hash)
    emit("PREVIOUS_RELEASE=" + str(previous))
    emit("CURRENT_JSON_UPDATED=PASS")
    emit("FACTORY_NAVIGATION=NON_REENTRANT")
    emit("VERTEX_WORKS_FACTORY_NAV_LOOP_CUT_084 PASS")

except Exception:
    shutil.copy2(backup / "vertex-works-factory-kernel.js", JS)
    shutil.copy2(backup / "current.json", CURRENT)
    emit("MIGRATION_RESTORED=" + str(backup))
    raise
