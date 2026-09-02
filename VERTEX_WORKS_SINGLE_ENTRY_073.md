# VERTEX WORKS — SINGLE ENTRY / MULTI-VERSION HISTORY 000073

000072 failed before build because its new launcher source was not rustfmt-clean.
No single-entry state was installed.

000073:
- uses the rustfmt shape returned by 000072
- formats, checks, and builds the launcher BEFORE changing project-root launch state
- backs up current.json, the existing root VertexWorks.exe, and every root-level
  VertexWorks_<version>.exe before migration
- moves version-labelled root EXEs into history
- installs exactly one root launch entry: VertexWorks.exe
- leaves current.json::release_exe pointing to the current Verified immutable build
- records update history
- restores all touched root state if the migration fails

Customer contract:
1 Product / 1 Root Launch Point / 1 Current Pointer / N Immutable History
