# VERTEX WORKS DIRECT APPLY 000088

Requested workflow:

`INSPECT -> STAGE -> APPLY click -> APPLY immediately -> VERIFY`

The redundant confirmation shown after the operator has already clicked APPLY is removed.

Preserved:
- STAGE remains separate from APPLY.
- No auto-apply merely because staging succeeded.
- APPLY remains the explicit HUMAN_APPLY gate.
- Backup / rollback / verification / Evidence remain intact.

The migration fails closed if the current UI source does not contain one uniquely identifiable browser confirmation guard in the same handler as `apply_stage`.
