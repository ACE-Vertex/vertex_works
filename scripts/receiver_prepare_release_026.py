from pathlib import Path

root = Path.cwd()
built = root / "src-tauri" / "target" / "release" / "vertex-receiver.exe"

if built.exists():
    built.unlink()
    print(f"RECEIVER_RELEASE_PREP_REMOVED {built}")
else:
    print(f"RECEIVER_RELEASE_PREP_CLEAN {built}")
