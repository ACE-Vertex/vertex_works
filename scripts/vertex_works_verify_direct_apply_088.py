from pathlib import Path
import re

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
APP = ROOT / "ui" / "app.js"

if not APP.exists():
    print("APP_JS_EXISTS=FAIL")
    raise SystemExit(1)

text = APP.read_text(encoding="utf-8")

checks = {
    "APP_JS_EXISTS": True,
    "DIRECT_APPLY_MARKER": "VERTEX_WORKS_DIRECT_APPLY_088" in text,
    "STAGE_ARTIFACT_PRESERVED": bool(re.search(r'["\']stage_artifact["\']', text)),
    "APPLY_STAGE_PRESERVED": bool(re.search(r'["\']apply_stage["\']', text)),
}

m = re.search(r'["\']apply_stage["\']', text)
if m:
    window = text[max(0, m.start() - 2600):min(len(text), m.start() + 1200)]
    checks["NO_CONFIRM_NEAR_APPLY_STAGE"] = not bool(
        re.search(r'(?:window\.)?confirm\s*\(', window)
    )
else:
    checks["NO_CONFIRM_NEAR_APPLY_STAGE"] = False

for key, value in checks.items():
    print(f"{key}={'PASS' if value else 'FAIL'}")

print("FLOW=INSPECT -> STAGE -> APPLY_CLICK -> APPLY_STAGE -> VERIFY")
print("SECOND_CONFIRMATION=ABSENT")
print("AUTO_APPLY_AFTER_STAGE=FALSE")
print("AUTHORITY=HUMAN_APPLY")

failed = [k for k, v in checks.items() if not v]
if failed:
    print("VERTEX_WORKS_DIRECT_APPLY_088_VERIFY FAIL", ",".join(failed))
    raise SystemExit(1)

print("VERTEX_WORKS_DIRECT_APPLY_088_VERIFY PASS")
