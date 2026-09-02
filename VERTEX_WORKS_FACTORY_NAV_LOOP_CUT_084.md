# VERTEX WORKS — FACTORY NAV LOOP CUT 000084

Emergency stabilization.

Root cause:
`switchFacility("RAY")` and `switchFacility("FORGE")` called `.click()` on their
own navigation controls. The navigation click handler then called switchFacility
again, producing an endless re-entry loop.

Fix:
- Remove the two programmatic self-click calls.
- Keep facility switching as state transition only.
- Preserve RAY / FORGE / JUDGE / SENSOR / EVIDENCE / RELEASE.
- Publish a new immutable release and update current.json.

This is a correctness hotfix only.
