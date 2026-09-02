from pathlib import Path
import hashlib
import json

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
ENTRY = ROOT / "VertexWorks.exe"
PENDING = ROOT / "VertexWorks.pending-launcher.exe"
CURRENT = ROOT / "current.json"
LEDGER = ROOT / "history" / "update-ledger.jsonl"
LAUNCHER_BUILD = ROOT / "launcher" / "target" / "release" / "vertex-works-launcher.exe"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

data = json.loads(CURRENT.read_text(encoding="utf-8"))
single = data.get("single_entry", {})
release = Path(data.get("release_exe",""))

checks = {
    "CURRENT_EXISTS": CURRENT.exists(),
    "ACTIVE_RELEASE_EXISTS": release.is_file(),
    "LAUNCHER_BUILD_EXISTS": LAUNCHER_BUILD.is_file(),
    "LEDGER_EXISTS": LEDGER.is_file(),
    "ENTRY_MODE": single.get("mode") == "FIXED_LAUNCHER_CURRENT_POINTER",
    "ENTRY_NAME": single.get("entry_exe") == str(ENTRY),
    "ENTRY_STATE_VALID": single.get("state") in ("INSTALLED", "PENDING_ROOT_REPLACEMENT"),
}

state = single.get("state")
if state == "INSTALLED":
    checks["ROOT_ENTRY_EXISTS"] = ENTRY.is_file()
    checks["ROOT_ENTRY_IS_LAUNCHER"] = ENTRY.is_file() and sha(ENTRY) == sha(LAUNCHER_BUILD)
    checks["NO_PENDING_REQUIRED"] = not PENDING.exists()
else:
    checks["PENDING_EXISTS"] = PENDING.is_file()
    checks["PENDING_IS_LAUNCHER"] = PENDING.is_file() and sha(PENDING) == sha(LAUNCHER_BUILD)

# Project-root UX contract: no version-labelled VertexWorks_*.exe should remain unlocked at root.
root_versioned = [p.name for p in ROOT.glob("VertexWorks_*.exe")]
checks["NO_VERSIONED_ROOT_ENTRY"] = len(root_versioned) == 0

for k,v in checks.items():
    print(f"{k}={'PASS' if v else 'FAIL'}")

if root_versioned:
    print("ROOT_VERSIONED_EXE=", ",".join(root_versioned))

bad = [k for k,v in checks.items() if not v]
if bad:
    raise SystemExit("VERTEX_WORKS_SINGLE_ENTRY_072_VERIFY FAIL: " + ", ".join(bad))

print("SINGLE_ENTRY_STATE=", state)
print("VISIBLE_ENTRY=", ENTRY)
print("ACTIVE_RELEASE=", release)
print("VERTEX_WORKS_SINGLE_ENTRY_072_VERIFY PASS")
