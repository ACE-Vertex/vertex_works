from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import time

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
LAUNCHER = ROOT / "launcher"
LAUNCHER_CARGO = LAUNCHER / "Cargo.toml"
LAUNCHER_BUILD = LAUNCHER / "target" / "release" / "vertex-works-launcher.exe"
ENTRY = ROOT / "VertexWorks.exe"
CURRENT = ROOT / "current.json"
HISTORY = ROOT / "history"
LEDGER = HISTORY / "update-ledger.jsonl"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(label, args):
    print(f"\n=== {label} ===")
    cp = subprocess.run(args, cwd=ROOT, text=True)
    if cp.returncode:
        raise RuntimeError(f"{label} failed with exit code {cp.returncode}")

print("VERTEX WORKS SINGLE ENTRY LAUNCHER 000072")
print("ROOT=", ROOT)
print("ENTRY=", ENTRY)

if not CURRENT.exists():
    raise RuntimeError("current.json missing")

data = json.loads(CURRENT.read_text(encoding="utf-8"))
release_exe = Path(data.get("release_exe", ""))
if not release_exe.is_file():
    raise RuntimeError(f"active release missing: {release_exe}")

print("ACTIVE_RELEASE=", release_exe)
print("ACTIVE_VERSION=", data.get("version", "UNKNOWN"))
print("ACTIVE_SHA256=", data.get("sha256", "UNKNOWN"))

run("LAUNCHER CARGO FMT", ["cargo", "fmt", "--manifest-path", str(LAUNCHER_CARGO), "--", "--check"])
run("LAUNCHER CARGO BUILD", ["cargo", "build", "--release", "--manifest-path", str(LAUNCHER_CARGO)])

if not LAUNCHER_BUILD.exists():
    raise RuntimeError(f"launcher build missing: {LAUNCHER_BUILD}")

launcher_sha = sha(LAUNCHER_BUILD)
release_sha = sha(release_exe)
print("LAUNCHER_SHA256=", launcher_sha)
print("RELEASE_SHA256=", release_sha)

stamp = time.strftime("%Y%m%d-%H%M%S")
bootstrap_dir = HISTORY / "single-entry-bootstrap" / stamp
bootstrap_dir.mkdir(parents=True, exist_ok=True)

# Preserve any previous root entry exactly once as transition evidence.
if ENTRY.exists():
    old_sha = sha(ENTRY)
    if old_sha != launcher_sha:
        shutil.copy2(ENTRY, bootstrap_dir / "VertexWorks.pre-launcher.exe")
        (bootstrap_dir / "pre-launcher.sha256.txt").write_text(old_sha + "\n", encoding="utf-8")
        print("PREVIOUS_ROOT_ENTRY_BACKUP=PASS")
    else:
        print("ROOT_ENTRY_ALREADY_LAUNCHER=PASS")

# Root hygiene: move version-labelled VertexWorks executables out of the project root.
legacy_dir = HISTORY / "legacy-root-exe" / stamp
moved = []
for p in ROOT.glob("VertexWorks_*.exe"):
    if p.resolve() == release_exe.resolve():
        continue
    legacy_dir.mkdir(parents=True, exist_ok=True)
    dest = legacy_dir / p.name
    try:
        shutil.move(str(p), str(dest))
        moved.append((str(p), str(dest)))
    except PermissionError:
        print("LEGACY_ROOT_EXE_LOCKED_WARNING=", p)

# Install a fixed launcher at the single human entry point.
tmp = ROOT / ".VertexWorks.launcher.tmp.exe"
shutil.copy2(LAUNCHER_BUILD, tmp)
entry_state = "INSTALLED"
pending = None
try:
    os.replace(tmp, ENTRY)
except PermissionError:
    pending = ROOT / "VertexWorks.pending-launcher.exe"
    shutil.copy2(LAUNCHER_BUILD, pending)
    try:
        tmp.unlink()
    except Exception:
        pass
    entry_state = "PENDING_ROOT_REPLACEMENT"

# Record the launcher contract without changing the active immutable release pointer.
data["single_entry"] = {
    "entry_exe": str(ENTRY),
    "mode": "FIXED_LAUNCHER_CURRENT_POINTER",
    "launcher_sha256": launcher_sha,
    "state": entry_state,
}
if pending:
    data["single_entry"]["pending_launcher"] = str(pending)

data["customer_release_identity"] = {
    "visible_entry": "VertexWorks.exe",
    "active_version": data.get("version"),
    "active_release": str(release_exe),
    "active_release_sha256": release_sha,
}
CURRENT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

HISTORY.mkdir(parents=True, exist_ok=True)
event = {
    "timestamp": stamp,
    "event": "SINGLE_ENTRY_LAUNCHER_INSTALL",
    "visible_entry": str(ENTRY),
    "entry_state": entry_state,
    "active_version": data.get("version"),
    "active_release": str(release_exe),
    "active_release_sha256": release_sha,
    "launcher_sha256": launcher_sha,
    "legacy_root_exes_moved": moved,
}
with LEDGER.open("a", encoding="utf-8", newline="\n") as f:
    f.write(json.dumps(event, ensure_ascii=False) + "\n")

print("\nSINGLE_ENTRY_STATE=", entry_state)
if pending:
    print("PENDING_LAUNCHER=", pending)
else:
    print("ROOT_SINGLE_ENTRY=PASS")
print("VISIBLE_ENTRY=", ENTRY)
print("ACTIVE_RELEASE_UNCHANGED=", release_exe)
print("UPDATE_LEDGER=", LEDGER)
print("LEGACY_ROOT_EXES_MOVED=", len(moved))
print("VERTEX_WORKS_SINGLE_ENTRY_072 PASS")
