PYTHON := .venv/bin/python

.PHONY: setup acquire all test lint qc clean

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip==25.2
	$(PYTHON) -m pip install -r environment/requirements.lock
	$(PYTHON) -m pip install -e .

acquire:
	$(PYTHON) -m acdc_boundary.acquire

all:
	$(PYTHON) -m acdc_boundary.pipeline

test:
	$(PYTHON) -m pytest tests -q

lint:
	$(PYTHON) -m ruff check src tests

qc:
	$(PYTHON) -m acdc_boundary.qc

clean:
	rm -rf data_interim/* data_processed/* results/* figures/* tables/*
	rm -rf manuscript/build submission/build qc/generated
