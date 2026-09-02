from pathlib import Path
import json

R=Path(r"G:\Vertex_Project\Development\vertex_works")
U=R/"ui"
I=U/"index.html"
J=U/"vertex-works-vxn-browser.js"
C=U/"vertex-works-vxn-browser.css"
CUR=R/"current.json"
ENTRY=R/"VertexWorks.exe"

def q(k,v):
    print(f"{k}={'PASS' if v else 'FAIL'}");return v

i=I.read_text(encoding="utf-8",errors="replace") if I.exists() else ""
j=J.read_text(encoding="utf-8",errors="replace") if J.exists() else ""
c=C.read_text(encoding="utf-8",errors="replace") if C.exists() else ""
cur=json.loads(CUR.read_text(encoding="utf-8")) if CUR.exists() else {}
v=cur.get("vxn_browser") or {}
g=v.get("gpu_affinity") or {}
rv=cur.get("release_exe") or ""
rel=Path(rv) if rv else Path("__missing__")

x=[
 q("ENTRY",ENTRY.exists()),
 q("JS",J.exists()),
 q("CSS",C.exists()),
 q("LINKS","vertex-works-vxn-browser.js" in i and "vertex-works-vxn-browser.css" in i),
 q("VERSION",'const VERSION="000089"' in j),
 q("LOW_POWER",'requestAdapter({powerPreference:"low-power"})' in j),
 q("NO_HIGH_PERF",'powerPreference:"high-performance"' not in j and 'highPerformanceRequested:false' in j),
 q("WEBGPU_BYTE_MAP",'getContext("webgpu")' in j and "GPUBufferUsage.STORAGE" in j),
 q("SOFTWARE_FALLBACK",'CANVAS2D_SOFTWARE' in j and 'getContext("2d")' in j),
 q("GPU_SENSOR","GPU AFFINITY SENSOR" in j),
 q("ADAPTER_CLASS_UNRESOLVED",'adapterClass:"UNRESOLVED"' in j),
 q("RAW",'semanticDecoder:"UNRESOLVED"' in j),
 q("CURRENT",v.get("version")=="000089" and v.get("truth_mode")=="RAW" and v.get("fake_semantics") is False),
 q("POLICY",g.get("policy")=="INTEGRATED_PREFERRED"),
 q("SCOPE",g.get("scope")=="BYTE_MAP_VISUALIZATION"),
 q("LOW_POWER_CURRENT",g.get("webgpu_power_preference")=="low-power"),
 q("HIGH_PERF_FALSE",g.get("high_performance_request") is False),
 q("DGPU_NON_PREFERRED",g.get("dgpu_non_preferred") is True),
 q("FALLBACK",g.get("fallback")=="CANVAS2D_SOFTWARE"),
 q("ACTUAL_RUNTIME_UNRESOLVED",g.get("actual_adapter_class")=="RUNTIME_UNRESOLVED"),
 q("RUNTIME_EVIDENCE_REQUIRED",g.get("runtime_evidence_required") is True),
 q("RELEASE",rel.exists()),
 q("IMMUTABLE","\\versions\\0.5.0\\builds\\" in str(rel).lower())
]
if not all(x):raise SystemExit("VXN_BROWSER_089_VERIFY FAIL")
print("GPU_POLICY=INTEGRATED_PREFERRED")
print("WEBGPU_REQUEST=LOW_POWER")
print("HIGH_PERFORMANCE_REQUEST=FALSE")
print("ACTUAL_ADAPTER_CLASS=RUNTIME_UNRESOLVED")
print("VXN_BROWSER_IGPU_AFFINITY_STATIC_BUILD=PASS")
print("VERTEX_WORKS_VXN_BROWSER_089_VERIFY PASS")
