# VERTEX WORKS 0.4.1 — PROJECT X-RAY FULL TREE HOTFIX

Recursive read-only Project X-Ray for the complete visible Vertex Project folder tree.

- Project root: `G:\Vertex_Project\Development`
- Project Explorer now indexes nested folders recursively instead of only top-level areas.
- Manifest-bearing nested crates/apps/components are no longer treated as recursion stop points.
- `target`, `node_modules`, `.git`, IDE caches and generated caches remain visible as `IGNORED` boundaries but are not descended into.
- Central topology intentionally stays top-level for readability; the left Explorer is the full recursive structural index.
- X-Ray remains read-only: no source, evidence or runtime file is modified.
- 500,000 entry safety budget; partial status is explicit if reached.
- SUCCESS / ERROR / ANALYSIS lane and compact **CLIP TO VERA** handoff are preserved.
