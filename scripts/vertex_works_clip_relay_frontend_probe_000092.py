from pathlib import Path
import re
import hashlib

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
APP = ROOT / "ui" / "app.js"
INDEX = ROOT / "ui" / "index.html"
MAIN = ROOT / "src-tauri" / "src" / "main.rs"

def safe_print(value=""):
    text = str(value)
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "backslashreplace").decode("ascii"))

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def emit_match_blocks(title, path, patterns, context=12, max_blocks=24):
    safe_print(f"--- {title} ---")
    if not path.exists():
        safe_print("FOUND=FALSE")
        return 0

    lines = path.read_text(encoding="utf-8").splitlines()
    safe_print(f"FILE={path}")
    safe_print(f"SHA256={sha(path)}")

    hit_lines = []
    for i, line in enumerate(lines):
        if any(re.search(p, line, re.IGNORECASE) for p in patterns):
            hit_lines.append(i)

    blocks = []
    for i in hit_lines:
        start = max(0, i - context)
        end = min(len(lines), i + context + 1)
        if blocks and start <= blocks[-1][1]:
            blocks[-1] = (blocks[-1][0], max(blocks[-1][1], end))
        else:
            blocks.append((start, end))
        if len(blocks) >= max_blocks:
            break

    for start, end in blocks:
        safe_print(f"[L{start+1}-L{end}]")
        for n in range(start, end):
            safe_print(f"{n+1:04}: {lines[n]}")

    safe_print(f"{title}_BLOCKS={len(blocks)}")
    return len(blocks)

safe_print("VERTEX WORKS CLIP RELAY / FOCUSED FRONTEND PROBE 000092")
safe_print("MODE=READ_ONLY")

front_blocks = emit_match_blocks(
    "APP_JS_EVIDENCE_CLIPBOARD_EVENTS",
    APP,
    [
        r"evidence",
        r"return lane",
        r"clipboard",
        r"writetext",
        r"readtext",
        r"copy",
        r"paste",
        r"addEventListener",
        r"onclick",
        r"onmousedown",
        r"onmouseup",
        r"auxclick",
        r"pointerdown",
        r"pointerup",
        r"mousedown",
        r"mouseup",
        r"button\s*===\s*1",
        r"which\s*===\s*2",
        r"invoke\(",
    ],
    context=8,
    max_blocks=32,
)

html_blocks = emit_match_blocks(
    "INDEX_EVIDENCE_CONTROLS",
    INDEX,
    [
        r"evidence",
        r"return",
        r"copy",
        r"button",
        r"id=",
        r"class=",
    ],
    context=5,
    max_blocks=20,
)

handler_blocks = emit_match_blocks(
    "MAIN_INVOKE_HANDLER_TAIL",
    MAIN,
    [
        r"generate_handler!",
        r"invoke_handler",
        r"tauri::Builder::default",
    ],
    context=18,
    max_blocks=6,
)

safe_print("--- CONTRACT CHECKS ---")
checks = {
    "APP_JS_EXISTS": APP.exists(),
    "INDEX_EXISTS": INDEX.exists(),
    "MAIN_EXISTS": MAIN.exists(),
    "FRONTEND_BLOCKS_PRESENT": front_blocks > 0,
    "INVOKE_HANDLER_PRESENT": handler_blocks > 0,
}
for key, value in checks.items():
    safe_print(f"{key}={'PASS' if value else 'FAIL'}")

safe_print("SOURCE_MUTATION=NONE")
safe_print("NEXT=VERTEX_CLIP_RELAY_IMPLEMENTATION_FROM_EXACT_FRONTEND_CONTRACT")

if not all(checks.values()):
    raise SystemExit(1)
