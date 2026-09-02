# VERTEX WORKS 0.5.0
## VERTEX RAY — POINTER-EXACT SCOPE BINDING / 000057

Observed after 000055:
Selecting `vertex_brain_system` and opening Ray still resolved to
`G:\Vertex_Project\Development`, so the entire project was scanned.

Root cause addressed:
The Explorer DOM carries the Development-root path at a higher/container level.
Even row-first ancestry heuristics can still bind to that root when the actual
folder label/path lives in a sibling/child element.

000057 changes the contract:
1. Freeze the exact right-click x/y coordinates.
2. Read `document.elementsFromPoint(x,y)` deepest-first.
3. Prefer direct text / row-local folder labels under the pointer.
4. Treat `Development` as a last-priority root candidate.
5. Never accept an absolute Explorer path unless its basename matches a visible
   pointer-derived folder label.
6. Resolve candidate labels through the Rust resolver one by one.
7. Accept the Rust result only when the resolved basename matches the requested label.
8. If binding is still impossible, show an explicit Ray error instead of scanning
   the Development root.

Expected:
Right-click `vertex_brain_system` -> scope
`G:\Vertex_Project\Development\vertex_brain_system`.
