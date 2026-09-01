.PHONY: help setup verify test test-leakage eval clean

help:
	@echo "=================================================================="
	@echo " UNIFIED RECOVERY ENGINE — STANDARDIZED BUILD & QUALITY TARGETS  "
	@echo "=================================================================="
	@echo "  make setup        - Install pinned dependencies (pip install -r requirements.txt)"
	@echo "  make verify       - Run complete environment quality gate script"
	@echo "  make test         - Run complete pytest suite"
	@echo "  make test-leakage - Run point-in-time leakage tests"
	@echo "  make eval         - Run experiment evaluation suite"
	@echo "  make clean        - Remove temporary cache, model logs, and test artifacts"
	@echo ""
	@echo "  Note for Windows PowerShell users without GNU make:"
	@echo "    python scripts/verify_environment.py"
	@echo "    pytest -v"
	@echo "    Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse"

setup:
	pip install -r requirements.txt

verify:
	python scripts/verify_environment.py

test:
	pytest

test-leakage:
	pytest -m leakage

clean:
	python -c "import shutil, glob, os; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True) + ['.pytest_cache', '.coverage', 'htmlcov', 'catboost_info']]"
