# VERTEX WORKS ENGINE — RECEIVING BAY CACHE RESET MIGRATION 000071

Purpose:
- Complete the Receiving Bay migration to:
  `G:\Vertex_Project\Development\_incoming`
- Remove stale Cargo/Tauri build metadata left from the historical
  `G:\Vertex_Project\Development\vertex_receiver\src-tauri` source path.

000070 proved that the source patch itself was valid but Cargo/Tauri build
metadata still referenced the old absolute source location.

000071 therefore performs `cargo clean` on the current real source:
`G:\Vertex_Project\Development\vertex_works\src-tauri\Cargo.toml`

Then:
- exact DEFAULT_INBOX patch
- cargo fmt --check
- cargo test
- cargo build --release
- immutable release publication
- current.json Receiving Bay contract update
- final verification

Restart is required only after VERIFIED.
