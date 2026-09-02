from pathlib import Path
import re

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
UI = ROOT / "ui"

print("VERTEX WORKS UI / LOCALIZATION SOURCE CAPTURE 000074")
print("MODE=READ_ONLY")
print("UI_ROOT=", UI)

if not UI.exists():
    raise SystemExit("UI_ROOT_MISSING")

files = []
for p in sorted(UI.rglob("*")):
    if p.is_file() and p.suffix.lower() in {".html",".css",".js",".json",".svg"}:
        if "node_modules" not in p.parts:
            files.append(p)

print("UI_SOURCE_FILES=", len(files))
for p in files[:120]:
    print("UI_FILE=", p.relative_to(ROOT))

patterns = {
    "BRAND": re.compile(r"vertex\s*works|vertexworks|brand|logo|mark", re.I),
    "HEADER_NAV": re.compile(r"header|topbar|toolbar|nav|workspace|project explorer", re.I),
    "THEME": re.compile(r"--[a-zA-Z0-9_-]+\s*:|#[0-9a-fA-F]{6}|accent|theme|color", re.I),
    "LOCALIZATION": re.compile(r"i18n|locale|language|lang\b|日本語|english|japanese|['\"]ja['\"]|['\"]en['\"]", re.I),
    "JAPANESE": re.compile(r"[\u3040-\u30ff\u3400-\u9fff]"),
}

def capture(path, label, regex, max_hits=30, radius=2):
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return
    hits = [i for i,l in enumerate(lines) if regex.search(l)]
    if not hits:
        return
    print(f"\n=== {label}: {path.relative_to(ROOT)} HITS={len(hits)} ===")
    emitted = 0
    seen=set()
    for idx in hits:
        if emitted >= max_hits:
            print("...TRUNCATED...")
            break
        start=max(0,idx-radius); end=min(len(lines),idx+radius+1)
        key=(start,end)
        if key in seen:
            continue
        seen.add(key)
        for j in range(start,end):
            print(f"{j+1:5}: {lines[j]}")
        print("---")
        emitted += 1

# Prioritize primary UI files, then search all UI source.
preferred = [
    UI/"index.html",
    UI/"app.js",
    UI/"style.css",
    UI/"scoped-xray.css",
]
ordered = [p for p in preferred if p.exists()] + [p for p in files if p not in preferred]

for p in ordered:
    for label, regex in patterns.items():
        # Japanese and localization are especially important for English-only removal.
        limit = 50 if label in {"LOCALIZATION","JAPANESE"} else 20
        capture(p, label, regex, max_hits=limit)

# Summary counts for Japanese-bearing files.
jp=[]
for p in files:
    try:
        text=p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    count=len(patterns["JAPANESE"].findall(text))
    if count:
        jp.append((count,p))
print("\n=== JAPANESE FILE SUMMARY ===")
print("JAPANESE_FILES=", len(jp))
for count,p in sorted(jp, reverse=True)[:60]:
    print("JP_FILE=", count, p.relative_to(ROOT))

print("\nVERTEX_WORKS_UI_SOURCE_CAPTURE_074 PASS")
