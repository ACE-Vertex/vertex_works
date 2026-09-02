# VERTEX WORKS — NATIVE RESTART VERIFICATION HOTFIX 000083

000082 implementation succeeded:
- Rust command added and registered
- Cargo fmt/test/release build passed
- New immutable release created
- current.json advanced
- Restart UI assets linked

000082 was marked VERIFY FAILED only because its verifier expected the literal
`data-state="armed"` inside JavaScript.

Actual implementation uses:
- `const ARM_MS = 2400`
- `setState("armed", "CONFIRM")`
- second-click condition `Date.now() <= armedUntil`
- CSS selector `button[data-state="armed"]`

000083 changes no product source.
It corrects the verification contract and reconfirms cargo fmt/test.
