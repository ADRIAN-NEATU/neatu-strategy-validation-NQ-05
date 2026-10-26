"""Block any commit or upload that contains private strategy details.

The forbidden strings live in a private TOML file kept OUTSIDE this folder (or in git-ignored config/private.toml),
so the list itself is never published.
  python tools/check_private.py --private PATH            scan every file in the repo
  python tools/check_private.py --private PATH --staged   scan only files staged for commit
PATH defaults to config/private.toml. Exit code 1 if anything is found."""
import pathlib
import subprocess
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache"}


def private_path():
    if "--private" in sys.argv:
        return pathlib.Path(sys.argv[sys.argv.index("--private") + 1])
    return ROOT / "config" / "private.toml"


def forbidden_strings():
    path = private_path()
    if not path.exists():
        print(f"WARNING: private file {path} not found; nothing to check against")
        return []
    return [s for s in tomllib.loads(path.read_text(encoding="utf-8")).get("forbidden", {}).get("strings", []) if s]


def candidate_files(staged):
    if staged:
        out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.split()
        return [ROOT / p for p in out]
    return [p for p in ROOT.rglob("*") if p.is_file() and not (set(p.relative_to(ROOT).parts) & SKIP_DIRS)]


def main():
    words = forbidden_strings()
    hits = []
    staged = "--staged" in sys.argv
    for f in candidate_files(staged):
        rel = f.relative_to(ROOT).as_posix()
        if rel == "config/private.toml":
            if staged:          # it lives here on purpose; it must just never be committed
                hits.append((rel, "the private file itself must never be committed"))
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        hits += [(rel, w) for w in words if w.lower() in text]
    for rel, w in hits:
        print(f"PRIVATE DETAIL in {rel}: {w!r}")
    print("check_private: " + ("FAILED" if hits else "clean"))
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
