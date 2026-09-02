from pathlib import Path
import re
import hashlib

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")

def safe_print(value=""):
    text = str(value)
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "backslashreplace").decode("ascii"))

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def emit_lines(title: str, path: Path, patterns, context=8, limit=80):
    safe_print(f"--- {title} ---")
    if not path.exists():
        safe_print("FOUND=FALSE")
        return

    safe_print(f"FILE={path}")
    safe_print(f"SHA256={sha(path)}")

    lines = path.read_text(encoding="utf-8").splitlines()
    hits = []
    for i, line in enumerate(lines):
        if any(re.search(p, line, re.IGNORECASE) for p in patterns):
            hits.append(i)

    used = set()
    emitted = 0
    for i in hits:
        start = max(0, i - context)
        end = min(len(lines), i + context + 1)

        if any(n in used for n in range(start, end)):
            continue

        safe_print(f"[L{i+1}]")
        for n in range(start, end):
            safe_print(f"{n+1:04}: {lines[n]}")
            used.add(n)

        emitted += 1
        if emitted >= limit:
            break

    safe_print(f"{title}_BLOCKS={emitted}")

def emit_cargo(path: Path):
    safe_print("--- CARGO_CONTRACT ---")
    if not path.exists():
        safe_print("FOUND=FALSE")
        return

    safe_print(f"FILE={path}")
    safe_print(f"SHA256={sha(path)}")

    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        s = line.strip()
        if (
            s.startswith("name")
            or s.startswith("version")
            or s.startswith("edition")
            or s.startswith("tauri")
            or "windows" in s.lower()
            or "clipboard" in s.lower()
            or "serde" in s.lower()
            or "tokio" in s.lower()
        ):
            safe_print(f"L{i}: {s}")

safe_print("VERTEX WORKS CLIP RELAY 000090 / SOURCE PROBE")
safe_print("MODE=READ_ONLY_CP932_SAFE")

emit_cargo(ROOT / "src-tauri" / "Cargo.toml")

emit_lines(
    "TAURI_BACKEND",
    ROOT / "src-tauri" / "src" / "main.rs",
    [
        r"#\[tauri::command\]",
        r"invoke_handler",
        r"Builder::default",
        r"stage_artifact",
        r"apply_stage",
        r"evidence",
        r"clipboard",
        r"window",
        r"state",
        r"setup",
    ],
    context=10,
    limit=40,
)

emit_lines(
    "FRONTEND_CLIP_AND_EVIDENCE",
    ROOT / "ui" / "app.js",
    [
        r"evidence",
        r"clipboard",
        r"navigator\.clipboard",
        r"copy",
        r"paste",
        r"stage_artifact",
        r"apply_stage",
        r"addEventListener",
        r"mousedown",
        r"mouseup",
        r"auxclick",
        r"pointer",
        r"wheel",
    ],
    context=10,
    limit=50,
)

emit_lines(
    "FRONTEND_LAYOUT",
    ROOT / "ui" / "index.html",
    [
        r"evidence",
        r"button",
        r"script",
        r"app\.js",
    ],
    context=8,
    limit=20,
)

safe_print("--- CONTRACT CHECKS ---")
checks = {
    "MAIN_RS": (ROOT / "src-tauri" / "src" / "main.rs").exists(),
    "CARGO_TOML": (ROOT / "src-tauri" / "Cargo.toml").exists(),
    "APP_JS": (ROOT / "ui" / "app.js").exists(),
}
for key, value in checks.items():
    safe_print(f"{key}={'PASS' if value else 'FAIL'}")

safe_print("SOURCE_MUTATION=NONE")
safe_print("NEXT=IMPLEMENT_VERTEX_CLIP_RELAY_GLOBAL_MIDDLE_BUTTON")

if not all(checks.values()):
    raise SystemExit(1)
