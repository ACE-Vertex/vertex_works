# VERTEX WORKS CLIP RELAY 000090 — SOURCE PROBE

Purpose: inspect the exact current Works 0.5.0 backend/frontend contract before adding Vertex Clip Relay.

Target behavior:

- While Works is running, middle-button press on selected text or selected files => CLIP IN.
- A later middle-button press on an editable destination => RELEASE / PASTE.
- Works Evidence action => PRIORITY CLIP IN.
- If no capturable selection and no releasable destination exists, the native middle click should pass through.
- STAGE/APPLY/VERIFY behavior is unrelated and must remain untouched.

This probe is read-only. It captures:

- current Tauri command registration;
- current Rust dependencies and Windows-related crates;
- Evidence/clipboard handling in `ui/app.js`;
- current UI event wiring.

The implementation must use the current source contract rather than inventing handler names.
