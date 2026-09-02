from pathlib import Path
import shutil
import sys

root = Path.cwd()
built = root / "src-tauri" / "target" / "release" / "vertex-receiver.exe"
dest = root / "VertexReceiver_0.2.4.exe"

if not built.exists():
    print(f"RECEIVER_BUILD_NOT_FOUND {built}", file=sys.stderr)
    raise SystemExit(2)

shutil.copy2(built, dest)
print(f"RECEIVER_024_READY {dest}")
print("FEATURE: real cargo/python/git stdout/stderr now streams inside VERTEX SHELL.")
