# VERTEX WORKS 0.5.0
## SCOPED X-RAY — EXACT CLICKED FOLDER SCOPE / 000055

Observed evidence:
A folder-scoped Vera handoff was produced successfully, but its scope became the entire
`G:\Vertex_Project\Development` root.

Diagnosis:
The old UI resolver walked upward through the DOM looking for any absolute path. When the clicked
folder row did not expose a direct path, the Explorer container/root path could be captured first.

Fix:
- identify the nearest plausible Project Explorer row
- read an absolute path only from that clicked row
- never inherit the Explorer container's Development-root path for a child folder
- otherwise resolve the clicked row label through the existing Rust `xray_resolve_scope`
- retain duplicate-name hint resolution
- retain 000053 right-click interception and 000054 FORGE-unified dark Ray UI

Expected BrainSystem handoff:
`Scope: G:\Vertex_Project\Development\vertex_brain_system`
not the whole Development root.
