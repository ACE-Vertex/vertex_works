# Vertex Receiver 0.2.4 — Embedded Vertex Shell

The Receiver no longer needs visible external console windows for verification,
but the actual command stream is now visible inside the application.

## Real stream
For every verification command:
- command line is emitted before process spawn,
- stdout is streamed line by line,
- stderr is streamed line by line,
- real exit status is emitted at completion.

The Evidence result still stores the complete stdout/stderr and exit code.

This is not simulated terminal text. The UI receives Tauri events from the
actual cargo/python/git/npm/etc. child process pipes.

## UI
The lower area shows both:
- VERTEX SHELL — live process stream
- Evidence / Receiver Log — lifecycle and audit log

The header spinner remains the high-level activity indicator.
