.PHONY: help setup verify test test-leakage eval eval-quick demo clean

# The interpreter used ONLY to bootstrap the venv. Override if `python` on your PATH is
# outside the supported range (3.11-3.13):
#   make setup PYTHON=python3.12        # macOS / Linux
#   make setup PYTHON="py -3.12"        # Windows
PYTHON ?= python

# Every real target runs through the venv interpreter, never a bare `python` / `pytest`.
# This is what stops a cold clone from silently using an unsupported system Python.
ifeq ($(OS),Windows_NT)
VENV_PY := .venv/Scripts/python.exe
else
VENV_PY := .venv/bin/python
endif

help:
	@echo "=================================================================="
	@echo " UNIFIED RECOVERY ENGINE - BUILD & QUALITY TARGETS                "
	@echo "=================================================================="
	@echo "  make setup        - Create .venv with a supported Python and install deps"
	@echo "  make verify       - Environment quality gate (versions, imports, secrets)"
	@echo "  make test         - Run the full pytest suite in .venv"
	@echo "  make test-leakage - Run point-in-time leakage tests"
	@echo "  make eval         - Full evaluation -> results/report.json + RESULTS.md"
	@echo "  make eval-quick   - Fast evaluation (60 events, 5 seeds)"
	@echo "  make demo         - Launch the judge dashboard (Streamlit) on :8555"
	@echo "  make clean        - Remove caches and test artifacts"
	@echo ""
	@echo "  First run: make setup   (needs Python 3.11-3.13 available; 3.12 recommended)"
	@echo "  No GNU make? Run scripts/bootstrap.py, then the .venv commands it prints."

setup:
	$(PYTHON) scripts/bootstrap.py

verify:
	$(VENV_PY) scripts/verify_environment.py

test:
	$(VENV_PY) -m pytest

test-leakage:
	$(VENV_PY) -m pytest -m leakage

eval:
	$(VENV_PY) scripts/run_evaluation.py --events 200 --seeds 21-40

eval-quick:
	$(VENV_PY) scripts/run_evaluation.py --events 60 --seeds 21-25

demo:
	$(VENV_PY) -m streamlit run app/ui/dashboard.py --server.port 8555

clean:
	$(VENV_PY) -c "import shutil, glob; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True) + ['.pytest_cache', '.coverage', 'htmlcov', 'catboost_info']]"
