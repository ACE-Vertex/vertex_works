from pathlib import Path
root=Path(r"G:\Vertex_Project\Development\vertex_works")
exe=root/"src-tauri/target/release/vertex-receiver.exe"
if exe.exists():
    exe.unlink()
print("VERTEX_WORKS_050_RELEASE_PREP", exe)
