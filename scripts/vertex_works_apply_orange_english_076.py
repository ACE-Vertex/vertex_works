from pathlib import Path
import json
import hashlib
import shutil
import subprocess
import sys
from datetime import datetime

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
UI = ROOT / "ui"
INDEX = UI / "index.html"
APP = UI / "app.js"
ORANGE = UI / "vertex-works-orange.css"
CURRENT = ROOT / "current.json"
CARGO = ROOT / "src-tauri" / "Cargo.toml"
RELEASE_EXE = ROOT / "src-tauri" / "target" / "release" / "vertex-receiver.exe"
BRAND_ICON = UI / "assets" / "brand" / "vertex-works-app-icon.png"
WORDMARK = UI / "assets" / "brand" / "vertex-works-wordmark.png"
VERSION = "0.5.0"

ORANGE_CSS = '/* VERTEX WORKS 000076 - VW ORANGE WORKSPACE\n   Product identity: VW / Orange\n   Dark manufacturing surface; orange is action/energy, not decoration.\n*/\n:root,\n:root[data-theme="vertex"],\n:root[data-product="VW"] {\n  --vertex-bg-deep: #050403;\n  --vertex-bg-shell: #080604;\n  --vertex-bg-panel: #0d0a07;\n  --vertex-bg-panel-raised: #15100b;\n  --vertex-bg-inset: #090603;\n  --vertex-bg-hover: #21150b;\n  --vertex-line: #342313;\n  --vertex-line-bright: #63401e;\n  --vertex-text: #e9e0d6;\n  --vertex-text-muted: #9e8d7d;\n  --vertex-text-faint: #62564a;\n  --vertex-accent: #ff7a18;\n  --vertex-accent-bright: #ffad55;\n  --vertex-accent-soft: #3a1c08;\n  --vertex-accent-rgb: 255, 122, 24;\n  --vertex-header-top: #171009;\n  --vertex-header-bottom: #0a0704;\n  --vertex-status-top: #311807;\n  --vertex-status-bottom: #1e0f05;\n\n  /* Compatibility aliases used by the existing Ray / Forge CSS. */\n  --blue: #ff7a18;\n  --blue-bright: #ffad55;\n  --blue-soft: #3a1c08;\n  --cyan: #ff7a18;\n  --cyan2: #ffad55;\n  --accent: #ff7a18;\n  --accent-rgb: 255, 122, 24;\n  --amber: #ff9a3d;\n}\n\nhtml, body {\n  min-width: 0;\n  background:\n    radial-gradient(circle at 52% -20%, rgba(255,122,24,.075), transparent 38%),\n    linear-gradient(180deg, #070503 0%, #030303 100%);\n}\n\n.vertex-mode-bar,\n.xray-topbar,\n.command-deck {\n  border-color: rgba(255,122,24,.22) !important;\n  background: linear-gradient(180deg, rgba(27,17,9,.96), rgba(8,6,4,.96)) !important;\n  box-shadow: 0 10px 32px rgba(0,0,0,.22);\n}\n\n.mode-brand img,\n.xray-brand img {\n  width: 34px;\n  height: 34px;\n  border-radius: 8px;\n  object-fit: cover;\n  box-shadow:\n    0 0 0 1px rgba(255,173,85,.24),\n    0 0 20px rgba(255,122,24,.14);\n}\n\n.works-mark .vertex-project-mark {\n  width: 42px;\n  height: 42px;\n  border-radius: 9px;\n  object-fit: cover;\n  filter: none !important;\n}\n\n.mode-switch button.active,\n.rail-item.active,\n.xray-button.primary,\n.xray-chip.active {\n  border-color: rgba(255,122,24,.58) !important;\n  color: #ffd4ab !important;\n  background: linear-gradient(180deg, rgba(255,122,24,.18), rgba(100,45,8,.16)) !important;\n  box-shadow:\n    inset 0 0 0 1px rgba(255,173,85,.06),\n    0 0 18px rgba(255,122,24,.08) !important;\n}\n\n.mode-index,\n.xray-live,\n.works-online,\n.xray-state,\n.brand-block h1 span,\n.works-mark .mark-dot {\n  color: #ff9a3d !important;\n}\n\n.xray-live i,\n.works-mark .mark-dot {\n  background: #ff7a18 !important;\n  box-shadow: 0 0 12px rgba(255,122,24,.72) !important;\n}\n\n.xray-panel,\n.works-card,\n.metric-card,\n.terminal-log,\n.receiving-bay,\n.inspection-bay,\n.staging-bay,\n.evidence-bay,\n.return-lane {\n  border-color: rgba(255,122,24,.13) !important;\n}\n\n.xray-panel:hover,\n.works-card:hover {\n  border-color: rgba(255,122,24,.24) !important;\n}\n\n.legacy-language-hooks {\n  display: none !important;\n}\n\n.mode-brand,\n.mode-switch,\n.vertex-mode-bar,\n.xray-grid,\n.xray-panel,\n.works-shell,\n.works-main,\n.command-deck,\n.brand-block {\n  min-width: 0;\n}\n\n/* Compress chrome before semantic content. */\n@media (max-width: 1700px) {\n  .mode-switch button em { display: none; }\n  .mode-switch button { min-width: 72px; }\n  .mode-brand strong { font-size: clamp(10px, .8vw, 13px); }\n}\n\n@media (max-width: 1280px) {\n  .vertex-mode-bar { gap: 8px; padding-inline: 8px; }\n  .mode-brand small { display: none; }\n  .xray-brand span { display: none; }\n  .command-deck { gap: 10px; }\n}\n'
ENGLISH_LOCK_SCRIPT = '  <script id="vertexWorksEnglishLock076">\n  (() => {\n    const lockEnglish = () => {\n      document.documentElement.lang = "en";\n      document.documentElement.dataset.product = "VW";\n      document.documentElement.dataset.productTheme = "orange";\n      const en = document.getElementById("langEnBtn");\n      if (en && !en.dataset.vwEnglishLocked) {\n        en.dataset.vwEnglishLocked = "1";\n        try { en.click(); } catch (_) {}\n      }\n    };\n    if (document.readyState === "loading") {\n      document.addEventListener(\n        "DOMContentLoaded",\n        () => requestAnimationFrame(lockEnglish),\n        { once: true }\n      );\n    } else {\n      requestAnimationFrame(lockEnglish);\n    }\n  })();\n  </script>\n'

