from __future__ import annotations

import argparse
from pathlib import Path
import sys

REQUIRED = [
    "index.html",
    "styles.css",
    "app.js",
    "counter.php",
    "data/.gitignore",
    "data/README.txt",
]

def check_tree(root: Path, label: str) -> bool:
    ok = True
    print(f"{label}_ROOT={root}")
    for rel in REQUIRED:
        p = root / rel
        passed = p.exists() and p.is_file()
        print(f"{label}_{rel.replace('/', '_').upper()}={'PASS' if passed else 'FAIL'}")
        ok &= passed

    if not ok:
        return False

    index = (root / "index.html").read_text(encoding="utf-8")
    css = (root / "styles.css").read_text(encoding="utf-8")
    app = (root / "app.js").read_text(encoding="utf-8")
    php = (root / "counter.php").read_text(encoding="utf-8")

    checks = {
        "TITLE": "VERTEX WORKS" in index,
        "REFERENCE_PRICE": "¥5,000,000" in index,
        "VERTEX_EXCLUSIVE": "VERTEX EXCLUSIVE" in index,
        "FACILITY_RAY": "RAY" in index and "SEE" in index,
        "FACILITY_FORGE": "FORGE" in index and "BUILD" in index,
        "FACILITY_VXN": "VXN" in index and "FLOW" in index,
        "FACILITY_EVIDENCE": "EVIDENCE" in index and "PROVE" in index,
        "ACCESS_COUNTER_DOM": 'id="visitorCount"' in index,
        "COUNTER_FETCH": "counter.php" in app,
        "COUNTER_STORAGE": "SQLite3" in php and "flock" in php,
        "ORANGE_CORE": "#ff" in css.lower() and "core-ring" in css,
        "NETWORK_ANIMATION": "@keyframes" in css and "network-svg" in index,
        "MOTTO": "流れよ流れ" in index,
        "CLOSE_AND_SHIP": "CLOSE & SHIP" in index,
    }
    for name, passed in checks.items():
        print(f"{label}_{name}={'PASS' if passed else 'FAIL'}")
        ok &= passed
    return ok

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", required=True)
    ap.add_argument("--deploy-root")
    args = ap.parse_args()

    source = Path(args.source_root)
    ok = check_tree(source, "SOURCE")

    if args.deploy_root:
        deploy = Path(args.deploy_root)
        ok &= check_tree(deploy, "DEPLOY")

        if ok:
            for rel in REQUIRED:
                a = (source / rel).read_bytes()
                b = (deploy / rel).read_bytes()
                same = a == b
                print(f"MATCH_{rel.replace('/', '_').upper()}={'PASS' if same else 'FAIL'}")
                ok &= same

    print(f"VERTEX_WORKS_PUBLIC_SITE_000038_VERIFY={'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
