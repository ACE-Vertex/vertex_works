from pathlib import Path
import json

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
INDEX = ROOT / "ui" / "index.html"
ORANGE = ROOT / "ui" / "vertex-works-orange.css"
CURRENT = ROOT / "current.json"
APP = ROOT / "ui" / "app.js"
ICON = ROOT / "ui" / "assets" / "brand" / "vertex-works-app-icon.png"
ROOT_EXE = ROOT / "VertexWorks.exe"

def emit(name, ok):
    print(f"{name}={'PASS' if ok else 'FAIL'}")
    return ok

index = INDEX.read_text(encoding="utf-8", errors="replace") if INDEX.exists() else ""
css = ORANGE.read_text(encoding="utf-8", errors="replace") if ORANGE.exists() else ""
app = APP.read_text(encoding="utf-8", errors="replace") if APP.exists() else ""
current = json.loads(CURRENT.read_text(encoding="utf-8")) if CURRENT.exists() else {}

release_value = current.get("release_exe") or current.get("executable") or ""
release = Path(release_value) if release_value else Path("__missing__")

checks = [
    emit("ROOT_ENTRY_EXISTS", ROOT_EXE.exists()),
    emit("HTML_LANG_EN", '<html lang="en"' in index),
    emit("PRODUCT_CODE_VW_HTML", 'data-product="VW"' in index),
    emit("ORANGE_CSS_LINKED", 'vertex-works-orange.css' in index),
    emit("ORANGE_CSS_EXISTS", ORANGE.exists()),
    emit("ORANGE_ACCENT", '#ff7a18' in css.lower()),
    emit("VW_ICON_EXISTS", ICON.exists()),
    emit("VW_ICON_IN_UI", 'assets/brand/vertex-works-app-icon.png' in index),
    emit("OLD_GENERIC_MARK_NOT_IN_INDEX", 'assets/vertex-project-mark.svg' not in index),
    emit("ENGLISH_LOCK_PRESENT", 'vertexWorksEnglishLock076' in index),
    emit("LANGUAGE_HOOKS_HIDDEN", '.legacy-language-hooks' in css),
    emit("RAY_PRESERVED", 'id="rayNavBtn"' in index),
    emit("FORGE_PRESERVED", 'id="forgeNavBtn"' in index),
    emit("VERA_HANDOFF_PRESERVED", ('vera' in index.lower() or 'vera' in app.lower())),
    emit("CURRENT_THEME_ORANGE", current.get("theme") == "ORANGE"),
    emit("CURRENT_PRODUCT_VW", current.get("product_code") == "VW"),
    emit("CURRENT_RELEASE_EXISTS", release.exists()),
    emit("IMMUTABLE_BUILD_PATH", "\\versions\\0.5.0\\builds\\" in str(release).lower()),
    emit(
        "RESPONSIVE_LAYER",
        '@media (max-width: 1700px)' in css
        and '@media (max-width: 1280px)' in css
    ),
]

if not all(checks):
    raise SystemExit("VERTEX_WORKS_ORANGE_ENGLISH_076_VERIFY FAIL")

print("VERTEX_WORKS_ORANGE_ENGLISH_076_VERIFY PASS")
