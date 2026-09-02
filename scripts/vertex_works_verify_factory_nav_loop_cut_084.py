from pathlib import Path
import json

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
JS = ROOT / "ui" / "vertex-works-factory-kernel.js"
CURRENT = ROOT / "current.json"
ENTRY = ROOT / "VertexWorks.exe"

def emit(name, ok):
    print(f"{name}={'PASS' if ok else 'FAIL'}")
    return ok

src = JS.read_text(encoding="utf-8", errors="replace") if JS.exists() else ""
cur = json.loads(CURRENT.read_text(encoding="utf-8")) if CURRENT.exists() else {}
nav = cur.get("factory_navigation") or {}
release_value = cur.get("release_exe") or cur.get("executable") or ""
release = Path(release_value) if release_value else Path("__missing__")

checks = [
    emit("ROOT_ENTRY_EXISTS", ENTRY.exists()),
    emit("FACTORY_KERNEL_EXISTS", JS.exists()),
    emit("RAY_SELF_CLICK_ABSENT", 'clickExisting("rayNavBtn");' not in src),
    emit("FORGE_SELF_CLICK_ABSENT", 'clickExisting("forgeNavBtn");' not in src),
    emit("SELF_CLICK_CONTRACT_FALSE", "const FACTORY_NAV_SELF_CLICK = false;" in src),
    emit("SWITCH_FACILITY_PRESENT", "function switchFacility(name)" in src),
    emit("RAY_BRANCH_PRESENT", 'activeFacility === "RAY"' in src),
    emit("FORGE_BRANCH_PRESENT", 'activeFacility === "FORGE"' in src),
    emit("CUSTOM_FACILITIES_PRESENT",
         all(x in src for x in [
             'data-facility="JUDGE"',
             'data-facility="SENSOR"',
             'data-facility="EVIDENCE"',
             'data-facility="RELEASE"'
         ])),
    emit("CURRENT_NAV_VERSION", nav.get("version") == "000084"),
    emit("CURRENT_NON_REENTRANT", nav.get("mode") == "NON_REENTRANT"),
    emit("CURRENT_SELF_CLICK_FALSE", nav.get("programmatic_self_click") is False),
    emit("CURRENT_BOOT_REENTRY_FALSE", nav.get("boot_nav_reentry") is False),
    emit("CURRENT_RELEASE_EXISTS", release.exists()),
    emit("IMMUTABLE_RELEASE", "\\versions\\0.5.0\\builds\\" in str(release).lower()),
]

if not all(checks):
    raise SystemExit("VERTEX_WORKS_FACTORY_NAV_LOOP_CUT_084_VERIFY FAIL")

print("FAULT_CLASS=UI_NAVIGATION_REENTRANCY")
print("LOOP_CUT=PASS")
print("VERTEX_WORKS_FACTORY_NAV_LOOP_CUT_084_VERIFY PASS")
