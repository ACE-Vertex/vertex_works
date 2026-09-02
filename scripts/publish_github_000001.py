from pathlib import Path
import os
import re
import shutil
import subprocess
import sys

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
REMOTE = "https://github.com/ACE-FRDS/vertex_works.git"
BRANCH = "main"
BLOCK_BEGIN = "# >>> VERTEX SOURCE REPOSITORY SAFETY >>>"
BLOCK_END = "# <<< VERTEX SOURCE REPOSITORY SAFETY <<<"

IGNORE_BLOCK = r"""
# >>> VERTEX SOURCE REPOSITORY SAFETY >>>
# Build/cache/runtime output
target/
**/target/
node_modules/
**/node_modules/
dist/
build/
.vite/
.tauri/
versions/
MIGRATION_BACKUPS/

# Generated/release binaries
*.exe
*.dll
*.pdb
*.msi
*.msix
*.appx
*.dmg
*.pkg
*.pending

# Local logs/temp
*.log
*.tmp
*.bak
.DS_Store
Thumbs.db

# Local secrets / credentials
.env
.env.*
!.env.example
!.env.sample
*.pem
*.key
*.p12
*.pfx
id_rsa
id_ed25519
credentials.json
secrets.json
# <<< VERTEX SOURCE REPOSITORY SAFETY <<<
""".strip() + "\n"

STRONG_SECRET_PATTERNS = [
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(rb"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
]

BLOCKED_PATH_PARTS = {
    ".env", "credentials.json", "secrets.json",
    "id_rsa", "id_ed25519"
}
BLOCKED_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
BINARY_SUFFIXES = {
    ".exe", ".dll", ".pdb", ".msi", ".msix", ".appx",
    ".dmg", ".pkg", ".zip", ".7z", ".rar"
}
MAX_GITHUB_BYTES = 95 * 1024 * 1024

def run(args, check=True, capture=True):
    cmd = [str(a) for a in args]
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if capture:
        if result.stdout.strip():
            print(result.stdout.rstrip())
        if result.stderr.strip():
            print(result.stderr.rstrip())
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result

def ensure_ignore():
    path = ROOT / ".gitignore"
    existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    if BLOCK_BEGIN in existing and BLOCK_END in existing:
        print("GITIGNORE_VERTEX_BLOCK=ALREADY_PRESENT")
        return
    if existing and not existing.endswith("\n"):
        existing += "\n"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(existing)
        if existing:
            handle.write("\n")
        handle.write(IGNORE_BLOCK)
    print("GITIGNORE_VERTEX_BLOCK=ADDED")

def ensure_git():
    if not (ROOT / ".git").exists():
        run(["git", "init", "-b", BRANCH])
        print("GIT_INIT=PASS")
    else:
        print("GIT_INIT=EXISTING")

    # Normalize the publishing branch for the new public source repository.
    run(["git", "branch", "-M", BRANCH])

    remotes = run(["git", "remote"], capture=True).stdout.split()
    if "origin" in remotes:
        run(["git", "remote", "set-url", "origin", REMOTE])
        print("REMOTE_ORIGIN=UPDATED")
    else:
        run(["git", "remote", "add", "origin", REMOTE])
        print("REMOTE_ORIGIN=ADDED")

    name = run(["git", "config", "--get", "user.name"], check=False).stdout.strip()
    email = run(["git", "config", "--get", "user.email"], check=False).stdout.strip()
    if not name:
        run(["git", "config", "user.name", "ACE-FRDS"])
        print("GIT_USER_NAME=LOCAL_FALLBACK")
    if not email:
        run(["git", "config", "user.email", "ACE-FRDS@users.noreply.github.com"])
        print("GIT_USER_EMAIL=LOCAL_FALLBACK")

def staged_files():
    result = run(["git", "diff", "--cached", "--name-only", "-z"])
    raw = result.stdout
    return [p for p in raw.split("\0") if p]

def safety_scan(paths):
    problems = []
    for rel in paths:
        path = ROOT / rel
        parts_lower = {p.lower() for p in Path(rel).parts}
        name_lower = path.name.lower()
        suffix_lower = path.suffix.lower()

        if name_lower in BLOCKED_PATH_PARTS or suffix_lower in BLOCKED_SUFFIXES:
            problems.append(f"SENSITIVE_PATH {rel}")
            continue

        if suffix_lower in BINARY_SUFFIXES:
            problems.append(f"BINARY_ARCHIVE_PATH {rel}")
            continue

        if not path.exists() or not path.is_file():
            continue

        size = path.stat().st_size
        if size > MAX_GITHUB_BYTES:
            problems.append(f"TOO_LARGE {size} {rel}")
            continue

        # Strong token/key scan only. Avoid broad "password=" patterns that
        # would create false positives in application source and documentation.
        if size <= 4 * 1024 * 1024:
            try:
                data = path.read_bytes()
            except OSError:
                continue
            for pattern in STRONG_SECRET_PATTERNS:
                if pattern.search(data):
                    problems.append(f"STRONG_SECRET_PATTERN {rel}")
                    break

    if problems:
        print("SOURCE_SAFETY_SCAN=BLOCKED")
        for item in problems:
            print(item)
        raise SystemExit(17)

    print(f"SOURCE_SAFETY_SCAN=PASS ({len(paths)} staged paths)")

def main():
    if not ROOT.exists():
        print(f"ROOT_MISSING={ROOT}")
        raise SystemExit(2)

    if shutil.which("git") is None:
        print("GIT_NOT_FOUND")
        raise SystemExit(3)

    ensure_ignore()
    ensure_git()

    run(["git", "add", "-A"])
    files = staged_files()
    safety_scan(files)

    status = run(["git", "status", "--short"]).stdout.strip()
    if status:
        commit = run(
            ["git", "commit", "-m",
             "Publish Vertex Works source and current Works architecture"],
            check=False,
        )
        if commit.returncode not in (0, 1):
            raise SystemExit(commit.returncode)

        # git commit returns 1 for "nothing to commit" in some situations.
        if commit.returncode == 0:
            print("GIT_COMMIT=PASS")
        else:
            print("GIT_COMMIT=NO_CHANGES")
    else:
        print("GIT_COMMIT=NO_CHANGES")

    # Public repository is confirmed to exist. Push only the source branch.
    push = run(["git", "push", "-u", "origin", BRANCH], check=False)
    if push.returncode != 0:
        print("GIT_PUSH=FAIL")
        print("If authentication is requested, configure Git/GitHub credentials on this PC and rerun this publisher.")
        raise SystemExit(push.returncode)

    print("GIT_PUSH=PASS")

    head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    remote = run(["git", "ls-remote", "origin", f"refs/heads/{BRANCH}"]).stdout.strip()
    remote_sha = remote.split()[0] if remote else ""

    print(f"LOCAL_HEAD={head}")
    print(f"REMOTE_HEAD={remote_sha}")
    print(f"HEAD_MATCH={'PASS' if head and head == remote_sha else 'FAIL'}")
    if not head or head != remote_sha:
        raise SystemExit(19)

    print("VERTEX_WORKS_GITHUB_PUBLISH_000001=PASS")

if __name__ == "__main__":
    main()
