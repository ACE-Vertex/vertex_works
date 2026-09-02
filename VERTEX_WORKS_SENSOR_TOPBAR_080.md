# VERTEX WORKS — SENSOR BUS TOPBAR INTEGRATION 000080

Purpose:
Move the real Sensor Bus away from the lower-right work surface and integrate it
into the common Vertex Works top bar.

Why:
The 000079 runtime screenshot showed the Sensor Bus covering the CLIP TO VERA action.
Observation mechanisms must never obstruct the workflow they observe.

Contract:
- Sensor Bus host: #vertexModeBar
- Insert immediately before #settingsBtn when possible
- No fixed bottom-right dock
- Detail panel opens downward from the top bar
- RAY/FORGE workspace tracking preserved
- Existing inspection checks preserved
- Adds SENSOR_TOPBAR_HOST inspection
- CLIP TO VERA clearance is a product requirement
- Sensor remains low-frequency 1500 ms real observation
- No fake telemetry