def safe_print(value=""):
    text = str(value)
    sys.stdout.write(text.encode("ascii", "backslashreplace").decode("ascii") + "\n")

def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def run(args):
    safe_print("RUN " + " ".join(map(str, args)))
    cp = subprocess.run(args, text=True, capture_output=True)
    if cp.stdout:
        safe_print(cp.stdout)
    if cp.stderr:
        safe_print(cp.stderr)
    if cp.returncode != 0:
        raise RuntimeError("COMMAND_FAILED " + " ".join(map(str, args)))

required = [ROOT, UI, INDEX, APP, CURRENT, CARGO, BRAND_ICON, WORDMARK]
missing = [str(x) for x in required if not x.exists()]
if missing:
    raise SystemExit("REQUIRED_MISSING " + " | ".join(missing))

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = ROOT / "MIGRATION_BACKUPS" / "UI_ORANGE_ENGLISH_076" / stamp
backup.mkdir(parents=True, exist_ok=True)

backup_index = backup / "index.html"
backup_current = backup / "current.json"
backup_orange = backup / "vertex-works-orange.css"
shutil.copy2(INDEX, backup_index)
shutil.copy2(CURRENT, backup_current)
orange_existed = ORANGE.exists()
if orange_existed:
    shutil.copy2(ORANGE, backup_orange)

