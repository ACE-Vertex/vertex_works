# VERTEX WORKS 0.5.0
## VERTEX RAY — SCOPED X-RAY / VERA HANDOFF

This migration upgrades the existing Project X-Ray Observatory without removing FORGE or the global Project X-Ray.

### Core behavior
- Right-click a folder in VERTEX PROJECT EXPLORER.
- `X-RAY THIS FOLDER`: bounded read-only structural/source scan.
- `DEEP X-RAY`: deeper source-anchor and recent-file surface.
- `X-RAY & CLIP TO VERA`: deep scan and one-click Vera handoff capsule.
- `OPEN LAST REPORT`: reopen the current-session scoped report.
- Project mutation from Scoped X-Ray is forbidden.
- Existing `CLIP TO VERA` remains available.
- Existing VRA/FORGE pipeline remains available.

### Handoff capsule
The clipboard handoff includes:
- selected absolute scope
- scan mode
- manifest/kind/version
- directory/file/source counts
- generated/cache boundaries
- executable build artifacts
- findings
- recently modified files
- important source anchors
- SHA-256 report fingerprint
- explicit read-only / mutation=false statement

### Migration safety
The VRA installs the additive Scoped X-Ray assets and a transactional migration gate.
Before current Vertex Works source is modified, the migration gate backs up:
- `src-tauri/src/main.rs`
- `src-tauri/Cargo.toml`
- `ui/index.html`

If migration, verification, tests, or release build fails, those files are automatically restored.
