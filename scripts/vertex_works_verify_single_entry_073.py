from pathlib import Path
import hashlib
import json

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
ENTRY = ROOT / "VertexWorks.exe"
CURRENT = ROOT / "current.json"
LEDGER = ROOT / "history" / "update-ledger.jsonl"
LAUNCHER_BUILD = ROOT / "launcher" / "target" / "release" / "vertex-works-launcher.exe"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

data = json.loads(CURRENT.read_text(encoding="utf-8"))
single = data.get("single_entry", {})
release = Path(data.get("release_exe", ""))

root_versioned = [p.name for p in ROOT.glob("VertexWorks_*.exe")]

checks = {
    "ENTRY_EXISTS": ENTRY.is_file(),
    "ACTIVE_RELEASE_EXISTS": release.is_file(),
    "LAUNCHER_BUILD_EXISTS": LAUNCHER_BUILD.is_file(),
    "ENTRY_IS_LAUNCHER": ENTRY.is_file() and LAUNCHER_BUILD.is_file() and sha(ENTRY) == sha(LAUNCHER_BUILD),
    "ENTRY_MODE": single.get("mode") == "FIXED_LAUNCHER_CURRENT_POINTER",
    "ENTRY_STATE": single.get("state") == "INSTALLED",
    "ENTRY_NAME": single.get("entry_exe") == str(ENTRY),
    "LEDGER_EXISTS": LEDGER.is_file(),
    "NO_VERSIONED_ROOT_ENTRY": len(root_versioned) == 0,
    "VISIBLE_ENTRY_CONTRACT": data.get("customer_release_identity", {}).get("visible_entry") == "VertexWorks.exe",
}

for k,v in checks.items():
    print(f"{k}={'PASS' if v else 'FAIL'}")

if root_versioned:
    print("ROOT_VERSIONED_EXE=", ",".join(root_versioned))

bad = [k for k,v in checks.items() if not v]
if bad:
    raise SystemExit("VERTEX_WORKS_SINGLE_ENTRY_073_VERIFY FAIL: " + ", ".join(bad))

print("VISIBLE_ENTRY=", ENTRY)
print("ACTIVE_RELEASE=", release)
print("ROOT_EXECUTABLE_COUNT_CONTRACT=1")
print("VERTEX_WORKS_SINGLE_ENTRY_073_VERIFY PASS")
