from pathlib import Path
import re
import shutil
import time

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
UI = ROOT / "ui"
BACKUP_ROOT = ROOT / "MIGRATION_BACKUPS" / "TYPOGRAPHY_PLUS1PT_000096"
MARKER = "VERTEX_WORKS_TYPOGRAPHY_PLUS1PT_000096"

def fail(message):
    print(f"TYPOGRAPHY_PLUS1PT_000096_FAIL={message}")
    raise SystemExit(1)

if not UI.exists():
    fail(f"UI_DIR_MISSING:{UI}")

targets = sorted(
    [p for p in UI.rglob("*.css") if p.is_file()]
    + [p for p in UI.rglob("*.html") if p.is_file()]
)

if not targets:
    fail("NO_UI_STYLE_TARGETS")

pattern = re.compile(
    r'(?P<prefix>font-size\s*:\s*)'
    r'(?P<value>[0-9]+(?:\.[0-9]+)?(?:px|pt|rem|em))'
    r'(?P<suffix>\s*;)',
    re.IGNORECASE,
)

stamp = time.strftime("%Y%m%d-%H%M%S")
backup_root = BACKUP_ROOT / stamp
modified = []
replacement_count = 0

for path in targets:
    text = path.read_text(encoding="utf-8")

    if MARKER in text:
        print(f"SKIP_ALREADY_PATCHED={path}")
        continue

    def repl(match):
        nonlocal_count[0] += 1
        value = match.group("value")
        return f'{match.group("prefix")}calc({value} + 1pt){match.group("suffix")}'

    nonlocal_count = [0]
    patched = pattern.sub(repl, text)

    if nonlocal_count[0] == 0:
        continue

    rel = path.relative_to(ROOT)
    backup = backup_root / rel
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup)

    marker = f"/* {MARKER}: every explicit simple font-size in this file is +1pt */\n"
    patched = marker + patched

    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(patched)

    modified.append(str(rel))
    replacement_count += nonlocal_count[0]
    print(f"PATCHED={rel} FONT_SIZE_RULES={nonlocal_count[0]}")

if not modified:
    fail("NO_FONT_SIZE_RULES_MODIFIED")

print(f"BACKUP={backup_root}")
print(f"MODIFIED_FILES={len(modified)}")
print(f"FONT_SIZE_RULES_PLUS_1PT={replacement_count}")
print("SCOPE=UI_EXPLICIT_FONT_SIZE_RULES_ONLY")
print("LAYOUT_GEOMETRY=UNCHANGED")
print("COLOR_THEME=UNCHANGED")
print("VERTEX_WORKS_TYPOGRAPHY_PLUS1PT_000096_SOURCE_PATCH=PASS")
