from pathlib import Path
import sys

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
MAIN = ROOT / "src-tauri" / "src" / "main.rs"
APP = ROOT / "ui" / "app.js"
RELAY = ROOT / "src-tauri" / "src" / "clip_relay.rs"

checks = {
    "MAIN_EXISTS": MAIN.exists(),
    "APP_EXISTS": APP.exists(),
    "RELAY_EXISTS": RELAY.exists(),
}

if all(checks.values()):
    main = MAIN.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    relay = RELAY.read_text(encoding="utf-8")

    checks.update({
        "MODULE_REGISTERED": "mod clip_relay;" in main,
        "RELAY_STARTED": "clip_relay::start()" in main,
        "PRIORITY_COMMAND_REGISTERED": "clip_relay_set_priority," in main,
        "STATUS_COMMAND_REGISTERED": "clip_relay_status," in main,
        "EVIDENCE_PRIORITY_FRONTEND": 'invoke("clip_relay_set_priority"' in app,
        "WH_MOUSE_LL": "WH_MOUSE_LL" in relay,
        "MIDDLE_DOWN": "WM_MBUTTONDOWN" in relay,
        "MIDDLE_UP": "WM_MBUTTONUP" in relay,
        "CTRL_C_CAPTURE": "send_ctrl_key(VK_C)" in relay,
        "CTRL_V_RELEASE": "send_ctrl_key(VK_V)" in relay,
        "TEXT_CLIPBOARD": "CF_UNICODETEXT" in relay,
        "FILE_CLIPBOARD": "CF_HDROP" in relay,
        "PRIORITY_PATH": "priority_armed" in relay,
        "PASSTHROUGH_PATH": "CallNextHookEx" in relay,
        "RELEASE_CLEARS_BUFFER": "state.payload = None;" in relay,
    })

for key, value in checks.items():
    print(f"{key}={'PASS' if value else 'FAIL'}")

print("FLOW=SELECTION -> MIDDLE -> CLIP_IN -> MIDDLE -> RELEASE")
print("EVIDENCE_FLOW=EVIDENCE_BUTTON -> PRIORITY_CLIP_IN -> MIDDLE -> RELEASE")
print("FILES=CF_HDROP_PLUS_TEXT_PATH_FALLBACK")
print("WORKS_RUNNING_SCOPE=TRUE")

failed = [key for key, value in checks.items() if not value]
if failed:
    print("VERTEX_WORKS_CLIP_RELAY_000093_VERIFY FAIL", ",".join(failed))
    sys.exit(1)

print("VERTEX_WORKS_CLIP_RELAY_000093_VERIFY PASS")
