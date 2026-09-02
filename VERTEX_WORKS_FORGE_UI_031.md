# VERTEX WORKS 0.3.1 — FORGE UI

## Product identity

`Vertex Receiver` is no longer the name of the whole application.

**VERTEX WORKS** is the facility.

The existing Receiver role survives as the **Receiving Bay / Intake Gate**.

```text
VERTEX WORKS
├─ Receiving Bay
├─ Inspection
├─ Staging / Backup
├─ Foundry
├─ Verification
├─ Evidence Vault
├─ Recovery / Return Lane
└─ Dispatch
```

## UI direction

The interface is rebuilt in a Vertex-native animated system inspired by the
interaction ideas of modern Vue Bits-style components, without adding Vue or a
new frontend runtime to this small Tauri utility.

Implemented concepts:

- ambient moving Beams
- line-based facility rail
- specular sweep buttons
- gradual fade around scrolling cargo
- animated telemetry counts
- facility process Dock
- glass / deep-panel Vertex Blue surfaces
- restrained motion; real Shell/Evidence remains foreground truth

These are original VERTEX WORKS implementations. No external component source
is redistributed.

## Preserved from Receiver 0.2.6

- VRA scan / inspect
- SHA verification
- allowed-root validation
- HUMAN_APPLY
- staging
- backup
- apply
- verification commands
- real-time embedded Vertex Shell stream
- Evidence generation/copy
- Error report copy
- rollback
- Return Lane
- NAME / GENRE sorting and persisted choice
- supplied Vertex Blue CSS tokens
- stale-release protection

## Incoming organization

NAME and GENRE remain intentionally lightweight.

The former Receiver family now displays as **WORKS**, because Receiver is only
one bay inside the facility. Historical `vertex-receiver-*` artifacts are still
recognized and grouped under WORKS.

No VRA schema change is required.

## Version

VERTEX WORKS 0.3.1


## 0.3.1 hotfix

The first 0.3.0 Receiver verification proved that the Rust application itself
was healthy:

- cargo fmt passed
- all six Receiver/Works tests passed
- stale-release preparation passed
- optimized release build passed

The final Python copy step failed only while printing an em dash to the Windows
CP932 console. The executable had already been copied before that print failed.

0.3.1 makes release-verification stdout intentionally ASCII-only so typography
cannot break packaging on CP932.

### Brand mark

The official user-supplied `VERTEX Project` SVG mark is now installed at:

`ui/assets/vertex-project-mark.svg`

and replaces the temporary text-only `V` mark in the Works facility rail.

The supplied SVG geometry and original cyan/blue fills are preserved verbatim.
