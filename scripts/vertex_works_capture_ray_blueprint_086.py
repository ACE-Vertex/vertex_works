from pathlib import Path
import hashlib
import re
import sys
import json

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
UI = ROOT / "ui"
CURRENT = ROOT / "current.json"

def safe_print(value=""):
    text = str(value)
    sys.stdout.write(text.encode("ascii", "backslashreplace").decode("ascii") + "\n")

def read(path):
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

def sha(path):
    if not path.exists():
        return "MISSING"
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def capture_hits(path, label, regex, radius=3, max_blocks=60):
    if not path.exists():
        safe_print(f"{label}_FILE_MISSING={path}")
        return
    lines = read(path).splitlines()
    hits = [i for i, line in enumerate(lines) if regex.search(line)]
    safe_print(f"\n=== {label} :: {path.relative_to(ROOT)} HITS={len(hits)} ===")
    if not hits:
        safe_print("NO_MATCH")
        return
    blocks = 0
    last_end = -1
    for idx in hits:
        if blocks >= max_blocks:
            safe_print("...TRUNCATED...")
            break
        start = max(0, idx-radius)
        end = min(len(lines), idx+radius+1)
        if start <= last_end:
            continue
        for j in range(start, end):
            safe_print(f"{j+1:5}: {lines[j]}")
        safe_print("---")
        last_end = end-1
        blocks += 1

safe_print("VERTEX WORKS RAY / BLUEPRINT CAPABILITY PROBE 000086")
safe_print("MODE=READ_ONLY")
safe_print("PRODUCTION_UI_MUTATION=FALSE")
safe_print("PURPOSE=RAY_THEME_CONSISTENCY + BLUEPRINT_RELATION + GRID_DRAG_CAPABILITY")
safe_print("POLICY=NO_FAKE_EDITOR / NO_DECORATIVE_CARDS")
safe_print("TRANSPORT=ASCII_ESCAPED")

files = {
    "INDEX": UI / "index.html",
    "XRAY_JS": UI / "scoped-xray.js",
    "XRAY_CSS": UI / "scoped-xray.css",
    "APP_JS": UI / "app.js",
    "STYLE": UI / "style.css",
    "THEME": UI / "vertex-theme.css",
    "ORANGE": UI / "vertex-works-orange.css",
    "FACTORY_JS": UI / "vertex-works-factory-kernel.js",
    "FACTORY_CSS": UI / "vertex-works-factory-kernel.css",
}
for name, path in files.items():
    safe_print(f"FILE_{name}={path.relative_to(ROOT) if path.exists() else 'MISSING'}")
    safe_print(f"SHA256_{name}={sha(path)}")

index = read(files["INDEX"])
xjs = read(files["XRAY_JS"])
xcss = read(files["XRAY_CSS"])
app = read(files["APP_JS"])
orange = read(files["ORANGE"])
factory_css = read(files["FACTORY_CSS"])

relation_ids = [
    "blueprintAddRelationBtn", "relationEditor", "relationFrom", "relationTo",
    "relationType", "relationStrength", "relationConfidence", "relationDependency",
    "relationCorrelation", "relationSuperiority", "relationNote",
    "relationSaveBtn", "relationDeleteBtn"
]

safe_print("\n=== RELATION UI CONTRACT ===")
all_relation_controls = True
for ident in relation_ids:
    needle = 'id="' + ident + '"'
    present = needle in index
    all_relation_controls = all_relation_controls and present
    safe_print("UI_" + ident + "=" + ("PRESENT" if present else "ABSENT"))
safe_print("RELATION_UI_CONTRACT=" + ("PRESENT" if all_relation_controls else "INCOMPLETE"))
safe_print("NOTE=UI_CONTRACT_IS_NOT_RUNTIME_PROOF")

