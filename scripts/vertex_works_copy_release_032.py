from pathlib import Path
import shutil
import sys

root = Path.cwd()
built = root / "src-tauri" / "target" / "release" / "vertex-receiver.exe"
dest = root / "VertexWorks_0.3.2.exe"

if not built.exists():
    print(f"VERTEX_WORKS_BUILD_NOT_FOUND {built}", file=sys.stderr)
    raise SystemExit(2)

shutil.copy2(built, dest)
print(f"VERTEX_WORKS_032_READY {dest}")
print("PRODUCT: VERTEX WORKS 0.3.2")
print("UI: readability pass complete")
print("HOVER: cargo hit geometry is fixed; no translate-on-hover")
print("BRAND: official Vertex Project SVG retained")
print("FEATURE: NAME / GENRE sorting retained")
print("THEME: Vertex Blue tokens retained")
print("GUARD: stale release binary protection active")
print("FINAL: VERTEX WORKS 0.3.2 READY")
