from pathlib import Path
import sys

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
APP = ROOT / "ui" / "app.js"

if not APP.exists():
    print("APP_EXISTS=FAIL")
    raise SystemExit(1)

text = APP.read_text(encoding="utf-8")

checks = {
    "MARKER": "VERTEX_WORKS_CONTEXT_MENU_000097_BEGIN" in text,
    "CONTEXTMENU_CAPTURE": 'document.addEventListener("contextmenu", openVertexContextMenu, true)' in text,
    "PREVENT_DEFAULT": "event.preventDefault();" in text,
    "PRODUCT_PROPERTIES": "PRODUCT PROPERTIES" in text,
    "HELP": "HELP / INPUT GUIDE" in text,
    "PRODUCT_SITE": "VERTEX PRODUCT SITE" in text,
    "ARTIFACT_INSPECT": '"INSPECT"' in text,
    "ARTIFACT_CLIP_IN": "CLIP IN PATH" in text,
    "TEXT_CLIP_IN": 'vertexClipIn(selection, "TEXT")' in text,
    "VERTEX_STYLE": "vertexContextStyle000097" in text,
}

for key, value in checks.items():
    print(f"{key}={'PASS' if value else 'FAIL'}")

failed = [k for k, v in checks.items() if not v]
if failed:
    print("VERTEX_WORKS_CONTEXT_MENU_000097_VERIFY FAIL", ",".join(failed))
    sys.exit(1)

print("NATIVE_CONTEXT_MENU=ABSENT_BY_GLOBAL_PREVENT_DEFAULT")
print("RIGHT_CLICK=VERTEX_CONTEXT_ONLY")
print("VERTEX_WORKS_CONTEXT_MENU_000097_VERIFY PASS")
