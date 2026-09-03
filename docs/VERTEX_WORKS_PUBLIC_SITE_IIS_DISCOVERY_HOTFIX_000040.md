# VERTEX WORKS PUBLIC SITE IIS DISCOVERY HOTFIX 000040

## Failure in 000039

000039 reached the PowerShell builder correctly, but PowerShell 7 could not load the legacy IIS `WebAdministration` module.

That made IIS discovery fail before deployment.

## Fix

IIS discovery is now dual-path:

1. Try `WebAdministration` when available.
2. Fall back to native IIS `appcmd.exe` from:
   `%WINDIR%\System32\inetsrv\appcmd.exe`

The fallback resolves:

- IIS site name
- bindings
- physical site root
- application pool

for the site whose binding matches:

`vertex.a-portal.net`

No IIS binding or configuration is modified.

## Full closure

VRA apply
→ source present
→ Python runner
→ PowerShell builder
→ IIS discovery (WebAdministration or appcmd)
→ backup `/vertex-works`
→ deploy
→ preserve counter runtime data
→ verify source/deploy
→ best-effort HTTPS check
→ commit owned paths
→ push

000038 and 000039 remain failed Evidence runs. 000040 supersedes their execution path.
