from pathlib import Path
import re, shutil, subprocess, sys, time

ROOT=Path(r"G:\Vertex_Project\Development\vertex_works")
APP=ROOT/"ui/app.js"
SCOPED=ROOT/"ui/scoped-xray.js"
BACKUP_ROOT=ROOT/"MIGRATION_BACKUPS"/"EXPLORER_EXACT_ROW_BINDING_063"/time.strftime("%Y%m%d-%H%M%S")
BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
APP_BACKUP=BACKUP_ROOT/"app.js"
shutil.copy2(APP, APP_BACKUP)

def run(label,args):
    print(f"\n=== {label} ===")
    cp=subprocess.run(args,cwd=ROOT,text=True)
    if cp.returncode:
        raise RuntimeError(f"{label} failed with exit code {cp.returncode}")

def find_function_block(text, name):
    m=re.search(rf"function\s+{re.escape(name)}\s*\(([^)]*)\)\s*\{{", text)
    if not m:
        raise RuntimeError(f"{name} not found")
    open_pos=m.end()-1
    depth=0
    quote=None
    esc=False
    template=False
    i=open_pos
    while i<len(text):
        c=text[i]
        if quote:
            if esc: esc=False
            elif c=="\\": esc=True
            elif c==quote: quote=None
            i+=1; continue
        if template:
            if esc: esc=False
            elif c=="\\": esc=True
            elif c=="`": template=False
            i+=1; continue
        if c in ("'",'"'):
            quote=c; i+=1; continue
        if c=="`":
            template=True; i+=1; continue
        if c=="{": depth+=1
        elif c=="}":
            depth-=1
            if depth==0:
                return m.start(), i+1, m.group(1), text[m.start():i+1]
        i+=1
    raise RuntimeError(f"{name} block end not found")

text=APP.read_text(encoding="utf-8-sig",errors="strict")

try:
    if "VERTEX_WORKS_EXPLORER_EXACT_ROW_BINDING_063" in text:
        print("APP_EXACT_BINDING_ALREADY_PRESENT PASS")
    else:
        start,end,args,block=find_function_block(text,"xrayBuildFolderRow")

        params=[p.strip().split("=")[0].strip() for p in args.split(",") if p.strip()]
        if "f" not in params:
            raise RuntimeError(f"xrayBuildFolderRow no longer exposes expected folder parameter 'f': {params}")

        create=re.search(
            r"\b(?:const|let)\s+row\s*=\s*document\.createElement\([^;]+;",
            block
        )
        if not create:
            raise RuntimeError("xrayBuildFolderRow row creation statement not found")

        # 000062 incorrectly required f.depth. 000061 already identified
        # xrayBuildFolderRow(f) and row as the exact renderer tuple.
        if "f.name" not in block:
            raise RuntimeError("xrayBuildFolderRow no longer renders f.name; source left untouched")

        binding=(
            "\n  // VERTEX_WORKS_EXPLORER_EXACT_ROW_BINDING_063\n"
            "  row.dataset.xrayPath = f.path;\n"
            "  row.dataset.xrayId = f.id;\n"
            "  row.dataset.xrayRelativePath = f.relative_path;\n"
        )
        patched_block=block[:create.end()] + binding + block[create.end():]
        patched=text[:start]+patched_block+text[end:]
        APP.write_text(patched,encoding="utf-8",newline="\n")
        print("PATCHED function=xrayBuildFolderRow object=f element=row")

    app=APP.read_text(encoding="utf-8",errors="replace")
    scoped=SCOPED.read_text(encoding="utf-8",errors="replace")
    checks={
        "EXACT_RENDERER_MARKER":"VERTEX_WORKS_EXPLORER_EXACT_ROW_BINDING_063" in app,
        "ROW_PATH":"row.dataset.xrayPath = f.path;" in app,
        "ROW_ID":"row.dataset.xrayId = f.id;" in app,
        "ROW_RELATIVE":"row.dataset.xrayRelativePath = f.relative_path;" in app,
        "AUTHORITATIVE_SCOPED_RAY":"resolveAuthoritativeScope" in scoped,
        "NO_POINTER_LABEL_INFERENCE":"candidateLabelsFromPoint" not in scoped,
        "NO_LABEL_RESOLVER":'invoke("xray_resolve_scope"' not in scoped,
        "FAIL_CLOSED":"Development-root fallback is forbidden" in scoped,
    }
    bad=[k for k,v in checks.items() if not v]
    for k,v in checks.items():
        print(f"{k}={'PASS' if v else 'FAIL'}")
    if bad:
        raise RuntimeError("Static contract failed: "+", ".join(bad))

    run("CARGO FMT",["cargo","fmt","--manifest-path",str(ROOT/"src-tauri/Cargo.toml"),"--","--check"])
    run("CARGO TEST",["cargo","test","--manifest-path",str(ROOT/"src-tauri/Cargo.toml")])
    run("RELEASE BUILD",["cargo","build","--release","--manifest-path",str(ROOT/"src-tauri/Cargo.toml")])
    run("COPY IMMUTABLE RELEASE",[sys.executable,str(ROOT/"scripts/vertex_works_copy_release_050.py")])

    print("\nVERTEX_WORKS_EXPLORER_EXACT_ROW_BINDING_063 PASS")
    print("BACKUP",BACKUP_ROOT)

except Exception:
    shutil.copy2(APP_BACKUP,APP)
    print("MIGRATION_RESTORED",APP_BACKUP)
    raise
