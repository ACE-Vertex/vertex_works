# VERTEX WORKS 0.5.0 — ORANGE WORKSPACE / ENGLISH LOCK PYCOMPAT 000077

000076 failed before any product-source commit because pathlib.Path.write_text()
does not support a `newline=` argument in the deployed Python runtime.

The 000076 transaction restored index.html/current.json and removed the temporary
orange CSS, so the product UI remained unchanged.

000077 is the same source-grounded UI migration with one compatibility change:
all LF-normalized writes use Path.open(..., newline="\n") instead.

Includes:
- VW orange workspace theme
- approved VW product icon in real UI
- HTML English contract
- hidden compatibility language hooks + one-shot English lock
- responsive chrome compression
- RAY / FORGE / Vera handoff preservation checks
- cargo fmt/test/release build
- immutable build publication
- current.json pointer/theme update
- fail-closed restoration