combined_js = xjs + "\n" + app
tokens = {
    "BLUEPRINT_ADD_RELATION_REF": r"\bblueprintAddRelationBtn\b",
    "RELATION_SAVE_REF": r"\brelationSaveBtn\b",
    "RELATION_DELETE_REF": r"\brelationDeleteBtn\b",
    "RELATION_EDITOR_REF": r"\brelationEditor\b",
    "RELATION_FROM_REF": r"\brelationFrom\b",
    "RELATION_TO_REF": r"\brelationTo\b",
    "RELATION_TYPE_REF": r"\brelationType\b",
    "RELATION_STORAGE": r"localStorage|sessionStorage|indexedDB|JSON\.stringify|JSON\.parse",
    "RELATION_RENDER": r"renderRelation|renderRelations|relation.*(?:line|edge|path)|(?:line|edge|path).*relation",
    "SVG_LINE_PATH": r"createElementNS|<svg|<line|<path|stroke",
    "POINTER_DOWN": r"pointerdown|mousedown|dragstart",
    "POINTER_MOVE": r"pointermove|mousemove|\bdrag\b",
    "POINTER_UP": r"pointerup|mouseup|drop|dragend",
    "POINTER_CAPTURE": r"setPointerCapture|releasePointerCapture",
    "POSITION_WRITE": r"style\.(?:left|top|transform)|translate3?d?\(|translate\(",
    "POSITION_READ": r"getBoundingClientRect|offsetLeft|offsetTop|clientX|clientY",
    "GRID_TOKEN": r"\bgrid\b|grid-template|gridSize|grid_size|layoutGrid|layout_grid",
    "SNAP_TOKEN": r"\bsnap\b|snapToGrid|snap_to_grid|Math\.round\([^)]*/[^)]*\)",
    "UNDO_TOKEN": r"\bundo\b|\bredo\b|history",
}
safe_print("\n=== BLUEPRINT IMPLEMENTATION TOKEN COUNTS ===")
counts = {}
for label, pat in tokens.items():
    counts[label] = len(re.findall(pat, combined_js, flags=re.I))
    safe_print(f"{label}={counts[label]}")

drag_evidence = (
    counts["POINTER_DOWN"] > 0 and
    counts["POINTER_MOVE"] > 0 and
    counts["POINTER_UP"] > 0 and
    counts["POSITION_WRITE"] > 0
)
grid_evidence = counts["GRID_TOKEN"] > 0 and counts["SNAP_TOKEN"] > 0
relation_binding_evidence = (
    counts["BLUEPRINT_ADD_RELATION_REF"] > 0 and
    counts["RELATION_SAVE_REF"] > 0 and
    counts["RELATION_DELETE_REF"] > 0 and
    counts["RELATION_FROM_REF"] > 0 and
    counts["RELATION_TO_REF"] > 0
)

safe_print("\n=== CAPABILITY GATE (STATIC EVIDENCE ONLY) ===")
safe_print(f"RELATION_BINDING_STATIC_EVIDENCE={'FOUND' if relation_binding_evidence else 'NOT_FOUND'}")
safe_print(f"CARD_DRAG_STATIC_EVIDENCE={'FOUND' if drag_evidence else 'NOT_FOUND'}")
safe_print(f"LAYOUT_GRID_SNAP_STATIC_EVIDENCE={'FOUND' if grid_evidence else 'NOT_FOUND'}")
safe_print("RUNTIME_BEHAVIOR_VERIFIED=NO")
safe_print("POLICY_IF_NO_GRID_DRAG=REMOVE_OR_HIDE_EDITOR_CARDS")
safe_print("POLICY_RELATION_ENGINE=PRESERVE_AND_VERIFY_BEFORE_UI_REMOVAL")
safe_print("POLICY_THEME=VW_ORANGE_CHROME + SEMANTIC_RELATION_COLORS")

