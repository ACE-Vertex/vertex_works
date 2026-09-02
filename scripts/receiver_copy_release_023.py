from pathlib import Path
import shutil
import sys

root = Path.cwd()
built = root / "src-tauri" / "target" / "release" / "vertex-receiver.exe"
dest = root / "VertexReceiver_0.2.3.exe"

if not built.exists():
    print(f"RECEIVER_BUILD_NOT_FOUND {built}", file=sys.stderr)
    raise SystemExit(2)

shutil.copy2(built, dest)
print(f"RECEIVER_023_READY {dest}")
print("FEATURE: Incoming Artifact cards show applied / verified / rollback history.")
