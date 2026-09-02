# VERTEX WORKS CLIP RELAY — FOCUSED FRONTEND PROBE 000092

000091 verified successfully, but its stdout was dominated by the large Rust backend and Vertex Works truncated the report before the frontend Evidence/clipboard blocks were emitted.

000092 is intentionally narrow. It emits only:

- `ui/app.js` Evidence, Return Lane, clipboard, copy/paste, invoke and pointer/mouse event wiring;
- `ui/index.html` controls related to Evidence/copy/return;
- the Tauri `generate_handler!` tail.

No existing Works source is modified.

This is the last source-capture gate before implementing Vertex Clip Relay.
