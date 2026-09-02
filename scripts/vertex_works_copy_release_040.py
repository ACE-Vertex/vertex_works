from pathlib import Path
import shutil,sys
root=Path.cwd(); built=root/"src-tauri"/"target"/"release"/"vertex-receiver.exe"; dest=root/"VertexWorks_0.4.0.exe"
if not built.exists(): print(f"VERTEX_WORKS_BUILD_NOT_FOUND {built}",file=sys.stderr); raise SystemExit(2)
shutil.copy2(built,dest)
print(f"VERTEX_WORKS_040_READY {dest}")
print("PRODUCT: VERTEX WORKS 0.4.0")
print("FEATURE: PROJECT X-RAY OBSERVATORY")
print("MODE: READ-ONLY PROJECT ANALYSIS")
print("OUTCOME: SUCCESS / ERROR / ANALYSIS lanes")
print("VERA: CLIP TO VERA preserved as compact one-click handoff")
print("FORGE: Existing VRA pipeline preserved behind FORGE tab")
print("FINAL: VERTEX WORKS 0.4.0 READY")
