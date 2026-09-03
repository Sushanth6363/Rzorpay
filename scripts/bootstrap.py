#!/usr/bin/env python3
"""One-command environment bootstrap — makes `make test` work from a cold clone.

THE PROBLEM THIS SOLVES
    The scientific stack this project pins (CatBoost, NumPy, SciPy, scikit-learn) ships
    compiled wheels per Python version. On a Python the wheels do not cover — notably 3.14,
    which is newer than the pins — a bare `pip install` fails to build them and `pytest`
    then collects a broken project. A judge who clones and runs `pytest` on whatever
    `python` happens to be on their PATH sees failures that have nothing to do with the
    code.

WHAT IT DOES
    1. Finds an interpreter in the supported range (3.11–3.13; 3.12 recommended), preferring
       the one running this script if it already qualifies.
    2. Creates `.venv` with it (reuses an existing `.venv`; never clobbers).
    3. Installs the pinned requirements INTO that venv.
    4. Prints exactly what to run next.

    Pure standard library, so it runs even on an unsupported interpreter — its whole job is
    to hand off to a supported one. If none is installed it says so plainly, with no partial
    or broken venv left behind.

    Usage:
        python scripts/bootstrap.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"

# Inclusive supported range. The suite is validated on 3.12; 3.11 and 3.13 have wheel
# coverage for the pinned stack. 3.14 does not, which is the exact trap this guards.
MIN_VERSION = (3, 11)
MAX_VERSION = (3, 13)
RECOMMENDED = "3.12"


def version_supported(version: tuple[int, int]) -> bool:
    return MIN_VERSION <= version <= MAX_VERSION


def venv_python(venv: Path) -> Path:
    """Path to the interpreter inside a venv, per platform."""
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _probe(cmd: list[str]) -> tuple[int, int] | None:
    """Return (major, minor) for an interpreter command, or None if it cannot be run."""
    try:
        out = subprocess.run(
            cmd + ["-c", "import sys; print('%d.%d' % sys.version_info[:2])"],
            capture_output=True, text=True, timeout=15,
        )
    except Exception:
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    try:
        major, minor = (int(p) for p in out.stdout.strip().split("."))
        return (major, minor)
    except ValueError:
        return None


def find_supported_interpreter() -> list[str] | None:
    """Find a command that launches a supported interpreter, preferring the current one."""
    if version_supported(sys.version_info[:2]):
        return [sys.executable]

    print(
        f"  This interpreter is Python {sys.version_info.major}.{sys.version_info.minor}, "
        f"outside the supported range {MIN_VERSION[0]}.{MIN_VERSION[1]}–"
        f"{MAX_VERSION[0]}.{MAX_VERSION[1]}. Searching for a supported one…"
    )

    candidates: list[list[str]] = []
    if os.name == "nt":
        # The Windows launcher selects an exact version regardless of PATH order.
        for minor in ("3.12", "3.13", "3.11"):
            candidates.append(["py", "-" + minor])
    for name in ("python3.12", "python3.13", "python3.11", "python3", "python"):
        candidates.append([name])

    seen: set[tuple[str, ...]] = set()
    for cmd in candidates:
        key = tuple(cmd)
        if key in seen:
            continue
        seen.add(key)
        version = _probe(cmd)
        if version and version_supported(version):
            print(f"  Found Python {version[0]}.{version[1]} via `{' '.join(cmd)}`.")
            return cmd
    return None


def fail_no_interpreter() -> int:
    print()
    print("ERROR: no supported Python found (need 3.11, 3.12 or 3.13; 3.12 recommended).")
    print()
    print("The pinned scientific stack (CatBoost, NumPy, SciPy, scikit-learn) has no wheels")
    print("for Python 3.14 yet, so the suite cannot be built there. Install a supported")
    print("interpreter and re-run this script:")
    print()
    if os.name == "nt":
        print(f"  winget install Python.Python.{RECOMMENDED.replace('.', '')}   # or from python.org")
        print("  Then:  py -3.12 scripts\\bootstrap.py")
    else:
        print(f"  # macOS:  brew install python@{RECOMMENDED}")
        print(f"  # Ubuntu: sudo apt install python{RECOMMENDED} python{RECOMMENDED}-venv")
        print(f"  Then:  python{RECOMMENDED} scripts/bootstrap.py")
    print()
    return 1


def main() -> int:
    print("=" * 70)
    print(" Unified Recovery Engine — environment bootstrap")
    print("=" * 70)

    if not REQUIREMENTS.exists():
        print(f"ERROR: {REQUIREMENTS} not found. Run this from the repo root.")
        return 1

    target = venv_python(VENV)

    if VENV.exists() and target.exists():
        version = _probe([str(target)])
        if version and version_supported(version):
            print(f"[1/2] Reusing existing .venv (Python {version[0]}.{version[1]}).")
        else:
            found = version[0:2] if version else "unknown"
            print(f"[1/2] Existing .venv runs Python {found}, which is unsupported.")
            print("      Delete it and re-run bootstrap:")
            print("        (Windows)  Remove-Item -Recurse -Force .venv")
            print("        (POSIX)    rm -rf .venv")
            return 1
    else:
        interpreter = find_supported_interpreter()
        if interpreter is None:
            return fail_no_interpreter()
        print(f"[1/2] Creating .venv with `{' '.join(interpreter)}`…")
        result = subprocess.run(interpreter + ["-m", "venv", str(VENV)])
        if result.returncode != 0 or not target.exists():
            print("ERROR: failed to create the virtual environment.")
            return 1

    print("[2/2] Installing pinned requirements into .venv (this can take a few minutes)…")
    pip_up = subprocess.run(
        [str(target), "-m", "pip", "install", "--upgrade", "pip", "--quiet"]
    )
    if pip_up.returncode != 0:
        print("  WARNING: could not upgrade pip; continuing with the bundled version.")
    install = subprocess.run(
        [str(target), "-m", "pip", "install", "-r", str(REQUIREMENTS)]
    )
    if install.returncode != 0:
        print()
        print("ERROR: dependency installation failed. See the pip output above.")
        return 1

    rel = target.relative_to(ROOT)
    print()
    print("=" * 70)
    print(" Ready. The environment is in .venv — every command below uses it.")
    print("=" * 70)
    print("  make test     # or:  " + str(rel) + " -m pytest")
    print("  make eval     # or:  " + str(rel) + " scripts/run_evaluation.py --events 200 --seeds 21-40")
    print("  make demo     # or:  " + str(rel) + " -m streamlit run app/ui/dashboard.py")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
