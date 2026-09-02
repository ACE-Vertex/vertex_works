from pathlib import Path
import re
import sys

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
UI = ROOT / "ui"

def safe_print(value=""):
    # Evidence transport on this Windows host is CP932.
    # Emit ASCII-only escaped text so source capture can never fail on Unicode.
    text = str(value)
    sys.stdout.write(text.encode("ascii", "backslashreplace").decode("ascii") + "\n")

safe_print("VERTEX WORKS UI / LOCALIZATION SOURCE CAPTURE 000075")
safe_print("MODE=READ_ONLY")
safe_print("TRANSPORT=ASCII_ESCAPED")
safe_print(f"UI_ROOT={UI}")

if not UI.exists():
    raise SystemExit("UI_ROOT_MISSING")

files = []
for p in sorted(UI.rglob("*")):
    if p.is_file() and p.suffix.lower() in {".html", ".css", ".js", ".json", ".svg"}:
        if "node_modules" not in p.parts:
            files.append(p)

safe_print(f"UI_SOURCE_FILES={len(files)}")
for p in files:
    safe_print(f"UI_FILE={p.relative_to(ROOT)}")

patterns = {
    "BRAND": re.compile(r"vertex\s*works|vertexworks|brand|logo|mark", re.I),
    "HEADER_NAV": re.compile(r"header|topbar|toolbar|nav|workspace|project explorer|mode-switch", re.I),
    "THEME": re.compile(r"--[a-zA-Z0-9_-]+\s*:|#[0-9a-fA-F]{3,8}|accent|theme|color", re.I),
    "LOCALIZATION": re.compile(r"i18n|locale|language|lang\b|日本語|english|japanese|['\"]ja['\"]|['\"]en['\"]", re.I),
    "JAPANESE": re.compile(r"[\u3040-\u30ff\u3400-\u9fff]"),
}

def capture(path, label, regex, max_hits=80, radius=2):
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        safe_print(f"READ_FAIL {path.relative_to(ROOT)} {e}")
        return
    hits = [i for i, line in enumerate(lines) if regex.search(line)]
    if not hits:
        return
    safe_print(f"\n=== {label}: {path.relative_to(ROOT)} HITS={len(hits)} ===")
    emitted = 0
    last_end = -1
    for idx in hits:
        if emitted >= max_hits:
            safe_print("...TRUNCATED...")
            break
        start = max(0, idx - radius)
        end = min(len(lines), idx + radius + 1)
        if start <= last_end:
            continue
        for j in range(start, end):
            safe_print(f"{j+1:5}: {lines[j]}")
        safe_print("---")
        last_end = end - 1
        emitted += 1

preferred = [
    UI / "index.html",
    UI / "app.js",
    UI / "style.css",
    UI / "vertex-theme.css",
    UI / "scoped-xray.css",
    UI / "scoped-xray.js",
]
ordered = [p for p in preferred if p.exists()] + [p for p in files if p not in preferred]

for p in ordered:
    for label, regex in patterns.items():
        capture(p, label, regex)

jp = []
for p in files:
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    count = len(patterns["JAPANESE"].findall(text))
    if count:
        jp.append((count, p))

safe_print("\n=== JAPANESE FILE SUMMARY ===")
safe_print(f"JAPANESE_FILES={len(jp)}")
for count, p in sorted(jp, reverse=True):
    safe_print(f"JP_FILE={count} {p.relative_to(ROOT)}")

safe_print("\n=== PRIMARY SOURCE LENGTHS ===")
for p in preferred:
    if p.exists():
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            safe_print(f"LINES {p.relative_to(ROOT)}={len(lines)}")
        except Exception as e:
            safe_print(f"LINES_FAIL {p.relative_to(ROOT)} {e}")

safe_print("\nVERTEX_WORKS_UI_SOURCE_CAPTURE_075 PASS")
