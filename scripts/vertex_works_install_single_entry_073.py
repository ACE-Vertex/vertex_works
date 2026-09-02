from pathlib import Path
import hashlib
import json
import os
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

print("VERTEX WORKS SINGLE ENTRY FMT TRANSACTION 000073")
print("ROOT=", ROOT)
print("ENTRY=", ENTRY)

if not CURRENT.exists():
    raise RuntimeError("current.json missing")

current_data = json.loads(CURRENT.read_text(encoding="utf-8"))
release_exe = Path(current_data.get("release_exe", ""))
if not release_exe.is_file():
    raise RuntimeError(f"active release missing: {release_exe}")

print("ACTIVE_RELEASE=", release_exe)
print("ACTIVE_VERSION=", current_data.get("version", "UNKNOWN"))
print("ACTIVE_SHA256=", current_data.get("sha256", "UNKNOWN"))

# Build first. No product-root launch state is mutated until the launcher is proven buildable.
run("LAUNCHER CARGO FMT", ["cargo", "fmt", "--manifest-path", str(LAUNCHER_CARGO)])
run("LAUNCHER CARGO FMT CHECK", ["cargo", "fmt", "--manifest-path", str(LAUNCHER_CARGO), "--", "--check"])
run("LAUNCHER CARGO BUILD", ["cargo", "build", "--release", "--manifest-path", str(LAUNCHER_CARGO)])

if not LAUNCHER_BUILD.exists():
    raise RuntimeError(f"launcher build missing: {LAUNCHER_BUILD}")

launcher_sha = sha(LAUNCHER_BUILD)
release_sha = sha(release_exe)
print("LAUNCHER_BUILD=PASS")
print("LAUNCHER_SHA256=", launcher_sha)

stamp = time.strftime("%Y%m%d-%H%M%S")
backup_root = ROOT / "MIGRATION_BACKUPS" / "SINGLE_ENTRY_073" / stamp
backup_root.mkdir(parents=True, exist_ok=True)

current_backup = backup_root / "current.json"
shutil.copy2(CURRENT, current_backup)

entry_existed = ENTRY.exists()
if entry_existed:
    shutil.copy2(ENTRY, backup_root / "VertexWorks.exe")

root_versioned = sorted(ROOT.glob("VertexWorks_*.exe"))
versioned_backup = backup_root / "root-versioned"
versioned_backup.mkdir(parents=True, exist_ok=True)
for p in root_versioned:
    shutil.copy2(p, versioned_backup / p.name)

moved = []
try:
    # Clean project root: historical version-labelled EXEs move to internal history.
    legacy_dir = HISTORY / "legacy-root-exe" / stamp
    for p in root_versioned:
        legacy_dir.mkdir(parents=True, exist_ok=True)
        dest = legacy_dir / p.name
        shutil.move(str(p), str(dest))
        moved.append((p, dest))
        print("MOVED_LEGACY_ROOT_EXE=", p.name)

    # Install exactly one customer-facing root entry.
    tmp = ROOT / ".VertexWorks.launcher.tmp.exe"
    shutil.copy2(LAUNCHER_BUILD, tmp)
    try:
        os.replace(tmp, ENTRY)
    except PermissionError:
        try:
            tmp.unlink()
        except Exception:
            pass
        raise RuntimeError(
            "ROOT ENTRY LOCKED: VertexWorks.exe is in use. "
            "Close the root-launched copy and apply 000073 from the immutable Verified build."
        )

    if sha(ENTRY) != launcher_sha:
        raise RuntimeError("installed root entry hash mismatch")

    # Preserve current immutable release pointer; only add the single-entry/customer contract.
    current_data["single_entry"] = {
        "entry_exe": str(ENTRY),
        "mode": "FIXED_LAUNCHER_CURRENT_POINTER",
        "launcher_sha256": launcher_sha,
        "state": "INSTALLED",
    }
    current_data["customer_release_identity"] = {
        "visible_entry": "VertexWorks.exe",
        "active_version": current_data.get("version"),
        "active_release": str(release_exe),
        "active_release_sha256": release_sha,
    }
    CURRENT.write_text(json.dumps(current_data, ensure_ascii=False, indent=2), encoding="utf-8")

    HISTORY.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": stamp,
        "event": "SINGLE_ENTRY_LAUNCHER_INSTALLED",
        "visible_entry": str(ENTRY),
        "active_version": current_data.get("version"),
        "active_release": str(release_exe),
        "active_release_sha256": release_sha,
        "launcher_sha256": launcher_sha,
        "legacy_root_exes_moved": [str(src) for src, _ in moved],
    }
    with LEDGER.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    print("\nROOT_SINGLE_ENTRY=PASS")
    print("VISIBLE_ENTRY=", ENTRY)
    print("ACTIVE_RELEASE_UNCHANGED=", release_exe)
    print("LEGACY_ROOT_EXES_MOVED=", len(moved))
    print("UPDATE_LEDGER=", LEDGER)
    print("BACKUP=", backup_root)
    print("VERTEX_WORKS_SINGLE_ENTRY_073 PASS")

except Exception:
    # Transactional restoration for every product-root state touched by this migration.
    try:
        shutil.copy2(current_backup, CURRENT)
    except Exception:
        pass

    if entry_existed:
        try:
            shutil.copy2(backup_root / "VertexWorks.exe", ENTRY)
        except Exception:
            pass
    else:
        try:
            if ENTRY.exists():
                ENTRY.unlink()
        except Exception:
            pass

    # Restore all root version-labelled EXEs from independent backup.
    for p in root_versioned:
        try:
            shutil.copy2(versioned_backup / p.name, p)
        except Exception:
            pass

    print("SINGLE_ENTRY_TRANSACTION_RESTORED=", backup_root)
    raise
