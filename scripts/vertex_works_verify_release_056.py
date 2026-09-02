from pathlib import Path
p=Path(r"G:\Vertex_Project\Development\vertex_works\scripts\vertex_works_copy_release_050.py")
t=p.read_text(encoding="utf-8",errors="replace")
checks={
 "IMMUTABLE_BUILD_DIR":'"builds" / stamp' in t,
 "NO_CANONICAL_REPLACE":"release_exe = build_dir" in t,
 "ALIASES_NON_FATAL":"LOCKED_PENDING" in t and "NON_FATAL_ALIAS_ERROR" in t,
 "VERSION_ALIAS_BEST_EFFORT":'best_effort_alias("version_alias"' in t,
 "CURRENT_JSON_POINTS_BUILD":'"release_exe": str(release_exe)' in t,
 "SHA256_RECORDED":"hashlib.sha256" in t,
}
bad=[k for k,v in checks.items() if not v]
for k,v in checks.items():
    print(f"{k}={'PASS' if v else 'FAIL'}")
if bad:
    raise SystemExit("VERTEX_WORKS_RELEASE_056_VERIFY FAIL: "+", ".join(bad))
print("VERTEX_WORKS_RELEASE_056_VERIFY PASS")
