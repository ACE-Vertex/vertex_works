# VERTEX WORKS PUBLIC SITE RUNNER HOTFIX 000039

## Why 000038 failed

000038 correctly installed the PowerShell builder and verifier, but its VRA verification command called the verifier immediately.

At that moment the builder had not yet run, therefore:

`G:\Vertex_Project\Development\vertex_works\site\vertex-works-public`

did not exist yet and every required source file failed verification.

The failure was sequencing, not a site-content failure.

## Correct flow

VRA apply
→ canonical public-site source exists
→ Python verification runner
→ PowerShell builder
→ resolve existing IIS binding for `vertex.a-portal.net`
→ backup existing `/vertex-works`
→ deploy
→ preserve access-counter runtime data
→ verify source + deployed copy
→ best-effort HTTP check
→ commit owned site paths
→ push current branch

The VRA verification entry remains on the Receiver allowlist by invoking `python`.
The Python runner delegates the site build/deploy operation to PowerShell.

## Git policy

Commit and push occur only after the builder's source/deployment verification passes.
