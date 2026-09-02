from pathlib import Path
import subprocess
import sys

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
MANIFEST = ROOT / "src-tauri" / "Cargo.toml"
RELAY = ROOT / "src-tauri" / "src" / "clip_relay.rs"
MAIN = ROOT / "src-tauri" / "src" / "main.rs"
APP = ROOT / "ui" / "app.js"

checks = {
    "MANIFEST_EXISTS": MANIFEST.exists(),
    "RELAY_EXISTS": RELAY.exists(),
    "MAIN_EXISTS": MAIN.exists(),
    "APP_EXISTS": APP.exists(),
}

if all(checks.values()):
    relay = RELAY.read_text(encoding="utf-8")
    main = MAIN.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    checks.update({
        "WH_MOUSE_LL": "WH_MOUSE_LL" in relay,
        "MIDDLE_DOWN": "WM_MBUTTONDOWN" in relay,
        "MIDDLE_UP": "WM_MBUTTONUP" in relay,
        "CTRL_C_CAPTURE": "send_ctrl_key(VK_C)" in relay,
        "CTRL_V_RELEASE": "send_ctrl_key(VK_V)" in relay,
        "CF_HDROP": "CF_HDROP" in relay,
        "PRIORITY_PATH": "priority_armed" in relay,
        "RELAY_STARTED": "clip_relay::start()" in main,
        "PRIORITY_COMMAND": "clip_relay_set_priority" in main,
        "EVIDENCE_FRONTEND": 'invoke("clip_relay_set_priority"' in app,
    })

for key, value in checks.items():
    print(f"{key}={'PASS' if value else 'FAIL'}")

failed = [key for key, value in checks.items() if not value]
if failed:
    print("VERTEX_WORKS_CLIP_RELAY_FMT_HOTFIX_000094_VERIFY FAIL", ",".join(failed))
    sys.exit(1)

cmd = ["cargo", "fmt", "--manifest-path", str(MANIFEST), "--", "--check"]
print("RUN", " ".join(cmd))
result = subprocess.run(cmd, cwd=ROOT)
if result.returncode != 0:
    print("FMT_CHECK=FAIL")
    sys.exit(result.returncode)

print("FMT_CHECK=PASS")
print("VERTEX_WORKS_CLIP_RELAY_FMT_HOTFIX_000094_VERIFY PASS")
