# VERTEX WORKS PUBLIC SITE 000038

Target public URL:

`https://vertex.a-portal.net/vertex-works/`

## Operational model

This follows the same family of approach used for the earlier Vertex Hub public builder:

- PowerShell 7 builder owns generation and deployment.
- IIS configuration and bindings are not modified.
- Existing `vertex.a-portal.net` IIS binding is discovered.
- Existing `/vertex-works` deployment is backed up before replacement.
- Canonical generated source lives inside the `vertex_works` repository under `site/vertex-works-public`.
- Runtime counter data is preserved across redeploys.
- Source and deployed copies are verified before Git closure.
- Git commit/push occurs only after verification and only for paths owned by this site task.

## Counter

`counter.php` prefers SQLite3 and falls back to a locked text counter. Runtime counter data lives in `data/` and is excluded from Git.

## Git policy

Default: commit + push after verification.

The builder stages/commits only:

- `site/vertex-works-public`
- `scripts/build_vertex_works_public_site_000038.ps1`
- `scripts/verify_vertex_works_public_site_000038.py`
- `docs/VERTEX_WORKS_PUBLIC_SITE_000038.md`

Unrelated working-tree or staged changes are not intentionally included.

## Run

```powershell
pwsh -ExecutionPolicy Bypass `
  -File "G:\Vertex_Project\Development\vertex_works\scripts\build_vertex_works_public_site_000038.ps1"
```

Use `-SkipGitPush` only when an intentional local-only run is required.
