from pathlib import Path
import json,hashlib,shutil,subprocess,sys
from datetime import datetime

R=Path(r"G:\Vertex_Project\Development\vertex_works")
U=R/"ui"
I=U/"index.html"
J=U/"vertex-works-vxn-browser.js"
C=U/"vertex-works-vxn-browser.css"
CUR=R/"current.json"
CAR=R/"src-tauri"/"Cargo.toml"
BUILT=R/"src-tauri"/"target"/"release"/"vertex-receiver.exe"

def p(v=""):
    s=str(v);sys.stdout.write(s.encode("ascii","backslashreplace").decode("ascii")+"\n")
def wr(x,t):
    with x.open("w",encoding="utf-8",newline="\n") as f:f.write(t)
def sh(x):
    h=hashlib.sha256()
    with x.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def run(a):
    z=subprocess.run(a,text=True,capture_output=True)
    p("RUN "+" ".join(map(str,a)));p(z.stdout);p(z.stderr)
    if z.returncode:raise RuntimeError("COMMAND_FAILED")

for x in [I,J,C,CUR,CAR]:
    if not x.exists():raise SystemExit("MISSING "+str(x))

idx=I.read_text(encoding="utf-8")
js=J.read_text(encoding="utf-8")
css=C.read_text(encoding="utf-8")

for a in ["vertex-works-factory-kernel.js","vertex-works-ray-contract.js","vertex-works-ray-orange.css"]:
    if a not in idx:raise RuntimeError("UI_CONTRACT_MISSING "+a)

stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
bak=R/"MIGRATION_BACKUPS"/"VXN_BROWSER_IGPU_089"/stamp
bak.mkdir(parents=True)
shutil.copy2(I,bak/"index.html")
shutil.copy2(CUR,bak/"current.json")

cl='<link rel="stylesheet" href="vertex-works-vxn-browser.css" />'
jl='<script src="vertex-works-vxn-browser.js"></script>'

p("VERTEX WORKS VXN BROWSER iGPU AFFINITY 000089")
p("GPU_POLICY=INTEGRATED_PREFERRED")
p("WEBGPU_POWER_PREFERENCE=LOW_POWER")
p("HIGH_PERFORMANCE_REQUEST=FALSE")
p("FALLBACK=CANVAS2D_SOFTWARE")
p("ACTUAL_ADAPTER_CLASS=RUNTIME_UNRESOLVED")

try:
    if cl not in idx:idx=idx.replace("</head>","  "+cl+"\n</head>",1)
    if jl not in idx:idx=idx.replace("</body>","  "+jl+"\n</body>",1)
    wr(I,idx)

    checks={
      "VERSION":'const VERSION="000089"' in js,
      "VXN_NAV":'dataset.facility="VXN"' in js,
      "LOW_POWER":'requestAdapter({powerPreference:"low-power"})' in js,
      "NO_HIGH_PERF":'highPerformanceRequested:false' in js and 'powerPreference:"high-performance"' not in js,
      "WEBGPU":'getContext("webgpu")' in js and "GPUBufferUsage.STORAGE" in js,
      "CANVAS_FALLBACK":'CANVAS2D_SOFTWARE' in js and 'getContext("2d")' in js,
      "GPU_SENSOR":'GPU AFFINITY SENSOR' in js,
      "UNRESOLVED_CLASS":'adapterClass:"UNRESOLVED"' in js,
      "CLIP_GPU":'requestedPowerPreference:G.requestedPowerPreference' in js,
      "RAW_TRUTH":'semanticDecoder:"UNRESOLVED"' in js,
      "ORANGE":"--vw-vxn-orange:#ff8a2a" in css
    }
    for k,v in checks.items():p(f"{k}={'PASS' if v else 'FAIL'}")
    if not all(checks.values()):raise RuntimeError("CONTRACT_FAIL")

    run(["cargo","fmt","--manifest-path",str(CAR),"--","--check"])
    run(["cargo","test","--manifest-path",str(CAR)])
    run(["cargo","build","--release","--manifest-path",str(CAR)])

    d=R/"versions"/"0.5.0"/"builds"/datetime.now().strftime("%Y%m%d-%H%M%S")
    d.mkdir(parents=True)
    exe=d/"VertexWorks_0.5.0.exe"
    shutil.copy2(BUILT,exe)
    h=sh(exe)

    cur=json.loads(CUR.read_text(encoding="utf-8"))
    prev=cur.get("release_exe") or cur.get("executable")
    cur["release_exe"]=str(exe)
    cur["sha256"]=h
    cur["updated_at"]=datetime.now().isoformat(timespec="seconds")
    cur["vxn_browser"]={
      "version":"000089",
      "facility":"VXN",
      "truth_mode":"RAW",
      "semantic_decoder":"UNRESOLVED",
      "fake_semantics":False,
      "capabilities":["OPEN","HEX","UTF8","STRINGS","RANGE","SHA256","BYTE_MAP","DIFF","CLIP_TO_VERA"],
      "project_source_discovery":True,
      "gpu_affinity":{
        "policy":"INTEGRATED_PREFERRED",
        "scope":"BYTE_MAP_VISUALIZATION",
        "webgpu_power_preference":"low-power",
        "high_performance_request":False,
        "dgpu_non_preferred":True,
        "fallback":"CANVAS2D_SOFTWARE",
        "actual_adapter_class":"RUNTIME_UNRESOLVED",
        "runtime_evidence_required":True
      }
    }
    cur["ui_phase"]="VXN_BROWSER_IGPU_AFFINITY_000089"
    wr(CUR,json.dumps(cur,ensure_ascii=False,indent=2)+"\n")
    p("NEW_IMMUTABLE_RELEASE="+str(exe))
    p("NEW_RELEASE_SHA256="+h)
    p("PREVIOUS_RELEASE="+str(prev))
    p("CURRENT_JSON_UPDATED=PASS")
    p("VXN_BROWSER_GPU_AFFINITY=ACTIVE_REQUEST_PATH")
    p("VERTEX_WORKS_VXN_BROWSER_089 PASS")
except Exception:
    shutil.copy2(bak/"index.html",I)
    shutil.copy2(bak/"current.json",CUR)
    p("MIGRATION_RESTORED="+str(bak))
    raise
