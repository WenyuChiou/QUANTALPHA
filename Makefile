.PHONY: help install index run-dashboard run-orchestrator clean

help:
	@echo "Alpha-Mining LLM Agent Framework"
	@echo ""
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make setup            - Setup environment (install, init DB, index KB)"
	@echo "  make index-kb         - Index knowledge base"
	@echo "  make test             - Run all tests"
	@echo "  make clean            - Clean temporary files"
	@echo "  make run-dashboard    - Start Streamlit dashboard"
	@echo "  make run-orchestrator - Run orchestrator (single iteration)"
	@echo "  make run-full-pipeline - Run complete pipeline (generate alpha + evaluate)"
	@echo "  make run-full-pipeline - Run complete pipeline (generate alpha + evaluate)"

install:
	pip install -r requirements.txt

index:
	python -m src.rag.indexer

run-dashboard:
	streamlit run src/dashboard/app.py

run-orchestrator:
	python -m src.agents.orchestrator --universe sp500 --n_candidates 3

run-full-pipeline:
	@echo "Running complete pipeline: generate alpha and evaluate..."
	python scripts/run_full_pipeline.py

clean:
	@echo "Cleaning temporary files..."
	python scripts/cleanup.py
	@echo "Cleanup complete!"

test:
	@echo "Running backend tests..."
	python scripts/test_backend.py
	@echo "Running unit tests..."
	python -m pytest tests/ -v

setup:
	@echo "Setting up environment..."
	python scripts/setup_env.py

index-kb:
	@echo "Indexing knowledge base..."
	python scripts/index_kb.py

