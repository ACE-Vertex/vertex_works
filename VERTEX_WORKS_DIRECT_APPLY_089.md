# VERTEX WORKS DIRECT APPLY HOTFIX 000089

Hotfix for DIRECT APPLY 000088.

Vertex Works Evidence proved that the migration correctly found exactly one confirmation guard in the APPLY handler:

- STAGE_ARTIFACT_CALLS=1
- APPLY_STAGE_CALLS=1
- APPLY_HANDLER_CONFIRM_CALLS=1
- REMOVABLE_CONFIRM_GUARDS=1

The patch then failed before writing `ui/app.js` because the user's Python `Path.write_text()` does not accept a `newline=` keyword.

000089 changes only the file-write mechanism to:

`APP.open("w", encoding="utf-8", newline="\n")`

The intended workflow remains:

`INSPECT -> STAGE -> APPLY click -> APPLY immediately -> VERIFY`

No auto-apply after STAGE. APPLY remains the HUMAN_APPLY gate.
