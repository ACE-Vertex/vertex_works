# VERTEX WORKS 0.5.0 — ORANGE WORKSPACE / ENGLISH LOCK 000076

Basis: VERIFIED UI SOURCE CAPTURE 000075.

This phase deliberately separates visible/runtime English-only behavior from
final dead-code removal. It does not guess the unknown exact i18n implementation
inside app.js.

Changes:
- VW product identity is applied to the real UI.
- Old generic Vertex mark references in index.html are replaced by the approved VW icon.
- Dedicated dark/orange product theme is loaded last.
- Responsive chrome compression is added without removing RAY/FORGE functionality.
- HTML language contract becomes English.
- Existing language controls are hidden but their element IDs are retained for one
  compatibility cycle.
- A one-shot English lock activates the existing English path after boot.
- Cargo fmt/test/release build runs.
- A new immutable 0.5.0 release is created and current.json becomes authoritative.

Next:
- Runtime visual confirmation.
- Then 000077 can remove the dead Japanese/i18n source itself with exact source evidence.
