# VERTEX WORKS 0.5.0
## VERTEX RAY — PROJECT ROOT SCOPE RESET / 000064

Blueprint work is intentionally deferred.

Ray's only scoped targeting rule is now:

1. A Project Explorer row owns an `XrayFolder.relative_path`.
2. Take only the first segment of that relative path.
3. Build one top-level project root:
   `G:\Vertex_Project\Development\<project>`
4. Right-click anywhere inside that project's tree and Ray scans that project root.
5. If a project root cannot be determined, Ray fails closed.
6. Scoped Ray never falls back to the whole Development tree.
7. Whole Development scanning remains an explicit global PROJECT X-RAY action.

Example:
`vertex_brain_system/ui/assets`
-> `vertex_brain_system`
-> `G:\Vertex_Project\Development\vertex_brain_system`

No exact nested-folder scope is required for this phase.
No pointer text inference is used.
No folder-name search command is used.


## 000065 Python compatibility hotfix

000064 correctly reached the exact `xrayBuildFolderRow(f)` migration path, but
failed before writing `ui/app.js` because this host Python does not support
`Path.write_text(..., newline="\n")`.

000065 changes only that file-write call to a Python-compatible form:

`APP.write_text(patched.replace("\r\n","\n"), encoding="utf-8")`

Ray scope architecture is unchanged:
top-level project root only, no text inference, no folder-name resolution,
no silent whole-Development fallback.
