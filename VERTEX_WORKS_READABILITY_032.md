# VERTEX WORKS 0.3.2 — FORGE UI

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

VERTEX WORKS 0.3.2


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


## 0.3.2 readability + hover stability

### Cargo hover flicker

0.3.1 translated an incoming cargo card by 3 px on hover. When the pointer was
close to the card edge, the element could move out from under the pointer,
dropping `:hover`, moving back, and immediately regaining `:hover`.

That creates a short hover oscillation perceived as an occasional flash.

0.3.2 never moves cargo hit geometry on hover. The reaction is paint-only:

- border emphasis
- background emphasis
- subtle static shadow / inner status line

The pointer target remains spatially fixed.

### Readability

The facility layout is intentionally preserved. Micro typography is enlarged
instead of scaling the entire UI:

- facility rail labels
- metric labels and captions
- panel section labels
- incoming cargo title / filename / ID / path / badges
- Inspector labels and values
- validation / action controls
- Foundry / Works Ledger logs
- process Dock captions

Card padding and metadata rhythm receive a small increase for cleaner scanning.

### Preserved

Official Vertex Project SVG mark, Vertex Blue token layer, NAME / GENRE sorting,
Embedded Vertex Shell, VRA validation, staging, backup, HUMAN_APPLY,
verification, Evidence, Return Lane, rollback, and stale-release protection
remain unchanged.
