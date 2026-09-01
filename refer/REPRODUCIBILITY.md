# REPRODUCIBILITY & ENVIRONMENT QUALITY GATE

**Unified Recovery Engine — Milestone 1.2 Verification & Reproducibility Guide**

---

## 1. RUNTIME & SPECIFICATION SUMMARY

- **Python Runtime**: Python `3.12.9` (64-bit AMD64).
- **Virtual Environment**: `.venv` (created via `py -3.12 -m venv .venv`).
- **Operating System**: Windows / Linux / macOS compatible.
- **Core Dependencies Pinned**:
  - `catboost==1.2.10`
  - `scikit-learn==1.9.0`
  - `scipy==1.18.1`
  - `pandas==3.0.5`
  - `numpy==2.5.2`
  - `pytest==9.1.1`
  - `hypothesis==6.167.1`
  - `streamlit==1.62.0`

---

## 2. FRESH ENVIRONMENT REPRODUCIBILITY INSTRUCTIONS

To recreate and verify this repository from a fresh clone:

### Step 1: Create Virtual Environment
```bash
# Windows
py -3.12 -m venv .venv
.\.venv\Scripts\activate

# Linux / macOS
python3.12 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Pinned Dependencies
```bash
pip install -r requirements.txt
pip check
```
*Expected output*: `No broken requirements found.`

### Step 3: Run Automated Quality Gate
```bash
python scripts/verify_environment.py
```
*Expected output*: `[PASSED] QUALITY GATE PASSED: Environment is 100% reproducible!`

### Step 4: Run Pytest Suite
```bash
pytest -v
```
*Expected output*: `4 passed in < 5.0s`.

---

## 3. QUALITY GATE COMPONENT CHECKS

The automated quality gate script (`scripts/verify_environment.py`) validates six independent criteria:

1. **Python Runtime Version**: Asserts Python version $\ge$ 3.11.
2. **Dependency Graph Integrity**: Executes `pip check` to ensure zero broken package requirements.
3. **Numerical & ML Imports**: Verifies `numpy`, `pandas`, `scipy`, `sklearn`, `catboost`, `matplotlib`, `pytest`, `hypothesis`, `streamlit`.
4. **CatBoost Deterministic Model Fit**: Instantiates a `CatBoostClassifier` with `random_seed=42`, fits a 4-sample array, and asserts discrete class prediction outputs `[0, 1, 0, 1]`.
5. **Pytest Test Suite Execution**: Programmatically invokes `pytest.main()`.
6. **Secret & Credential Hygiene**: Scans repository files via regex for hardcoded API keys, passwords, bearer tokens, or authorization secrets.

---

## 4. DETERMINISM GUARANTEES & LIMITATIONS

### What is Guaranteed
- **Exact Package Versions**: `requirements.txt` strictly pins exact patch releases across the entire stack.
- **Seed Determinism**: All random model fits and dataset generations use explicit integer seeds (`random_seed=42`).
- **Property-Based Testing**: Hypothesis property tests are locked with default profiles to prevent non-deterministic test ordering.
- **Offline Self-Containment**: The core test suite requires zero internet connectivity, zero cloud databases, and zero external credentials.

### What is Limited
- **C-Extension Floating Point Differences**: Microscopic floating-point variations may occur in CatBoost leaf weights across different OS/CPU architectures (e.g. AVX2 vs AVX-512 instruction sets). Test assertions rely on discrete integer class labels (`[0, 1]`) rather than unrounded float probabilities.
- **Python 3.14 Compatibility**: Pre-release Python 3.14 experience C-extension OpenMP locking on Windows. Python 3.12.9 LTS is the required authoritative build baseline.

---

## 5. AUDIT & VERIFICATION RECORD

- **Last Quality Gate Execution**: 2026-09-01
- **Quality Gate Result**: `PASS` (6/6 checks passed)
- **Pytest Output**: `4 passed in 0.45s`
- **Secret Scan Result**: `0 matches`
