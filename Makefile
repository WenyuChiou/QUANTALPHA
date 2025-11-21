.PHONY: help install index run-dashboard run-orchestrator clean

help:
	@echo "Alpha-Mining LLM Agent Framework"
	@echo ""
	@echo "Available commands:"
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

