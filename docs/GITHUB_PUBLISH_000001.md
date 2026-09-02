# Vertex Works GitHub Publish 000001

Publishes the current local Vertex Works source tree:

`G:\Vertex_Project\Development\vertex_works`

to:

`https://github.com/ACE-FRDS/vertex_works`

## Safety

The publisher:
- initializes Git only if required,
- normalizes the source branch to `main`,
- configures/updates `origin`,
- appends a Vertex source-safety `.gitignore` block,
- excludes build output, immutable releases, backups, binaries, and common local secrets,
- scans staged paths for strong secret/key patterns and GitHub-large-file hazards,
- commits source changes,
- pushes `main`,
- verifies local HEAD equals remote HEAD.

The user explicitly authorized pushing this repository.

This artifact does not contain GitHub credentials.
Local Git authentication must already be available on the Windows workstation.
