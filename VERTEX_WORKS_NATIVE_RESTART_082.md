# VERTEX WORKS — NATIVE RESTART CONTROL 000082

Adds a bottom-left Restart control.

Behavior:
1. First click arms for 2400 ms.
2. Second click invokes the native Tauri command `restart_vertex_works`.
3. Rust walks upward from the active immutable release until it finds both
   `current.json` and root `VertexWorks.exe`.
4. Rust launches the root `VertexWorks.exe`.
5. The current Tauri process exits.
6. The root launcher reads current.json, so the restart enters the latest
   authoritative Verified release.

This is a real application restart, not a WebView reload.
