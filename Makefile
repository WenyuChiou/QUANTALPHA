.PHONY: help install index run-dashboard run-orchestrator clean

help:
	@echo "Alpha-Mining LLM Agent Framework"
	@echo ""
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make index            - Index knowledge base"
	@echo "  make run-dashboard    - Start Streamlit dashboard"
	@echo "  make run-orchestrator - Run orchestrator (single iteration)"
	@echo "  make clean            - Clean cache and temporary files"

install:
	pip install -r requirements.txt

index:
	python -m src.rag.indexer

run-dashboard:
	streamlit run src/dashboard/app.py

run-orchestrator:
	python -m src.agents.orchestrator --universe sp500 --n_candidates 3

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	rm -rf data/cache/*.parquet
	rm -rf .pytest_cache

