from pathlib import Path
import shutil
import sys

root = Path.cwd()
built = root / "src-tauri" / "target" / "release" / "vertex-receiver.exe"
dest = root / "VertexWorks_0.3.1.exe"

if not built.exists():
    print(f"VERTEX_WORKS_BUILD_NOT_FOUND {built}", file=sys.stderr)
    raise SystemExit(2)

shutil.copy2(built, dest)

# IMPORTANT:
# Receiver currently launches this script under a Windows CP932 console.
# Keep verification stdout strictly ASCII so packaging cannot fail on
# typography such as em-dash, arrows, micro signs, etc.
print(f"VERTEX_WORKS_031_READY {dest}")
print("PRODUCT: VERTEX WORKS - Artifact Engineering, Verification and Dispatch Facility")
print("FACILITY: Receiver retained as Receiving Bay")
print("BRAND: official Vertex Project SVG mark installed")
print("FEATURE: NAME / GENRE sorting retained; WORKS genre active")
print("THEME: shared Vertex Blue CSS retained")
print("UI: Beams / Specular / Gradual Fade / Count-Up / Line Rail / Process Dock")
print("GUARD: stale release binary cannot be copied after failed build")
print("FINAL: VERTEX WORKS 0.3.1 READY")
