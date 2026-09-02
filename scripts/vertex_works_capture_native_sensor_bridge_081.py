from pathlib import Path
import re
import sys

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
MAIN = ROOT / "src-tauri" / "src" / "main.rs"

def emit(value=""):
    text = str(value)
    sys.stdout.write(text.encode("ascii", "backslashreplace").decode("ascii") + "\n")

emit("VERTEX WORKS NATIVE SENSOR BRIDGE SOURCE CAPTURE 000081")
emit("MODE=READ_ONLY")
emit("PURPOSE=NEXT NATIVE BUILD/FILE/RELEASE SENSOR PHASE")
emit("SOURCE=" + str(MAIN))

if not MAIN.exists():
    raise SystemExit("MAIN_RS_MISSING")

lines = MAIN.read_text(encoding="utf-8", errors="replace").splitlines()
patterns = {
    "TAURI_COMMANDS": re.compile(r"#\s*\[\s*tauri::command\s*\]|fn\s+[A-Za-z0-9_]+\s*\(", re.I),
    "INVOKE_HANDLER": re.compile(r"invoke_handler|generate_handler", re.I),
    "CURRENT_JSON": re.compile(r"current\.json|release_exe|sha256|versions|builds", re.I),
    "PROCESS_COMMAND": re.compile(r"Command::new|std::process|cargo|verify|build", re.I),
    "FILESYSTEM": re.compile(r"read_to_string|read_dir|metadata|canonicalize|fs::", re.I),
}

for label, regex in patterns.items():
    hits = [i for i,line in enumerate(lines) if regex.search(line)]
    emit(f"\n=== {label} HITS={len(hits)} ===")
    used = []
    emitted = 0
    for idx in hits:
        if emitted >= 60:
            emit("...TRUNCATED...")
            break
        start=max(0,idx-4); end=min(len(lines),idx+7)
        if any(not(end <= a or start >= b) for a,b in used):
            continue
        used.append((start,end))
        for j in range(start,end):
            emit(f"{j+1:5}: {lines[j]}")
        emit("---")
        emitted += 1

emit("\nMAIN_RS_LINES=" + str(len(lines)))
emit("VERTEX_WORKS_NATIVE_SENSOR_BRIDGE_SOURCE_CAPTURE_081 PASS")
