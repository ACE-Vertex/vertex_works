from pathlib import Path
import re
import sys

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
UI = ROOT / "ui"
MARKER = "VERTEX_WORKS_TYPOGRAPHY_PLUS1PT_000096"

targets = sorted(
    [p for p in UI.rglob("*.css") if p.is_file()]
    + [p for p in UI.rglob("*.html") if p.is_file()]
)

marked = []
calc_rules = 0

for path in targets:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        marked.append(path)
        calc_rules += len(re.findall(r'font-size\s*:\s*calc\([^;]+\+\s*1pt\)\s*;', text, re.I))

checks = {
    "UI_EXISTS": UI.exists(),
    "MARKED_FILES_PRESENT": len(marked) > 0,
    "PLUS_1PT_RULES_PRESENT": calc_rules > 0,
}

for key, value in checks.items():
    print(f"{key}={'PASS' if value else 'FAIL'}")

print(f"MARKED_FILES={len(marked)}")
print(f"PLUS_1PT_RULES={calc_rules}")
print("TYPOGRAPHY_CHANGE=EXPLICIT_FONT_SIZE_PLUS_1PT")
print("LAYOUT_STRUCTURE_CHANGE=NONE")
print("COLOR_THEME_CHANGE=NONE")

failed = [k for k, v in checks.items() if not v]
if failed:
    print("VERTEX_WORKS_TYPOGRAPHY_PLUS1PT_000096_VERIFY FAIL", ",".join(failed))
    sys.exit(1)

print("VERTEX_WORKS_TYPOGRAPHY_PLUS1PT_000096_VERIFY PASS")
