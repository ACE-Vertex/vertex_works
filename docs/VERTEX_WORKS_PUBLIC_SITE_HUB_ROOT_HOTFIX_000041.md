# VERTEX WORKS PUBLIC SITE — HUB ROOT HOTFIX 000041

## Root cause of 000040

000040 removed the hard dependency on `WebAdministration`, but `appcmd.exe` still required IIS administration access to enumerate sites.

The Works verification process does not need IIS administration access at all.

## Existing proven public-site architecture

The existing Vertex Hub public builder defines:

`G:\Vertex_Project\Development\vertex_studio_ai\VertexHub\site`

as its generated public site root and records that path as `physicalPath` in:

`VertexHub\deployment.json`

Therefore Vertex Works should use the established Hub public root instead of attempting to rediscover IIS configuration.

## 000041 deployment

The builder now resolves the public root from:

1. `VertexHub\deployment.json` → `physicalPath`, when valid.
2. Fallback: `G:\Vertex_Project\Development\vertex_studio_ai\VertexHub\site`

Then deploys:

`<HubPublicRoot>\vertex-works`

for:

`https://vertex.a-portal.net/vertex-works/`

No `WebAdministration` and no `appcmd.exe` are used.

## Closure

VRA
→ canonical source
→ PowerShell builder
→ existing Vertex Hub public root
→ backup old route
→ preserve counter runtime data
→ deploy
→ source/deploy verification
→ public HTTP check
→ commit/push `vertex_works`
→ commit/push `vertex_studio_ai` Hub route

000038 / 000039 / 000040 remain failed Evidence runs.
000041 supersedes their deployment strategy.
