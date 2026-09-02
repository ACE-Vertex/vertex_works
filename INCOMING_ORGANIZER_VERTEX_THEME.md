# Vertex Receiver 0.2.5 — Incoming Organizer + Vertex Theme

## Incoming sorting

The Incoming list intentionally stays lightweight.

- **NAME**
  - sorts by the actual `.vra` filename
  - numeric-aware / case-insensitive
- **GENRE**
  - groups by artifact family, then filename
  - genres:
    - RECEIVER
    - vCELL
    - vSCOPE
    - VXN / NATIVE
    - VSA
    - VERTEX
    - INVALID

The selected mode is remembered with `localStorage`.

Genre is derived from the existing artifact ID / title / target. No VRA schema
change is required.

## Vertex CSS format

`ui/vertex-theme.css` is the supplied Vertex FM ENGINE default color palette,
used as the shared Vertex Blue token layer.

The Receiver root uses:

```html
<html data-theme="vertex">
```

Receiver component CSS now consumes `--vertex-*` variables instead of carrying
a separate hard-coded dark palette.

This keeps the Receiver visually aligned with the broader Vertex product family
without coupling Receiver behavior to FM ENGINE.

## Compatibility

The Receiver security / staging / backup / verification / evidence / rollback /
embedded Vertex Shell behavior from 0.2.4 is preserved.

0.2.5 only adds Incoming organization, genre metadata, and theme normalization.


## 0.2.6 hotfix

The 0.2.5 Receiver report exposed a Rust ownership-order bug in `scan_inbox`.

`manifest.artifact_id`, `manifest.title`, and `manifest.target.project_root`
were moved into `ArtifactSummary` before `artifact_genre(...)` borrowed them.

0.2.6 computes `genre` first, then moves those Strings into the summary. No
clone is required.

The report also exposed stale-release copying: the copy script could reuse an
older `target/release/vertex-receiver.exe` after a failed build.

0.2.6 deletes the previous release executable immediately before the release
build. If the build fails, the copy step fails closed instead of publishing an
older executable under a new version.

Incoming NAME / GENRE sorting and the shared Vertex Blue CSS theme are unchanged.
