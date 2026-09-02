from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import time

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
CARGO = ROOT / "src-tauri" / "Cargo.toml"
MAIN = ROOT / "src-tauri" / "src" / "main.rs"
NEW_INBOX = Path(r"G:\Vertex_Project\Development\_incoming")
OLD_INBOX = Path(r"G:\Vertex_Project\_incoming\vertex_works")

OLD_LITERAL = r'const DEFAULT_INBOX: &str = r"G:\Vertex_Project\_incoming\vertex_works";'
NEW_LITERAL = r'const DEFAULT_INBOX: &str = r"G:\Vertex_Project\Development\_incoming";'

def run(label, args):
    print(f"\n=== {label} ===")
    cp = subprocess.run(args, cwd=ROOT, text=True)
    if cp.returncode:
        raise RuntimeError(f"{label} failed with exit code {cp.returncode}")

def cargo_value(key, fallback):
    text = CARGO.read_text(encoding="utf-8", errors="replace")
    pkg = re.search(r'(?ms)^\[package\]\s*(.*?)(?=^\[|\Z)', text)
    if not pkg:
        return fallback
    hit = re.search(rf'(?m)^\s*{re.escape(key)}\s*=\s*"([^"]+)"', pkg.group(1))
    return hit.group(1) if hit else fallback

print("VERTEX WORKS RECEIVING BAY EXACT CONTRACT MIGRATION 000070")
print("ROOT=", ROOT)
print("CARGO_EXISTS=", CARGO.exists())
print("MAIN_EXISTS=", MAIN.exists())

if not CARGO.exists() or not MAIN.exists():
    raise RuntimeError("SOURCE ROOT CONTRACT MISSING: expected vertex_works/src-tauri source is absent")

package = cargo_value("name", "")
version = cargo_value("version", "0.5.0")
print("PACKAGE=", package)
print("VERSION=", version)
if package != "vertex-receiver":
    raise RuntimeError(f"SOURCE ROOT CONTRACT MISMATCH: expected package vertex-receiver, got {package!r}")

backup_root = ROOT / "MIGRATION_BACKUPS" / "RECEIVING_BAY_070" / time.strftime("%Y%m%d-%H%M%S")
backup_root.mkdir(parents=True, exist_ok=True)
main_backup = backup_root / "main.rs"
shutil.copy2(MAIN, main_backup)

current = ROOT / "current.json"
current_backup = None
if current.exists():
    current_backup = backup_root / "current.json"
    shutil.copy2(current, current_backup)

created_new = not NEW_INBOX.exists()

