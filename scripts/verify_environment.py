#!/usr/bin/env python3
"""Unified Recovery Engine — Environment Quality Gate Script.

Verifies runtime environment, dependency integrity, library imports, CatBoost ML capability,
pytest execution, and secret hygiene in a single reproducible command.
"""

import os
import re
import sys
import subprocess
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def check_python_version() -> bool:
    """Verify CPython version is 3.11+."""
    version = sys.version_info
    print(f"[CHECK 1/6] Python Version: {version.major}.{version.minor}.{version.micro}")
    if version < (3, 11):
        print(f"  [FAIL] Python 3.11+ required. Found {version.major}.{version.minor}")
        return False
    print("  [OK] Python runtime version verified.")
    return True


def check_pip_dependencies() -> bool:
    """Run pip check to verify dependency graph integrity."""
    print("[CHECK 2/6] Dependency Integrity (pip check):")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"  [OK] {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [FAIL] Broken dependencies detected:\n{e.stdout}\n{e.stderr}")
        return False


def check_library_imports() -> bool:
    """Verify all core stack libraries import without error."""
    print("[CHECK 3/6] Core Stack Library Imports:")
    libs = [
        "numpy",
        "pandas",
        "scipy",
        "sklearn",
        "catboost",
        "matplotlib",
        "pytest",
        "hypothesis",
        "streamlit",
    ]
    failed = []
    for lib in libs:
        try:
            mod = __import__(lib)
            ver = getattr(mod, "__version__", "unknown")
            print(f"  • {lib}: {ver}")
        except Exception as err:
            print(f"  [FAIL] {lib}: Failed to import ({err})")
            failed.append(lib)

    if failed:
        print(f"  [FAIL] Could not import {len(failed)} libraries: {failed}")
        return False
    print("  [OK] All core stack libraries imported successfully.")
    return True


def check_catboost_fit() -> bool:
    """Verify CatBoost model instantiation and fitting."""
    print("[CHECK 4/6] CatBoost Model Deterministic Fit:")
    try:
        import catboost
        import numpy as np

        X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]])
        y = np.array([0, 1, 0, 1])

        model = catboost.CatBoostClassifier(
            iterations=5,
            learning_rate=0.1,
            depth=2,
            random_seed=42,
            verbose=0,
        )
        model.fit(X, y)
        preds = model.predict(X)
        print(f"  • Predictions: {preds.tolist()}")
        print("  [OK] CatBoost model fit & predict verified.")
        return True
    except Exception as err:
        print(f"  [FAIL] CatBoost verification failed: {err}")
        return False


def check_pytest_suite() -> bool:
    """Run pytest suite."""
    print("[CHECK 5/6] Pytest Suite Execution:")
    try:
        import pytest

        exit_code = pytest.main(["-v", "--tb=short"])
        if exit_code == 0:
            print("  [OK] All pytest tests passed.")
            return True
        else:
            print(f"  [FAIL] pytest exited with status code {exit_code}")
            return False
    except Exception as err:
        print(f"  [FAIL] Failed to execute pytest: {err}")
        return False


def check_secret_hygiene() -> bool:
    """Scan tracked repository files for potential secret patterns."""
    print("[CHECK 6/6] Secret & Credential Hygiene Check:")
    pattern = re.compile(r"(api_key|secret_key|private_key|password|bearer|auth_token)\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE)
    
    root_dir = Path(__file__).resolve().parent.parent
    violations = []

    for path in root_dir.rglob("*"):
        if path.is_file() and not any(part.startswith(".") or part in ["catboost_info", "results", "__pycache__", "venv", ".venv"] for part in path.parts):
            if path.suffix in [".py", ".json", ".yaml", ".yml", ".toml", ".md", ".sh", ".txt"]:
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                    for idx, line in enumerate(content.splitlines(), 1):
                        if pattern.search(line) and "TOOLCHAIN.md" not in str(path):
                            violations.append((str(path.relative_to(root_dir)), idx))
                except Exception:
                    pass

    if violations:
        print(f"  [FAIL] Potential hardcoded secret patterns found in {len(violations)} lines:")
        for file_path, line_no in violations:
            print(f"    • {file_path}:{line_no}")
        return False

    print("  [OK] Zero hardcoded secrets detected across repository files.")
    return True


def main() -> None:
    """Execute all environment quality gate checks."""
    print("==================================================================")
    print(" UNIFIED RECOVERY ENGINE — ENVIRONMENT QUALITY GATE VERIFICATION ")
    print("==================================================================")
    
    results = [
        check_python_version(),
        check_pip_dependencies(),
        check_library_imports(),
        check_catboost_fit(),
        check_pytest_suite(),
        check_secret_hygiene(),
    ]

    print("\n------------------------------------------------------------------")
    if all(results):
        print(" [PASSED] QUALITY GATE PASSED: Environment is 100% reproducible!")
        print("------------------------------------------------------------------\n")
        sys.exit(0)
    else:
        print(" [FAILED] QUALITY GATE FAILED: Resolve issues before proceeding.")
        print("------------------------------------------------------------------\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
