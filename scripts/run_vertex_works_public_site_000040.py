from __future__ import annotations

from pathlib import Path
import subprocess

WORKS_ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
BUILDER = WORKS_ROOT / "scripts" / "build_vertex_works_public_site_000038.ps1"

if not BUILDER.exists():
    print(f"BUILDER_EXISTS=FAIL {BUILDER}")
    raise SystemExit(1)

print(f"BUILDER_EXISTS=PASS {BUILDER}")
print("RUNNER_MODE=POWERSHELL_BUILDER")
print("RUNNER_IIS_DISCOVERY=WEBADMINISTRATION_OR_APPCMD")
print("RUNNER_TARGET=https://vertex.a-portal.net/vertex-works/")
print("RUNNER_GIT_POLICY=VERIFY_THEN_COMMIT_PUSH")

cmd = [
    "pwsh",
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    str(BUILDER),
    "-WorksRoot",
    str(WORKS_ROOT),
    "-HostName",
    "vertex.a-portal.net",
    "-Route",
    "vertex-works",
]

proc = subprocess.run(cmd, cwd=str(WORKS_ROOT))
print(f"BUILDER_EXIT_CODE={proc.returncode}")

if proc.returncode != 0:
    print("VERTEX_WORKS_PUBLIC_SITE_000040=FAIL")
    raise SystemExit(proc.returncode)

print("VERTEX_WORKS_PUBLIC_SITE_000040=PASS")
