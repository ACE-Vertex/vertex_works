# Vertex Receiver — GENESIS v0.1.0

Vertex Receiver is the first general AI Artifact Ingress for Vertex World.

## GENESIS flow

`AI / LLM → .vra → Receiver → Validate → Stage → Backup → Human Apply → Verify → Evidence`

The first version intentionally keeps Human Apply.

## Default paths

- Inbox: `G:\Vertex_Project\_incoming\vertex_works`
- Allowed project root: `G:\Vertex_Project\Development`
- Receiver evidence/staging/backups: `%LOCALAPPDATA%\VertexReceiver`

## VRA format

A `.vra` file is a ZIP container with:

- `manifest.json`
- `payload/...`

Each payload file has a SHA-256 in the manifest.

GENESIS only accepts:
- `copy` operations
- relative payload/destination paths
- targets inside the Vertex Development root
- `authority = HUMAN_APPLY`
- verification programs from an allowlist

## Desktop app

The app is Tauri + Rust with a static embedded UI.
After the one-time GENESIS bootstrap, run:

`G:\Vertex_Project\Development\vertex_works\VertexReceiver.exe`

Future `.vra` artifacts are detected automatically in the Receiver inbox.

## Important boundary

GENESIS does not execute arbitrary artifact scripts.
It is deliberately an artifact receiver, not an unrestricted remote shell.
