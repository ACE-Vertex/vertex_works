# VERTEX WORKS — TYPOGRAPHY +1pt 000096

Requested visual adjustment:

> 全体的にFONT 1ptアップ

This migration raises every simple explicit UI `font-size` declaration by exactly `1pt` using CSS `calc(...)`.

Examples:

- `font-size: 11px;` -> `font-size: calc(11px + 1pt);`
- `font-size: 0.8rem;` -> `font-size: calc(0.8rem + 1pt);`

Scope is intentionally limited to typography. Layout geometry, panel sizes, spacing, colors, and the Vertex amber/dark theme are not changed.

The patch is idempotent through a source marker and creates a migration backup before modification.
