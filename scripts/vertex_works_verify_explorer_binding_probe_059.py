from pathlib import Path
import re
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass
try:
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
APP = ROOT / "ui" / "app.js"
MAIN = ROOT / "src-tauri" / "src" / "main.rs"

def read(path):
    return path.read_text(encoding="utf-8-sig", errors="replace")

def emit_context(title, text, patterns, before=4, after=10, limit=36):
    print()
    print("=" * 92)
    print(title)
    print("=" * 92)
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines):
        if any(re.search(p, line, re.I) for p in patterns):
            hits.append(i)
    # de-duplicate overlapping windows
    emitted = []
    count = 0
    for idx in hits:
        start = max(0, idx-before)
        end = min(len(lines), idx+after+1)
        if any(start <= e <= end or s <= idx <= e for s, e in emitted):
            continue
        emitted.append((start, end))
        print(f"\n--- L{idx+1} ---")
        for j in range(start, end):
            print(f"{j+1:5}: {lines[j]}")
        count += 1
        if count >= limit:
            print("\n[TRUNCATED CONTEXT WINDOWS]")
            break
    if count == 0:
        print("NO_MATCH")

app = read(APP)
main = read(MAIN)

print("VERTEX WORKS 0.5.0 - EXPLORER AUTHORITATIVE BINDING PROBE 000060")
print(f"ROOT={ROOT}")
print("MODE=READ_ONLY")
print("PRODUCTION_SOURCE_MODIFIED=false")

# Backend proof: XrayFolder already owns exact identity.
folder_block = re.search(
    r"struct\s+XrayFolder\s*\{(?P<body>.*?)^\}",
    main,
    re.S | re.M
)
if not folder_block:
    raise SystemExit("XRAY_FOLDER_STRUCT=FAIL")
body = folder_block.group("body")
checks = {
    "XRAY_FOLDER_STRUCT": True,
    "XRAY_FOLDER_HAS_ID": re.search(r"\bid\s*:\s*String", body) is not None,
    "XRAY_FOLDER_HAS_NAME": re.search(r"\bname\s*:\s*String", body) is not None,
    "XRAY_FOLDER_HAS_PATH": re.search(r"\bpath\s*:\s*String", body) is not None,
    "XRAY_FOLDER_HAS_RELATIVE_PATH": re.search(r"\brelative_path\s*:\s*String", body) is not None,
}
for k, v in checks.items():
    print(f"{k}={'PASS' if v else 'FAIL'}")
if not all(checks.values()):
    raise SystemExit("BACKEND_AUTHORITATIVE_FOLDER_IDENTITY=FAIL")

# Find X-Ray command names and handler registration.
commands = []
for m in re.finditer(r"#\[tauri::command\]\s*(?:async\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)", main):
    name = m.group(1)
    if "xray" in name.lower() or "ray" in name.lower():
        commands.append(name)
print("XRAY_TAURI_COMMANDS=" + ",".join(commands))

emit_context(
    "RUST — XrayFolder / Project X-Ray result / command surface",
    main,
    [
        r"struct\s+XrayFolder",
        r"relative_path",
        r"folders\s*:",
        r"fn\s+[A-Za-z_]*xray[A-Za-z_]*\s*\(",
        r"generate_handler!",
    ],
    before=5, after=16, limit=30
)

emit_context(
    "APP.JS — Project Explorer / folder renderer / X-Ray result ownership",
    app,
    [
        r"project.?explorer",
        r"x.?ray",
        r"\.folders\b",
        r"\bfolders\b",
        r"relative_path",
        r"folder\.path",
        r"folder\.name",
        r"innerHTML",
        r"createElement",
        r"dataset",
        r"tree",
        r"explorer",
    ],
    before=7, after=18, limit=42
)

# Specific architectural verdicts, not a mutation.
app_has_exact_path_binding = bool(re.search(
    r"(dataset\.[A-Za-z0-9_]*path|setAttribute\(\s*[\"']data-[^\"']*path|data-[^=]*path\s*=).*folder\.path",
    app,
    re.I | re.S
))
app_mentions_relative = "relative_path" in app
app_mentions_folder_path = bool(re.search(r"\bfolder\.path\b", app))
print()
print("=" * 92)
print("BINDING VERDICT")
print("=" * 92)
print(f"APP_MENTIONS_FOLDER_PATH={'YES' if app_mentions_folder_path else 'NO'}")
print(f"APP_MENTIONS_RELATIVE_PATH={'YES' if app_mentions_relative else 'NO'}")
print(f"APP_EXPOSES_EXACT_PATH_DATASET={'YES' if app_has_exact_path_binding else 'NO'}")
if app_has_exact_path_binding:
    print("NEXT_ACTION=VERIFY_SCOPED_XRAY_CONSUMES_AUTHORITATIVE_DATASET")
else:
    print("NEXT_ACTION=PATCH_EXPLORER_RENDERER_TO_EXPOSE_XrayFolder.path_AND_FAIL_CLOSED_WITHOUT_IT")
print("SILENT_DEVELOPMENT_ROOT_FALLBACK=FORBIDDEN")
print("VERTEX_WORKS_EXPLORER_BINDING_PROBE_059 PASS")
