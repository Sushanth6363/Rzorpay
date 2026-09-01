.PHONY: help setup test test-leakage eval clean

help:
	@echo "Available commands:"
	@echo "  make setup        - Install dependencies"
	@echo "  make test         - Run test suite"
	@echo "  make test-leakage - Run point-in-time leakage tests"
	@echo "  make eval         - Run experiment evaluation suite"
	@echo "  make clean        - Remove temporary cache and test artifacts"

setup:
	pip install -r requirements.txt

test:
	pytest

test-leakage:
	pytest -m leakage

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov
