from pathlib import Path
import shutil,sys
root=Path.cwd(); built=root/'src-tauri'/'target'/'release'/'vertex-receiver.exe'; dest=root/'VertexWorks_0.4.1.exe'
if not built.exists(): print(f'VERTEX_WORKS_BUILD_NOT_FOUND {built}',file=sys.stderr); raise SystemExit(2)
shutil.copy2(built,dest)
print(f'VERTEX_WORKS_041_READY {dest}')
print('PRODUCT: VERTEX WORKS 0.4.1')
print('FEATURE: PROJECT X-RAY FULL RECURSIVE TREE')
print('MODE: READ-ONLY PROJECT ANALYSIS')
print('EXPLORER: ALL VISIBLE PROJECT FOLDERS / LAZY EXPANSION')
print('IGNORED: GENERATED/CACHE BOUNDARIES SHOWN BUT NOT DESCENDED')
print('VERA: CLIP TO VERA PRESERVED')
print('FINAL: VERTEX WORKS 0.4.1 READY')
