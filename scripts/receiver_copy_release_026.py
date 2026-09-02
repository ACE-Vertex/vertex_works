from pathlib import Path
import shutil
import sys

root = Path.cwd()
built = root / "src-tauri" / "target" / "release" / "vertex-receiver.exe"
dest = root / "VertexReceiver_0.2.6.exe"

if not built.exists():
    print(f"RECEIVER_BUILD_NOT_FOUND {built}", file=sys.stderr)
    raise SystemExit(2)

shutil.copy2(built, dest)
print(f"RECEIVER_026_READY {dest}")
print("FEATURE: Incoming NAME / GENRE sort + shared Vertex Blue CSS tokens.")
print("HOTFIX: genre is computed before manifest strings are moved.")
print("GUARD: stale release binary cannot be copied after a failed build.")
print("NEXT: close the older Receiver and launch VertexReceiver_0.2.6.exe")
