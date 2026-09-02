from pathlib import Path
import re,sys
ROOT=Path(r"G:\Vertex_Project\Development")
SKIP={".git","target","node_modules",".idea",".venv","venv","dist","build","versions","MIGRATION_BACKUPS"}
EXT={".rs",".py",".js",".ts",".tsx",".vue",".md",".toml",".json",".yaml",".yml",".h",".hpp",".c",".cpp",".cs"}
def p(v=""):s=str(v);sys.stdout.write(s.encode("ascii","backslashreplace").decode("ascii")+"\n")
def skip(x):return any(q in SKIP for q in x.parts)
p("VERTEX WORKS VXN SOURCE DISCOVERY 000088");p("MODE=READ_ONLY");p("NO_SOURCE_MUTATION=TRUE")
files=[];hits=[];n=0
for f in ROOT.rglob("*"):
    if skip(f) or not f.is_file():continue
    if f.suffix.lower()==".vxn":
        files.append(f)
        if len(files)<=100:
            try:p(f"VXN_FILE {f} SIZE={f.stat().st_size}")
            except:p(f"VXN_FILE {f}")
    if f.suffix.lower() not in EXT:continue
    n+=1
    if n>15000:break
    try:t=f.read_text(encoding="utf-8",errors="replace")
    except:continue
    if not re.search(r"\bvxn\b|vertex native|VXN-",t,re.I):continue
    ls=t.splitlines()
    for i,l in enumerate(ls):
        if re.search(r"\bvxn\b|vertex native|VXN-",l,re.I):hits.append((f,i,ls))
        if len(hits)>=240:break
    if len(hits)>=240:break
p(f"VXN_FILE_COUNT={len(files)}");p(f"TEXT_HITS={len(hits)}")
for label,pat in [("FORMAT",r"format|magic|header|version|schema"),("PARSER",r"parse|decode|reader|read_"),("WRITER",r"encode|serialize|writer|write_"),("TYPE",r"struct|enum|class|type|interface"),("DB",r"vxn[-_ ]?db|dimension|spatial")]:
    p(f"\n=== {label} ===");c=0
    for f,i,ls in hits:
        if not re.search(pat,ls[i],re.I):continue
        p("FILE="+str(f))
        for j in range(max(0,i-3),min(len(ls),i+5)):p(f"{j+1:5}: {ls[j]}")
        p("---");c+=1
        if c>=40:p("...TRUNCATED...");break
    p(f"{label}_BLOCKS={c}")
p("NEXT_PHASE=REAL_SCHEMA_ADAPTER_ONLY");p("VERTEX_WORKS_VXN_SOURCE_DISCOVERY_088 PASS")