from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
REMOTE = "https://github.com/ACE-FRDS/vertex_works.git"
BRANCH = "main"

# This is the exact remote HEAD observed during diagnosis.
# It is the GitHub-created one-line README "Initial commit".
EXPECTED_REMOTE_INITIAL = "f8bf34b51021de6fe6695614b1641cbe2df25762"

STRONG_SECRET_PATTERNS = [
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(rb"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
]

BLOCKED_NAMES = {
    ".env", "credentials.json", "secrets.json",
    "id_rsa", "id_ed25519",
}
BLOCKED_SUFFIXES = {
    ".pem", ".key", ".p12", ".pfx",
    ".exe", ".dll", ".pdb", ".msi", ".msix", ".appx",
    ".dmg", ".pkg", ".zip", ".7z", ".rar",
}
MAX_BYTES = 95 * 1024 * 1024

def run(args, check=True):
    result = subprocess.run(
        [str(a) for a in args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.stdout.strip():
        print(result.stdout.rstrip())
    if result.stderr.strip():
        print(result.stderr.rstrip())
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result

def ensure_remote():
    remotes = run(["git", "remote"]).stdout.split()
    if "origin" in remotes:
        run(["git", "remote", "set-url", "origin", REMOTE])
    else:
        run(["git", "remote", "add", "origin", REMOTE])
    print("REMOTE_ORIGIN=PASS")

def tracked_source_paths():
    result = run(["git", "ls-files", "-z"])
    return [item for item in result.stdout.split("\0") if item]

def safety_scan(paths):
    problems = []
    for rel in paths:
        p = ROOT / rel
        if not p.exists() or not p.is_file():
            continue

        name = p.name.lower()
        suffix = p.suffix.lower()

        if name in BLOCKED_NAMES:
            problems.append(f"SENSITIVE_PATH {rel}")
            continue
        if suffix in BLOCKED_SUFFIXES:
            problems.append(f"BLOCKED_BINARY_OR_SECRET_SUFFIX {rel}")
            continue

        size = p.stat().st_size
        if size > MAX_BYTES:
            problems.append(f"TOO_LARGE {size} {rel}")
            continue

        if size <= 4 * 1024 * 1024:
            try:
                data = p.read_bytes()
            except OSError:
                continue
            if any(pattern.search(data) for pattern in STRONG_SECRET_PATTERNS):
                problems.append(f"STRONG_SECRET_PATTERN {rel}")

    if problems:
        print("SOURCE_SAFETY_SCAN=BLOCKED")
        for item in problems:
            print(item)
        raise SystemExit(17)

    print(f"SOURCE_SAFETY_SCAN=PASS ({len(paths)} tracked paths)")

def remote_head():
    result = run(
        ["git", "ls-remote", "origin", f"refs/heads/{BRANCH}"],
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    line = result.stdout.strip()
    return line.split()[0] if line else ""

def commit_fmt_if_needed():
    cargo = shutil.which("cargo")
    if not cargo:
        print("CARGO_NOT_FOUND")
        raise SystemExit(3)

    # Fix the 000026 rustfmt-only failure before publishing the source.
    run([
        cargo, "fmt",
        "--manifest-path", str(ROOT / "src-tauri" / "Cargo.toml")
    ])
    print("CARGO_FMT_APPLY=PASS")

    run(["git", "add", "-A"])

    status = run(["git", "status", "--short"]).stdout.strip()
    if status:
        commit = run(
            ["git", "commit", "-m",
             "Finalize Works refinement formatting before GitHub publish"],
            check=False,
        )
        if commit.returncode != 0:
            raise SystemExit(commit.returncode)
        print("FORMAT_HOTFIX_COMMIT=PASS")
    else:
        print("FORMAT_HOTFIX_COMMIT=NO_CHANGES")

def verify_local():
    run([
        "cargo", "fmt",
        "--manifest-path", str(ROOT / "src-tauri" / "Cargo.toml"),
        "--", "--check"
    ])
    print("CARGO_FMT_CHECK=PASS")

    run([
        "cargo", "test",
        "--manifest-path", str(ROOT / "src-tauri" / "Cargo.toml")
    ])
    print("CARGO_TEST=PASS")

    run([
        "cargo", "build",
        "--manifest-path", str(ROOT / "src-tauri" / "Cargo.toml")
    ])
    print("CARGO_BUILD=PASS")

def publish():
    ensure_remote()
    run(["git", "branch", "-M", BRANCH])

    # Fetch first so diagnostics/audit show exactly what exists remotely.
    run(["git", "fetch", "origin", BRANCH], check=False)

    local = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    remote = remote_head()

    print(f"LOCAL_HEAD_BEFORE_PUSH={local}")
    print(f"REMOTE_HEAD_BEFORE_PUSH={remote or 'ABSENT'}")

    if remote == local:
        print("REMOTE_ALREADY_CURRENT=PASS")
        return

    if not remote:
        run(["git", "push", "-u", "origin", BRANCH])
        print("NORMAL_PUSH=PASS")
        return

    if remote != EXPECTED_REMOTE_INITIAL:
        print("REMOTE_HEAD_CHANGED_UNEXPECTEDLY=BLOCK")
        print(f"EXPECTED_INITIAL={EXPECTED_REMOTE_INITIAL}")
        print(f"ACTUAL_REMOTE={remote}")
        raise SystemExit(23)

    # The remote consists only of GitHub's trivial initial README commit.
    # Replace it, but only if it is STILL exactly that commit.
    lease = f"refs/heads/{BRANCH}:{EXPECTED_REMOTE_INITIAL}"
    run([
        "git", "push",
        "--force-with-lease=" + lease,
        "-u", "origin", BRANCH
    ])
    print("FORCE_WITH_LEASE_INITIAL_COMMIT_REPLACEMENT=PASS")

def verify_remote():
    local = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    remote = remote_head()
    print(f"LOCAL_HEAD={local}")
    print(f"REMOTE_HEAD={remote}")
    ok = bool(local and remote and local == remote)
    print(f"HEAD_MATCH={'PASS' if ok else 'FAIL'}")
    if not ok:
        raise SystemExit(29)
    print("VERTEX_WORKS_GITHUB_PUBLISH_HOTFIX_000002=PASS")

def main():
    if not ROOT.exists() or not (ROOT / ".git").exists():
        print("LOCAL_GIT_REPOSITORY_MISSING")
        raise SystemExit(2)

    commit_fmt_if_needed()
    safety_scan(tracked_source_paths())
    verify_local()
    publish()
    verify_remote()

if __name__ == "__main__":
    main()
