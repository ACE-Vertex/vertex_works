# VERTEX WORKS 0.5.0
## IMMUTABLE RELEASE BUILD HOTFIX / 000056

Observed failure:
`versions\0.5.0\VertexWorks_0.5.0.exe` was the running executable, so Windows refused
`os.replace(... -> VertexWorks_0.5.0.exe)` during the final release-copy stage.

The source migration, UI verification, tests and release build all passed before this lock.

Fix:
- every verified release build is written to a unique immutable directory:
  `versions\0.5.0\builds\YYYYMMDD-HHMMSS\VertexWorks_0.5.0.exe`
- `current.json` becomes the authoritative pointer to the newest verified executable
- root/version aliases are convenience aliases only
- locked aliases produce `LOCKED_PENDING` and never fail the migration
- SHA-256 for the immutable executable is stored in `current.json`

This removes self-overwrite from the release pipeline.
