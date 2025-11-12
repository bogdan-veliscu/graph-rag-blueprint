.PHONY: help install ingest query query-file test lint format demo clean validate-graph falkordb-start falkordb-stop falkordb-status falkordb-restart falkordb-logs

help: ## Show this help message
	@echo "GraphRAG Legal System - Makefile Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install dependencies (using pip)
	@echo "Installing dependencies..."
	@pip3 install redis falkordb sentence-transformers rank-bm25 pydantic numpy scikit-learn faiss-cpu tiktoken httpx python-dotenv tqdm rich || echo "Warning: Some dependencies failed to install"
	@pip3 install -e . --no-deps || echo "Warning: Editable install failed, but core dependencies are installed"
	@python3 -m spacy download en_core_web_sm 2>/dev/null || echo "spaCy model download skipped (optional - system works without spaCy)"
	@echo "Installation complete!"

install-uv: ## Install dependencies using uv (recommended)
	@echo "Installing dependencies with uv..."
	@uv sync || echo "Warning: uv sync failed, falling back to pip"
	@python3 -m spacy download en_core_web_sm 2>/dev/null || echo "spaCy model download skipped (optional - system works without spaCy)"
	@echo "Installation complete!"

ingest: ## Ingest documents from data/source_data/
	@if [ -f .env ]; then set -a; . .env; set +a; fi; \
	python3 main.py ingest data/source_data/

ingest-fast: ## Ingest a single file for fast testing (default: data/fast_data/2024-12-12_en.md)
	@if [ -f .env ]; then set -a; . .env; set +a; fi; \
	python3 main.py ingest data/fast_data/

query: ## Query with a single question (usage: make query Q="your question")
	@if [ -z "$(Q)" ]; then \
		echo "Usage: make query Q='your question here'"; \
		exit 1; \
	fi
	@if [ -f .env ]; then set -a; . .env; set +a; fi; \
	python3 main.py query "$(Q)"

query-file: ## Query from a JSON file (usage: make query-file FILE=data/sample_questions.json)
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make query-file FILE=data/sample_questions.json"; \
		exit 1; \
	fi
	@if [ -f .env ]; then set -a; . .env; set +a; fi; \
	python3 main.py query --file $(FILE) --output answers.json

test: ## Run all tests
	python3 -m pytest tests/ -v

evaluate: ## Evaluate answers (usage: make evaluate QUESTIONS=data/questions.json ANSWERS=answers.json)
	@if [ -z "$(QUESTIONS)" ] || [ -z "$(ANSWERS)" ]; then \
		echo "Usage: make evaluate QUESTIONS=data/questions.json ANSWERS=answers.json"; \
		exit 1; \
	fi
	@if [ -f .env ]; then set -a; . .env; set +a; fi; \
	python3 scripts/evaluate.py --questions $(QUESTIONS) --answers $(ANSWERS) --output evaluation_results.json

lint: ## Run linting checks
	@echo "Running ruff..."
	ruff check src/ tests/ || true
	@echo "Running mypy..."
	mypy src/ || true

format: ## Format code with black and ruff
	black src/ tests/ main.py scripts/
	ruff check --fix src/ tests/ main.py scripts/

demo: ## Run complete demo (ingest + process ~400 questions)
	@if [ -f .env ]; then set -a; . .env; set +a; fi; \
	python3 scripts/run_demo.py

demo-skip-ingest: ## Run demo skipping ingestion (for testing queries only)
	@if [ -f .env ]; then set -a; . .env; set +a; fi; \
	python3 scripts/run_demo.py --skip-ingest

validate-graph: ## Validate graph structure after ingestion
	@if [ -f .env ]; then set -a; . .env; set +a; fi; \
	python3 scripts/validate_graph.py

clean: ## Clean generated files
	rm -rf output/
	rm -f answers.json
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

setup: install ## Install dependencies and download spaCy model
	@echo "Setup complete!"

falkordb-start: ## Start FalkorDB container
	@echo "Starting FalkorDB..."
	@if docker ps -a --format '{{.Names}}' | grep -q '^falkordb$$'; then \
		if docker ps --format '{{.Names}}' | grep -q '^falkordb$$'; then \
			echo "FalkorDB is already running"; \
		else \
			echo "Starting existing FalkorDB container..."; \
			docker start falkordb; \
		fi \
	else \
		echo "Creating new FalkorDB container..."; \
		docker run -d --name falkordb -p 6379:6379 falkordb/falkordb:latest; \
	fi
	@echo "FalkorDB started on port 6379"
	@sleep 2
	@docker ps --filter "name=falkordb" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

falkordb-stop: ## Stop FalkorDB container
	@echo "Stopping FalkorDB..."
	@docker stop falkordb 2>/dev/null || echo "FalkorDB container not running"
	@echo "FalkorDB stopped"

falkordb-status: ## Check FalkorDB status
	@echo "FalkorDB Status:"
	@if docker ps --format '{{.Names}}' | grep -q '^falkordb$$'; then \
		echo "✅ FalkorDB is running"; \
		docker ps --filter "name=falkordb" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"; \
	else \
		if docker ps -a --format '{{.Names}}' | grep -q '^falkordb$$'; then \
			echo "⚠️  FalkorDB container exists but is not running"; \
			docker ps -a --filter "name=falkordb" --format "table {{.Names}}\t{{.Status}}"; \
		else \
			echo "❌ FalkorDB container does not exist"; \
			echo "Run 'make falkordb-start' to create and start it"; \
		fi \
	fi

falkordb-restart: falkordb-stop falkordb-start ## Restart FalkorDB container

falkordb-logs: ## Show FalkorDB logs
	@docker logs falkordb 2>/dev/null || echo "FalkorDB container not found. Run 'make falkordb-start' first."

