from pathlib import Path
import json

root=Path(r"G:\Vertex_Project\Development\vertex_works")
v57=(root/"scripts/vertex_works_verify_scoped_scope_057.py")
v55=(root/"scripts/vertex_works_verify_scoped_scope_055.py")

checks={
 "POINTER_EXACT_VERIFIER_PRESENT": v57.exists(),
 "LEGACY_055_MAY_REMAIN_AS_HISTORY": v55.exists(),
 "CURRENT_JS_USES_057": "candidateLabelsFromPoint" in (root/"ui/scoped-xray.js").read_text(encoding="utf-8",errors="replace"),
}
bad=[k for k,v in checks.items() if not v]
for k,v in checks.items():
    print(f"{k}={'PASS' if v else 'FAIL'}")
if bad:
    raise SystemExit("VERTEX_WORKS_VERIFY_CHAIN_058 FAIL: "+", ".join(bad))
print("VERTEX_WORKS_VERIFY_CHAIN_058 PASS")