theme_text = xcss + "\n" + orange + "\n" + factory_css
orange_hits = len(re.findall(r"#(?:ff[5-9a-f][0-9a-f]{3}|f[0-9a-f]{5})|rgba?\(\s*255\s*,\s*(?:8[0-9]|9[0-9]|1[0-6][0-9])\s*,", theme_text, re.I))
blue_hits = len(re.findall(r"#(?:[0-4][0-9a-f]{1,3}ff|[0-4][0-9a-f]{4}ff)|rgba?\(\s*(?:0|[0-8]?[0-9])\s*,\s*(?:1[0-9]{2}|2[0-4][0-9])\s*,\s*255\s*,", theme_text, re.I))
cyan_var_hits = len(re.findall(r"--(?:cyan|blue|xray|ray-blue)|var\(--(?:cyan|blue)", theme_text, re.I))
orange_var_hits = len(re.findall(r"--(?:orange|vw-|works-|vertex-orange)|var\(--(?:orange|vw-|works-|vertex-orange)", theme_text, re.I))
safe_print("\n=== RAY THEME STATIC AUDIT ===")
safe_print(f"ORANGE_LITERAL_APPROX={orange_hits}")
safe_print(f"BLUE_LITERAL_APPROX={blue_hits}")
safe_print(f"CYAN_BLUE_VAR_APPROX={cyan_var_hits}")
safe_print(f"ORANGE_WORKS_VAR_APPROX={orange_var_hits}")
safe_print("THEME_VERDICT=MANUAL_REVIEW_REQUIRED")
safe_print("NOTE=RELATION_STATUS_COLORS_MAY_REMAIN_SEMANTIC")

capture_hits(files["INDEX"], "INDEX_BLUEPRINT_RELATION", re.compile(
    r"blueprint|relation|xrayMap|xray-grid|xray-topbar|xray-brand", re.I), radius=2, max_blocks=80)

capture_hits(files["XRAY_JS"], "XRAY_JS_RELATION", re.compile(
    r"blueprint|relationFrom|relationTo|relationType|relationStrength|relationConfidence|"
    r"relationDependency|relationCorrelation|relationSuperiority|relationNote|"
    r"relationSaveBtn|relationDeleteBtn|addRelation", re.I), radius=4, max_blocks=100)

capture_hits(files["XRAY_JS"], "XRAY_JS_DRAG_GRID", re.compile(
    r"pointerdown|pointermove|pointerup|mousedown|mousemove|mouseup|dragstart|dragend|drop|"
    r"setPointerCapture|style\.left|style\.top|style\.transform|getBoundingClientRect|"
    r"\bgrid\b|\bsnap\b|undo|redo", re.I), radius=4, max_blocks=100)

capture_hits(files["XRAY_CSS"], "XRAY_CSS_THEME_GRID_CARD", re.compile(
    r"blueprint|xray-map|xray-node|blueprint-node|card|grid-template|background|border|"
    r"#[0-9a-fA-F]{3,8}|rgba?\(", re.I), radius=2, max_blocks=100)

capture_hits(files["ORANGE"], "ORANGE_OVERRIDE_RAY", re.compile(
    r"xray|ray-|blueprint|relation|--vw|--orange|#[0-9a-fA-F]{3,8}|rgba?\(", re.I),
    radius=2, max_blocks=80)

if CURRENT.exists():
    safe_print("\n=== CURRENT.JSON ===")
    try:
        cur = json.loads(read(CURRENT))
        for key in ("version", "current", "release", "ui_phase", "product_code", "theme"):
            if key in cur:
                safe_print(f"CURRENT_{key.upper()}={cur[key]}")
    except Exception as e:
        safe_print(f"CURRENT_JSON_PARSE_FAIL={e}")

safe_print("\nDECISION_GATE:")
safe_print("1 RELATION_RUNTIME must be proven before removing relation surfaces.")
safe_print("2 GRID+SNAP+DRAG absent => cards are not accepted as editor UI.")
safe_print("3 RAY chrome should converge on VW Orange; relation/status colors stay semantic.")
safe_print("4 Next mutation VRA must be based on this exact current-source capture.")
safe_print("\nVERTEX_WORKS_RAY_BLUEPRINT_PROBE_086 PASS")
