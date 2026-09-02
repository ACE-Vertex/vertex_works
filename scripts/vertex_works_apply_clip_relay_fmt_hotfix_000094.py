from pathlib import Path
import subprocess
import sys

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
MANIFEST = ROOT / "src-tauri" / "Cargo.toml"
RELAY = ROOT / "src-tauri" / "src" / "clip_relay.rs"
MAIN = ROOT / "src-tauri" / "src" / "main.rs"

def fail(message):
    print(f"CLIP_RELAY_FMT_HOTFIX_000094_FAIL={message}")
    raise SystemExit(1)

for path in (MANIFEST, RELAY, MAIN):
    if not path.exists():
        fail(f"MISSING:{path}")

relay = RELAY.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")

required = {
    "RELAY_MODULE": "WH_MOUSE_LL" in relay,
    "EVIDENCE_PRIORITY_COMMAND": "clip_relay_set_priority" in main,
    "RELAY_START": "clip_relay::start()" in main,
}
for key, value in required.items():
    print(f"{key}={'PASS' if value else 'FAIL'}")
if not all(required.values()):
    fail("000093_SOURCE_CONTRACT_MISSING")

cmd = ["cargo", "fmt", "--manifest-path", str(MANIFEST)]
print("RUN", " ".join(cmd))
result = subprocess.run(cmd, cwd=ROOT, text=True)
if result.returncode != 0:
    fail(f"CARGO_FMT_EXIT_{result.returncode}")

print("CHANGE=RUSTFMT_ONLY")
print("ALGORITHM_CHANGE=NONE")
print("CLIP_RELAY_000093_BEHAVIOR=PRESERVED")
print("VERTEX_WORKS_CLIP_RELAY_FMT_HOTFIX_000094=PASS")
