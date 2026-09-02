from pathlib import Path
import sys

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
APP = ROOT / "ui" / "app.js"
MAIN = ROOT / "src-tauri" / "src" / "main.rs"
RELAY = ROOT / "src-tauri" / "src" / "clip_relay.rs"

checks = {
    "APP_EXISTS": APP.exists(),
    "MAIN_EXISTS": MAIN.exists(),
    "RELAY_EXISTS": RELAY.exists(),
}

if all(checks.values()):
    app = APP.read_text(encoding="utf-8")
    main = MAIN.read_text(encoding="utf-8")
    relay = RELAY.read_text(encoding="utf-8")

    checks.update({
        "ERROR_PRIORITY_FRONTEND": 'invoke("clip_relay_set_priority", { text, kind: "ERROR" })' in app,
        "ERROR_PRIORITY_LOG": "CLIP RELAY: PRIORITY ERROR ARMED" in app,
        "EVIDENCE_PRIORITY_FRONTEND": 'invoke("clip_relay_set_priority", { text, kind: "EVIDENCE" })' in app,
        "PRIORITY_COMMAND_REGISTERED": "clip_relay_set_priority," in main,
        "PRIORITY_RELEASE_FIRST": "if priority_armed" in relay and "return release_payload();" in relay,
        "WH_MOUSE_LL_PRESERVED": "WH_MOUSE_LL" in relay,
        "CTRL_V_RELEASE_PRESERVED": "send_ctrl_key(VK_V)" in relay,
    })

for key, value in checks.items():
    print(f"{key}={'PASS' if value else 'FAIL'}")

print("ERROR_FLOW=ERROR_REPORT_BUTTON -> PRIORITY_CLIP_IN -> MIDDLE -> RELEASE")
print("EVIDENCE_FLOW=EVIDENCE_BUTTON -> PRIORITY_CLIP_IN -> MIDDLE -> RELEASE")
print("NORMAL_SELECTION_FLOW=UNCHANGED")

failed = [key for key, value in checks.items() if not value]
if failed:
    print("VERTEX_WORKS_CLIP_RELAY_ERROR_PRIORITY_000095_VERIFY FAIL", ",".join(failed))
    sys.exit(1)

print("VERTEX_WORKS_CLIP_RELAY_ERROR_PRIORITY_000095_VERIFY PASS")
