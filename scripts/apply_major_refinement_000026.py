from pathlib import Path
import shutil
import time

WORKS = Path(r"G:\Vertex_Project\Development\vertex_works")
INDEX = WORKS / "ui" / "index.html"
CANONICAL_RS = WORKS / "src-tauri" / "src" / "canonical_registry.rs"
BACKUP = WORKS / "MIGRATION_BACKUPS" / "MAJOR_REFINEMENT_000026" / time.strftime("%Y%m%d-%H%M%S")

if not INDEX.exists():
    raise SystemExit("Works ui/index.html not found")

def backup(path: Path):
    dest = BACKUP / path.relative_to(WORKS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    print(f"BACKUP={dest}")

index = INDEX.read_text(encoding="utf-8")
css = '  <link rel="stylesheet" href="./vertex-works-major-refinement-000026.css">'
js = '  <script src="./vertex-works-major-refinement-000026.js" defer></script>'

changed = False
if "vertex-works-major-refinement-000026.css" not in index:
    if "</head>" not in index:
        raise SystemExit("index head anchor not found")
    if not changed:
        backup(INDEX)
    index = index.replace("</head>", css + "\n</head>", 1)
    changed = True
    print("REFINEMENT_CSS=PATCHED")
else:
    print("REFINEMENT_CSS=ALREADY_PRESENT")

if "vertex-works-major-refinement-000026.js" not in index:
    if "</body>" not in index:
        raise SystemExit("index body anchor not found")
    if not changed:
        backup(INDEX)
    index = index.replace("</body>", js + "\n</body>", 1)
    changed = True
    print("REFINEMENT_JS=PATCHED")
else:
    print("REFINEMENT_JS=ALREADY_PRESENT")

if changed:
    with INDEX.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(index)

# Clean the already-observed 000001 warning without changing behavior.
if CANONICAL_RS.exists():
    raw = CANONICAL_RS.read_text(encoding="utf-8")
    fixed = raw.replace("path::{Path, PathBuf}", "path::PathBuf")
    if fixed != raw:
        backup(CANONICAL_RS)
        with CANONICAL_RS.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(fixed)
        print("CANONICAL_UNUSED_PATH_IMPORT=REMOVED")
    else:
        print("CANONICAL_UNUSED_PATH_IMPORT=NOT_PRESENT")

print("VERTEX_WORKS_MAJOR_REFINEMENT_000026_APPLY=PASS")
