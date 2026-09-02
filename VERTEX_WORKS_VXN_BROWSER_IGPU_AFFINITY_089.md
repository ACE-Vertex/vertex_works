# VERTEX WORKS — VXN BROWSER iGPU AFFINITY 000089

## Policy

VXN Browser visualization should preserve the discrete GPU for heavy Vertex workloads.

Preferred flow:

VXN raw observation
-> WebGPU adapter request with `powerPreference: "low-power"`
-> Byte Map visualization
-> fallback to Canvas2D/software if low-power WebGPU is unavailable

The implementation NEVER requests `high-performance`.

## Scope

000089 controls the VXN Browser Byte Map visualization workload. It does not claim
to control WebView2's entire compositor or the rest of Vertex Works.

## Truth contract

`low-power` is a preference hint. It is not proof of iGPU selection.

Therefore:
- policy = INTEGRATED_PREFERRED
- requested power preference = low-power
- dGPU = non-preferred
- actual adapter class = RUNTIME_UNRESOLVED until evidence exists

CLIP TO VERA includes GPU policy/backend/adapter information for later verification.

This artifact absorbs the 000088 VXN Browser foundation source so it can be applied
even if 000088 was not previously activated.
