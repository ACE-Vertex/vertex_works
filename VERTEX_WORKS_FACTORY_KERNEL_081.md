# VERTEX WORKS — FACTORY KERNEL / MULTI-FACILITY CHASSIS 000081

Vertex Works is the factory for Vertex products.

This phase changes the product from two crowded pages into one factory shell with
specialized facilities:

RAY      = SEE
FORGE    = BUILD
JUDGE    = DECIDE
SENSOR   = OBSERVE
EVIDENCE = PROVE
RELEASE  = SHIP

Implementation:
- Existing RAY and FORGE are preserved as real workspaces.
- JUDGE, SENSOR, EVIDENCE and RELEASE become dedicated workspaces.
- Sensor runtime data feeds Judge.
- Judge produces real connected-gate verdicts.
- Sensor/Judge evidence is retained locally.
- Release Gate derives readiness from Judge.
- Native build/release evidence is explicitly UNAVAILABLE until a real native bridge
  exists. It is not fabricated.
- Only the top-left product icon remains visible.
- The top chassis is compacted to 52px.
- Large displays are not artificially width-capped.
- Responsive layout reflows only when needed.
- Existing CLIP TO VERA path is preserved; EVIDENCE also provides a Vera evidence bundle.

The artifact also captures the current Rust/Tauri command surface read-only so the
next phase can implement real native Build/File/Release sensors instead of UI guesses.
