# VERTEX WORKS — CLIP RELAY RUSTFMT HOTFIX 000094

The 000093 implementation compiled, passed all six Rust tests, built the release binary, and passed the Clip Relay source-contract verifier.

The only failed verification was `cargo fmt --check`.

000094 performs **rustfmt only** on the current Works `src-tauri` source tree and then reruns the complete verification/build/release chain.

No Clip Relay algorithm or UX behavior is intentionally changed.

Expected final flow remains:

- selected text/files + middle click -> CLIP IN
- next middle click -> RELEASE
- Evidence button -> PRIORITY CLIP IN
- normal middle click passes through when the relay is idle

Because the currently running Works process may lock `VertexWorks.exe`, release publishing can still report `STABLE_ALIAS LOCKED_PENDING`. That is not a build failure; the new binary is still published to the immutable/versioned build path. Restart Works after verification to activate the newly compiled Clip Relay.
