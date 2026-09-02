# VERTEX WORKS — CLIP RELAY ERROR PRIORITY HOTFIX 000095

## Root cause

Vertex Clip Relay 000093 wired **Evidence** to the priority relay, but did not wire the separate **Error Report** Return Lane button.

Therefore:

- Evidence button -> Vertex Clip Relay was armed.
- Error Report button -> report was copied to ordinary Windows clipboard only.
- A later middle click in ChatGPT had no armed Vertex payload, so the relay passed the middle click through.

This was not primarily a Windows reservation conflict. It was a missing Return Lane wiring path.

## Fix

000095 arms the same priority relay for Error Report:

`ERROR REPORT -> clip_relay_set_priority(kind="ERROR") -> copyReport()`

Evidence remains:

`EVIDENCE -> clip_relay_set_priority(kind="EVIDENCE") -> copyReport()`

The Rust global hook and selection/release algorithm are unchanged.