safe_print("VERTEX WORKS ORANGE WORKSPACE / ENGLISH LOCK 000076")
safe_print("ROOT=" + str(ROOT))
safe_print("BACKUP=" + str(backup))
safe_print("MODE=FAIL_CLOSED")

original_index = INDEX.read_text(encoding="utf-8")
index = original_index

anchors = [
    '<html lang="ja" data-theme="vertex">',
    '<link rel="stylesheet" href="scoped-xray.css" />',
    'assets/vertex-project-mark.svg',
    'id="langJaBtn"',
    'id="langEnBtn"',
    'id="rayNavBtn"',
    'id="forgeNavBtn"',
]
for anchor in anchors:
    if anchor not in index:
        raise RuntimeError("SOURCE_ANCHOR_MISSING " + anchor)

index = index.replace(
    '<html lang="ja" data-theme="vertex">',
    '<html lang="en" data-theme="vertex" data-product="VW" data-product-theme="orange">'
)

orange_link = '<link rel="stylesheet" href="vertex-works-orange.css" />'
if orange_link not in index:
    index = index.replace(
        '<link rel="stylesheet" href="scoped-xray.css" />',
        '<link rel="stylesheet" href="scoped-xray.css" />\n  ' + orange_link
    )

index = index.replace(
    'assets/vertex-project-mark.svg',
    'assets/brand/vertex-works-app-icon.png'
)

direct_replacements = {
    'アーティファクト工学 · 検証 · ディスパッチ':
        'ARTIFACT ENGINEERING · VERIFICATION · DISPATCH',
    '観測・比較': 'OBSERVE / COMPARE',
    '受信・施工': 'RECEIVE / BUILD',
    '表示設定': 'DISPLAY',
    '表示言語': 'INTERFACE LANGUAGE',
    '既定は日本語です': 'VERTEX WORKS runs English-only',
    '設定はこの端末のVERTEX WORKSに保存されます。':
        'Display settings are stored on this workstation.',
}
for old, new in direct_replacements.items():
    index = index.replace(old, new)

lang_row_marker = (
    '<div class="language-switch"><button id="langJaBtn" class="active">日本語</button>'
    '<button id="langEnBtn">English</button></div>'
)
if lang_row_marker in index:
    index = index.replace(
        lang_row_marker,
        '<div class="language-switch legacy-language-hooks" aria-hidden="true">'
        '<button id="langJaBtn" tabindex="-1">JA</button>'
        '<button id="langEnBtn" tabindex="-1">EN</button>'
        '</div>'
    )
else:
    if 'class="language-switch"' not in index:
        raise RuntimeError("LANGUAGE_SWITCH_STRUCTURE_MISSING")
    index = index.replace(
        'class="language-switch"',
        'class="language-switch legacy-language-hooks"',
        1
    )

if 'id="vertexWorksEnglishLock076"' not in index:
    if "</body>" not in index:
        raise RuntimeError("BODY_END_MISSING")
    index = index.replace(
        "</body>",
        "\n" + ENGLISH_LOCK_SCRIPT + "\n</body>",
        1
    )

