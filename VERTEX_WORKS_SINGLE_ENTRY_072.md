# VERTEX WORKS — SINGLE ENTRY / MULTI-VERSION HISTORY 000072

## Customer-facing rule

The Vertex Works project root exposes exactly one launch identity:

`VertexWorks.exe`

The human launch point no longer represents a specific product version.

It is a fixed launcher that reads:

`current.json -> release_exe`

and launches the current Verified immutable release.

## Developer-facing rule

Version/build history remains internal and traceable.

- `current.json` = active release pointer
- immutable versioned build = actual runnable product
- `history/update-ledger.jsonl` = update history
- `history/single-entry-bootstrap/...` = transition backup
- `history/legacy-root-exe/...` = old root-level versioned executables

The launcher is deliberately separated from the product binary so future
product upgrades do not require a new shortcut, new root executable name, or
new user launch behavior.

## Transition state

If `VertexWorks.exe` is locked while 000072 is applied, a
`VertexWorks.pending-launcher.exe` is staged and current.json records
`PENDING_ROOT_REPLACEMENT`. That is a one-time migration condition, not the
steady-state layout.
