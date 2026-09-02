from pathlib import Path
import shutil, json, time, os, hashlib

root = Path(r"G:\Vertex_Project\Development\vertex_works")
src = root / "src-tauri/target/release/vertex-receiver.exe"
if not src.exists():
    raise SystemExit(f"release executable missing: {src}")

version = "0.5.0"
stamp = time.strftime("%Y%m%d-%H%M%S")
build_dir = root / "versions" / version / "builds" / stamp
build_dir.mkdir(parents=True, exist_ok=True)

# IMPORTANT:
# Never replace a possibly-running EXE in place.
# Each verified build receives its own immutable path.
release_exe = build_dir / f"VertexWorks_{version}.exe"
tmp = build_dir / f".VertexWorks_{version}.exe.tmp"
shutil.copy2(src, tmp)
os.replace(tmp, release_exe)

sha256 = hashlib.sha256(release_exe.read_bytes()).hexdigest()

aliases = {}

def best_effort_alias(label: str, target: Path):
    pending = target.with_name(target.name + f".{stamp}.pending")
    try:
        shutil.copy2(release_exe, pending)
        try:
            os.replace(pending, target)
            aliases[label] = {
                "state": "UPDATED",
                "path": str(target),
            }
        except PermissionError as e:
            aliases[label] = {
                "state": "LOCKED_PENDING",
                "path": str(target),
                "pending": str(pending),
                "error": str(e),
            }
    except Exception as e:
        aliases[label] = {
            "state": "NON_FATAL_ALIAS_ERROR",
            "path": str(target),
            "error": str(e),
        }

# These are convenience aliases only. A lock must never invalidate a good build.
best_effort_alias("stable_alias", root / "VertexWorks.exe")
best_effort_alias("legacy_version_alias", root / f"VertexWorks_{version}.exe")
best_effort_alias("version_alias", root / "versions" / version / f"VertexWorks_{version}.exe")

current = {
    "product": "VERTEX WORKS",
    "version": version,
    "feature": "VERTEX RAY / SCOPED X-RAY / VERA HANDOFF",
    "release_policy": "IMMUTABLE_BUILD_PATH",
    "release_exe": str(release_exe),
    "sha256": sha256,
    "aliases": aliases,
    "timestamp_unix": int(time.time()),
    "build_stamp": stamp,
}
(root / "current.json").write_text(
    json.dumps(current, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("VERTEX_WORKS_050_READY", release_exe)
print("RELEASE_POLICY IMMUTABLE_BUILD_PATH")
print("SHA256", sha256)
for label, info in aliases.items():
    print(label.upper(), info["state"], info["path"])
    if info.get("pending"):
        print(label.upper() + "_PENDING", info["pending"])
