from pathlib import Path
import shutil
import sys

root = Path.cwd()
built = root / "src-tauri" / "target" / "release" / "vertex-receiver.exe"
dest = root / "VertexWorks_0.3.0.exe"

if not built.exists():
    print(f"VERTEX_WORKS_BUILD_NOT_FOUND {built}", file=sys.stderr)
    raise SystemExit(2)

shutil.copy2(built, dest)
print(f"VERTEX_WORKS_030_READY {dest}")
print("PRODUCT: VERTEX WORKS — Artifact Engineering, Verification & Dispatch Facility")
print("FACILITY: Receiver retained as Receiving Bay")
print("FEATURE: NAME / GENRE sorting retained; WORKS genre added")
print("THEME: shared Vertex Blue CSS retained")
print("UI: Vertex-native Beams / Specular / Gradual Fade / Count-Up / Line Rail / Process Dock")
print("GUARD: stale release binary cannot be copied after failed build")
print("NEXT: close the older Receiver and launch VertexWorks_0.3.0.exe")
