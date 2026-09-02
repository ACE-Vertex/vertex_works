# VERTEX WORKS CLIP RELAY PROBE HOTFIX 000091

The original 000090 read-only probe failed only while printing source context to the Windows CP932 console.

Observed failure:

`UnicodeEncodeError: 'cp932' codec can't encode character '\u2014'`

000091 keeps the same read-only inspection logic and changes only terminal output to a CP932-safe path:

- normal print when encodable;
- ASCII `backslashreplace` fallback when not encodable.

No Works source is modified by this probe.

The goal remains to capture the exact current backend/frontend contract before implementing Vertex Clip Relay.
