# VERTEX WORKS — SENSOR BUS / INSPECTION GATE 000079

Purpose:
Install a real observation and inspection mechanism into the running Vertex Works UI.

Runtime sensors:
- frame interval (requestAnimationFrame)
- event-loop drift
- DOM node count
- optional Chromium heap usage
- viewport
- active workspace
- online / visibility state
- captured runtime errors / unhandled promise rejections

Inspection Gate:
- English document contract
- VW product identity
- Orange theme loaded
- VW brand icon healthy
- RAY present
- FORGE present
- Vera handoff control present
- duplicate DOM IDs
- visible Japanese text
- horizontal overflow
- broken images
- captured runtime errors

Design:
- No fake telemetry.
- Low-frequency sampling: 1500 ms.
- Inspection can be run on demand.
- Compact floating Sensor Bus dock; detailed panel only when opened.
- Existing RAY / FORGE / Clip-to-Vera flows are not replaced.
- Semantic success/failure colors remain distinct from the Orange product accent.

The first inspection is expected to expose remaining visible Japanese in Forge until
the native-English cleanup phase is completed. That is a real FAIL signal, not a defect
in the sensor.
