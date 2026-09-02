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
TARGET = ROOT / "src-tauri" / "target"
LAUNCHER_CARGO = ROOT / "launcher" / "Cargo.toml"
LAUNCHER_BUILD = ROOT / "launcher" / "target" / "release" / "vertex-works-launcher.exe"
ENTRY = ROOT / "VertexWorks.exe"
CURRENT = ROOT / "current.json"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(label, args):
    print(f"\n=== {label} ===")
    cp = subprocess.run(args, cwd=ROOT, text=True)
    if cp.returncode:
        raise RuntimeError(f"{label} failed with exit code {cp.returncode}")

def cargo_value(key, fallback=""):
    text = CARGO.read_text(encoding="utf-8", errors="replace")
    pkg = re.search(r'(?ms)^\[package\]\s*(.*?)(?=^\[|\Z)', text)
    if not pkg:
        return fallback
    hit = re.search(rf'(?m)^\s*{re.escape(key)}\s*=\s*"([^"]+)"', pkg.group(1))
    return hit.group(1) if hit else fallback

print("VERTEX WORKS BRAND FOUNDATION 000074")
print("ROOT=", ROOT)

if not CARGO.exists() or not CURRENT.exists():
    raise RuntimeError("Vertex Works source/current contract missing")

version = cargo_value("version", "0.5.0")
package = cargo_value("name")
if package != "vertex-receiver":
    raise RuntimeError(f"unexpected main package: {package!r}")

data = json.loads(CURRENT.read_text(encoding="utf-8"))
previous_release = Path(data.get("release_exe", ""))
if not previous_release.is_file():
    raise RuntimeError(f"current Verified release missing: {previous_release}")

stamp = time.strftime("%Y%m%d-%H%M%S")
backup = ROOT / "MIGRATION_BACKUPS" / "BRAND_074" / stamp
backup.mkdir(parents=True, exist_ok=True)
shutil.copy2(CURRENT, backup/"current.json")
if ENTRY.exists():
    shutil.copy2(ENTRY, backup/"VertexWorks.exe")

try:
    # 1) Rebuild fixed launcher with the accepted orange Vertex Works icon.
    run("LAUNCHER FMT", ["cargo","fmt","--manifest-path",str(LAUNCHER_CARGO)])
    run("LAUNCHER FMT CHECK", ["cargo","fmt","--manifest-path",str(LAUNCHER_CARGO),"--","--check"])
    run("LAUNCHER BUILD", ["cargo","build","--release","--manifest-path",str(LAUNCHER_CARGO)])
    if not LAUNCHER_BUILD.is_file():
        raise RuntimeError("branded launcher executable missing")
    launcher_sha = sha(LAUNCHER_BUILD)

    tmp_entry = ROOT / ".VertexWorks.brand074.tmp.exe"
    shutil.copy2(LAUNCHER_BUILD, tmp_entry)
    os.replace(tmp_entry, ENTRY)
    if sha(ENTRY) != launcher_sha:
        raise RuntimeError("root launcher hash mismatch after branding")

    # 2) Force main product package rebuild so changed Tauri icon resources are embedded.
    run("MAIN PACKAGE CLEAN", ["cargo","clean","--manifest-path",str(CARGO),"-p","vertex-receiver"])
    run("MAIN FMT CHECK", ["cargo","fmt","--manifest-path",str(CARGO),"--","--check"])
    run("MAIN TEST", ["cargo","test","--manifest-path",str(CARGO)])
    run("MAIN RELEASE BUILD", ["cargo","build","--release","--manifest-path",str(CARGO)])

    built = TARGET / "release" / "vertex-receiver.exe"
    if not built.is_file():
        raise RuntimeError(f"main release executable missing: {built}")

    build_stamp = time.strftime("%Y%m%d-%H%M%S")
    imm_dir = ROOT / "versions" / version / "builds" / build_stamp
    imm_dir.mkdir(parents=True, exist_ok=True)
    release_exe = imm_dir / f"VertexWorks_{version}.exe"
    shutil.copy2(built, release_exe)
    release_sha = sha(release_exe)

    # 3) Pointer moves; user-facing root launch identity remains VertexWorks.exe.
    data["release_exe"] = str(release_exe)
    data["sha256"] = release_sha
    data["build_stamp"] = build_stamp
    data["timestamp_unix"] = int(time.time())
    data["brand"] = {
        "family": "VERTEX PRODUCT IDENTITY",
        "product_code": "VW",
        "theme": "ORANGE",
        "app_icon": "ui/assets/brand/vertex-works-app-icon.png",
        "wordmark": "ui/assets/brand/vertex-works-wordmark.png",
        "launcher_icon_embedded": True,
        "main_app_icon_embedded": True,
        "phase": "BRAND_FOUNDATION",
    }
    single = data.setdefault("single_entry", {})
    single["launcher_sha256"] = launcher_sha
    single["entry_exe"] = str(ENTRY)
    single["mode"] = "FIXED_LAUNCHER_CURRENT_POINTER"
    single["state"] = "INSTALLED"
    CURRENT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nBRANDED_ROOT_LAUNCHER=PASS")
    print("ROOT_ENTRY=", ENTRY)
    print("PRODUCT_CODE=VW")
    print("THEME=ORANGE")
    print("NEW_IMMUTABLE_RELEASE=", release_exe)
    print("NEW_RELEASE_SHA256=", release_sha)
    print("LAUNCHER_SHA256=", launcher_sha)
    print("PREVIOUS_RELEASE_PRESERVED=", previous_release)
    print("BACKUP=", backup)
    print("VERTEX_WORKS_BRAND_FOUNDATION_074 PASS")

except Exception:
    try:
        shutil.copy2(backup/"current.json", CURRENT)
    except Exception:
        pass
    try:
        if (backup/"VertexWorks.exe").exists():
            shutil.copy2(backup/"VertexWorks.exe", ENTRY)
    except Exception:
        pass
    print("BRAND_074_TRANSACTION_RESTORED=", backup)
    raise
