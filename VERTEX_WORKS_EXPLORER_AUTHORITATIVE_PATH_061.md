# VERTEX WORKS 0.5.0
## PROJECT EXPLORER -> VERTEX RAY EXACT ROW BINDING / 000063

000062 reached the exact renderer but stopped on an unnecessary safety assertion:
it expected `xrayBuildFolderRow` to reference `f.depth`.

The exact renderer tuple is already known:
- function: `xrayBuildFolderRow`
- folder object: `f`
- row element: `row`

000063 removes only that incorrect depth gate. It still requires the exact
function, parameter `f`, a real `row = document.createElement(...)`, and
visible use of `f.name`.

Then it binds `f.path`, `f.id`, and `f.relative_path` directly to the row.
Scoped Ray remains authoritative-only and fail-closed.