try:
    NEW_INBOX.mkdir(parents=True, exist_ok=True)

    text = MAIN.read_text(encoding="utf-8", errors="strict")
    old_count = text.count(OLD_LITERAL)
    new_count = text.count(NEW_LITERAL)

    print("OLD_LITERAL_COUNT=", old_count)
    print("NEW_LITERAL_COUNT=", new_count)

    if new_count == 1 and old_count == 0:
        print("DEFAULT_INBOX_ALREADY_MIGRATED=PASS")
    elif old_count == 1 and new_count == 0:
        text = text.replace(OLD_LITERAL, NEW_LITERAL, 1)
        MAIN.write_text(text.replace("\r\n", "\n"), encoding="utf-8")
        print("DEFAULT_INBOX_PATCHED=PASS")
    else:
        raise RuntimeError(
            f"DEFAULT_INBOX exact contract mismatch: old={old_count}, new={new_count}; source restored"
        )

    post = MAIN.read_text(encoding="utf-8", errors="replace")
    checks = {
        "NEW_INBOX_LITERAL": NEW_LITERAL in post,
        "OLD_INBOX_LITERAL_REMOVED": OLD_LITERAL not in post,
        "NEW_INBOX_EXISTS": NEW_INBOX.is_dir(),
        "SCAN_INBOX_USES_DEFAULT": "fs::read_dir(DEFAULT_INBOX)" in post,
        "RECEIVER_INFO_EXPOSES_DEFAULT": '"inbox": DEFAULT_INBOX' in post,
    }
    bad = [k for k,v in checks.items() if not v]
    for k,v in checks.items():
        print(f"{k}={'PASS' if v else 'FAIL'}")
    if bad:
        raise RuntimeError("Receiving Bay contract failed: " + ", ".join(bad))

    run("CARGO FMT", ["cargo", "fmt", "--manifest-path", str(CARGO), "--", "--check"])
    run("CARGO TEST", ["cargo", "test", "--manifest-path", str(CARGO)])
    run("RELEASE BUILD", ["cargo", "build", "--release", "--manifest-path", str(CARGO)])

    release_src = ROOT / "src-tauri" / "target" / "release" / "vertex-receiver.exe"
    if not release_src.exists():
        raise RuntimeError(f"release executable missing: {release_src}")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    build_dir = ROOT / "versions" / version / "builds" / stamp
    build_dir.mkdir(parents=True, exist_ok=True)
    release_exe = build_dir / f"VertexWorks_{version}.exe"
    tmp = build_dir / f".VertexWorks_{version}.exe.tmp"
    shutil.copy2(release_src, tmp)
    os.replace(tmp, release_exe)
    sha256 = hashlib.sha256(release_exe.read_bytes()).hexdigest()

    aliases = {}
    def publish_alias(label, target):
        pending = target.with_name(target.name + f".{stamp}.pending")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(release_exe, pending)
            try:
                os.replace(pending, target)
                aliases[label] = {"state":"UPDATED","path":str(target)}
            except PermissionError as e:
                aliases[label] = {
                    "state":"LOCKED_PENDING","path":str(target),
                    "pending":str(pending),"error":str(e)
                }
        except Exception as e:
            aliases[label] = {
                "state":"NON_FATAL_ALIAS_ERROR","path":str(target),"error":str(e)
            }

    publish_alias("stable_alias", ROOT / "VertexWorks.exe")
    publish_alias("legacy_version_alias", ROOT / f"VertexWorks_{version}.exe")
    publish_alias("version_alias", ROOT / "versions" / version / f"VertexWorks_{version}.exe")

    current_data = {}
    if current.exists():
        try:
            current_data = json.loads(current.read_text(encoding="utf-8"))
        except Exception:
            current_data = {}

    current_data.update({
        "product": "VERTEX WORKS",
        "version": version,
        "release_policy": "IMMUTABLE_BUILD_PATH",
        "release_exe": str(release_exe),
        "sha256": sha256,
        "aliases": aliases,
        "build_stamp": stamp,
        "timestamp_unix": int(time.time()),
        "receiving_bay": str(NEW_INBOX),
        "legacy_receiving_bay": str(OLD_INBOX),
        "receiving_bay_policy": "PRIMARY_DEVELOPMENT_INCOMING",
        "source_root": str(ROOT),
        "source_root_judge": "PASS_EXACT_CONTRACT",
    })
    current.write_text(json.dumps(current_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nVERTEX_WORKS_RECEIVING_BAY_070 PASS")
    print("PRIMARY_RECEIVING_BAY", NEW_INBOX)
    print("LEGACY_RECEIVING_BAY_PRESERVED", OLD_INBOX)
    print("RESTART_REQUIRED=YES")
    print("IMMUTABLE_RELEASE", release_exe)
    print("SHA256", sha256)
    print("BACKUP", backup_root)

except Exception:
    shutil.copy2(main_backup, MAIN)
    if current_backup and current_backup.exists():
        shutil.copy2(current_backup, current)
    elif current.exists() and current_backup is None:
        try:
            current.unlink()
        except Exception:
            pass
    if created_new:
        try:
            if NEW_INBOX.exists() and not any(NEW_INBOX.iterdir()):
                NEW_INBOX.rmdir()
        except Exception:
            pass
    print("MIGRATION_RESTORED", backup_root)
    raise
