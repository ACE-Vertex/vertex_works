from pathlib import Path
import re
import shutil
import time

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
APP = ROOT / "ui" / "app.js"
BACKUP_ROOT = ROOT / "MIGRATION_BACKUPS" / "DIRECT_APPLY_088"

def fail(message: str):
    print(f"DIRECT_APPLY_088_FAIL={message}")
    raise SystemExit(1)

if not APP.exists():
    fail(f"APP_JS_MISSING:{APP}")

text = APP.read_text(encoding="utf-8")

stage_hits = [m.start() for m in re.finditer(r'["\']stage_artifact["\']', text)]
apply_hits = [m.start() for m in re.finditer(r'["\']apply_stage["\']', text)]

print("VERTEX WORKS DIRECT APPLY 000088")
print(f"ROOT={ROOT}")
print(f"STAGE_ARTIFACT_CALLS={len(stage_hits)}")
print(f"APPLY_STAGE_CALLS={len(apply_hits)}")

if len(stage_hits) < 1:
    fail("STAGE_ARTIFACT_CALL_NOT_FOUND")
if len(apply_hits) != 1:
    fail(f"EXPECTED_ONE_APPLY_STAGE_CALL_FOUND_{len(apply_hits)}")

apply_pos = apply_hits[0]
window_start = max(0, apply_pos - 2600)
window_end = min(len(text), apply_pos + 1200)
window = text[window_start:window_end]

patterns = [
    re.compile(
        r'if\s*\(\s*!\s*(?:window\.)?confirm\s*\((?P<msg>[\s\S]*?)\)\s*\)\s*(?:\{\s*)?return(?:\s+false)?\s*;?\s*(?:\})?',
        re.MULTILINE,
    ),
    re.compile(
        r'if\s*\(\s*(?:window\.)?confirm\s*\((?P<msg>[\s\S]*?)\)\s*===\s*false\s*\)\s*(?:\{\s*)?return(?:\s+false)?\s*;?\s*(?:\})?',
        re.MULTILINE,
    ),
]

matches = []
for p in patterns:
    for m in p.finditer(window):
        matches.append((m.start(), m.end(), m.group(0)))

matches.sort(key=lambda x: (x[0], x[1]))
dedup = []
for item in matches:
    if not dedup or item[0] >= dedup[-1][1]:
        dedup.append(item)

direct_confirm_count = len(re.findall(r'(?:window\.)?confirm\s*\(', window))
global_confirm_count = len(re.findall(r'(?:window\.)?confirm\s*\(', text))

print(f"APPLY_HANDLER_CONFIRM_CALLS={direct_confirm_count}")
print(f"GLOBAL_CONFIRM_CALLS={global_confirm_count}")
print(f"REMOVABLE_CONFIRM_GUARDS={len(dedup)}")

if len(dedup) != 1:
    print("APPLY_HANDLER_CONTEXT_BEGIN")
    safe = window.encode("ascii", "backslashreplace").decode("ascii")
    print(safe)
    print("APPLY_HANDLER_CONTEXT_END")
    fail("CONFIRM_GUARD_NOT_UNIQUELY_IDENTIFIED")

start, end, _removed = dedup[0]
abs_start = window_start + start
abs_end = window_start + end

marker = (
    "// VERTEX_WORKS_DIRECT_APPLY_088: APPLY click is the explicit HUMAN_APPLY gate; "
    "redundant second confirmation removed.\n"
)

new_text = text[:abs_start] + marker + text[abs_end:]

if re.search(r'["\']stage_artifact["\']', new_text) is None:
    fail("STAGE_FLOW_WOULD_BE_REMOVED")
if re.search(r'["\']apply_stage["\']', new_text) is None:
    fail("APPLY_FLOW_WOULD_BE_REMOVED")

new_apply_pos = re.search(r'["\']apply_stage["\']', new_text).start()
new_window = new_text[max(0, new_apply_pos - 2600):min(len(new_text), new_apply_pos + 1200)]
if re.search(r'(?:window\.)?confirm\s*\(', new_window):
    fail("SECOND_CONFIRM_STILL_PRESENT_NEAR_APPLY")

stamp = time.strftime("%Y%m%d-%H%M%S")
backup = BACKUP_ROOT / stamp / "ui" / "app.js"
backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(APP, backup)

# pathlib.Path.write_text() has no newline= parameter on the user's Python.
# Use open(..., newline="\n") explicitly so Works remains LF-stable on Windows.
with APP.open("w", encoding="utf-8", newline="\n") as f:
    f.write(new_text)

print(f"BACKUP={backup}")
print("STAGE_FLOW=PRESERVED")
print("APPLY_BUTTON_GATE=PRESERVED")
print("POST_APPLY_CONFIRMATION=REMOVED")
print("AUTO_APPLY_AFTER_STAGE=FALSE")
print("HUMAN_APPLY_AUTHORITY=PRESERVED")
print("VERTEX_WORKS_DIRECT_APPLY_088_SOURCE_PATCH=PASS")
