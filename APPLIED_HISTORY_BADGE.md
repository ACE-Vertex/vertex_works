# Vertex Receiver 0.2.3 — Applied History Checkmark

Incoming Artifact cards now show:
- ✓ APPLIED · VERIFIED
- ✓ APPLIED · VERIFY FAILED
- ↶ ROLLED BACK

Status is derived from Receiver Evidence, including existing Evidence files.
Re-staging remains allowed.

Rollback marks the corresponding Evidence file as rolled back so the Inbox does
not keep a false applied checkmark.

This build also includes 0.2.2's Windows CREATE_NO_WINDOW verification-child fix.