try:
    INDEX.write_text(index, encoding="utf-8", newline="\n")
    ORANGE.write_text(ORANGE_CSS, encoding="utf-8", newline="\n")

    check = INDEX.read_text(encoding="utf-8")
    static_checks = {
        "HTML_LANG_EN": '<html lang="en"' in check,
        "PRODUCT_VW": 'data-product="VW"' in check,
        "ORANGE_THEME_LINK": 'vertex-works-orange.css' in check,
        "OLD_MARK_REMOVED_FROM_INDEX": 'assets/vertex-project-mark.svg' not in check,
        "VW_ICON_REFERENCED": 'assets/brand/vertex-works-app-icon.png' in check,
        "ENGLISH_LOCK_PRESENT": 'vertexWorksEnglishLock076' in check,
        "RAY_PRESERVED": 'id="rayNavBtn"' in check,
        "FORGE_PRESERVED": 'id="forgeNavBtn"' in check,
        "VERA_HANDOFF_PRESERVED": (
            'vera' in check.lower()
            or 'vera' in APP.read_text(encoding="utf-8", errors="ignore").lower()
        ),
    }
    for name, ok in static_checks.items():
        safe_print(f"{name}={'PASS' if ok else 'FAIL'}")
    failed = [name for name, ok in static_checks.items() if not ok]
    if failed:
        raise RuntimeError("STATIC_CONTRACT_FAIL " + ",".join(failed))

    css = ORANGE.read_text(encoding="utf-8")
    css_checks = {
        "VW_ORANGE_ACCENT": "#ff7a18" in css.lower(),
        "VW_ORANGE_BRIGHT": "#ffad55" in css.lower(),
        "RESPONSIVE_1700": "@media (max-width: 1700px)" in css,
        "RESPONSIVE_1280": "@media (max-width: 1280px)" in css,
        "LEGACY_LANGUAGE_HIDDEN": ".legacy-language-hooks" in css,
    }
    for name, ok in css_checks.items():
        safe_print(f"{name}={'PASS' if ok else 'FAIL'}")
    failed = [name for name, ok in css_checks.items() if not ok]
    if failed:
        raise RuntimeError("CSS_CONTRACT_FAIL " + ",".join(failed))

    run(["cargo", "fmt", "--manifest-path", str(CARGO), "--", "--check"])
    run(["cargo", "test", "--manifest-path", str(CARGO)])
    run(["cargo", "build", "--release", "--manifest-path", str(CARGO)])

    if not RELEASE_EXE.exists():
        raise RuntimeError("RELEASE_EXE_MISSING " + str(RELEASE_EXE))

    release_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    release_dir = ROOT / "versions" / VERSION / "builds" / release_stamp
    release_dir.mkdir(parents=True, exist_ok=False)
    immutable = release_dir / f"VertexWorks_{VERSION}.exe"
    shutil.copy2(RELEASE_EXE, immutable)
    release_hash = sha256(immutable)

    current = json.loads(CURRENT.read_text(encoding="utf-8"))
    previous_release = current.get("release_exe") or current.get("executable")

    if "release_exe" in current:
        current["release_exe"] = str(immutable)
    elif "executable" in current:
        current["executable"] = str(immutable)
    else:
        current["release_exe"] = str(immutable)

    current["sha256"] = release_hash
    current["version"] = VERSION
    current["updated_at"] = datetime.now().isoformat(timespec="seconds")
    current["product_code"] = "VW"
    current["theme"] = "ORANGE"
    current["ui_phase"] = "ORANGE_WORKSPACE_ENGLISH_LOCK_000076"

    CURRENT.write_text(
        json.dumps(current, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n"
    )

    safe_print("BUILD_TEST=PASS")
    safe_print("NEW_IMMUTABLE_RELEASE=" + str(immutable))
    safe_print("NEW_RELEASE_SHA256=" + release_hash)
    safe_print("PREVIOUS_RELEASE=" + str(previous_release))
    safe_print("CURRENT_JSON_UPDATED=PASS")
    safe_print("PRODUCT_CODE=VW")
    safe_print("THEME=ORANGE")
    safe_print("LANGUAGE_MODE=ENGLISH_LOCK_COMPAT")
    safe_print("NEXT_PHASE=REMOVE_DEAD_I18N_SOURCE_AFTER_RUNTIME_CONFIRMATION")
    safe_print("VERTEX_WORKS_ORANGE_ENGLISH_076 PASS")

except Exception:
    shutil.copy2(backup_index, INDEX)
    shutil.copy2(backup_current, CURRENT)
    if orange_existed:
        shutil.copy2(backup_orange, ORANGE)
    elif ORANGE.exists():
        ORANGE.unlink()
    safe_print("MIGRATION_RESTORED=" + str(backup))
    raise
