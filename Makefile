.DEFAULT_GOAL := help
VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

$(VENV)/bin/activate:
	python3 -m venv $(VENV) || (pip3 install --user virtualenv && python3 -m virtualenv $(VENV))
	$(PIP) install --upgrade pip

.PHONY: install
install: $(VENV)/bin/activate ## Install backend (dev) dependencies into .venv
	$(PIP) install -r requirements-dev.txt

.PHONY: install-frontend
install-frontend: ## Install frontend dependencies
	cd frontend && npm install

.PHONY: lint
lint: ## Lint backend with ruff
	$(VENV)/bin/ruff check backend scripts tests

.PHONY: format
format: ## Format backend with black + ruff --fix
	$(VENV)/bin/black backend scripts tests
	$(VENV)/bin/ruff check --fix backend scripts tests

.PHONY: test
test: ## Run backend test suite
	$(VENV)/bin/pytest

.PHONY: seed
seed: ## Generate synthetic data and run the pipeline once
	$(PY) scripts/seed.py

.PHONY: demo
demo: ## Inject the golden dengue outbreak scenario and run the full pipeline end-to-end
	$(PY) scripts/demo_scenario.py

.PHONY: api
api: ## Run the FastAPI backend (http://localhost:8000)
	$(VENV)/bin/uvicorn pathogenradar.api.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload

.PHONY: dev-frontend
dev-frontend: ## Run the Vite dev server (http://localhost:5173)
	cd frontend && npm run dev

.PHONY: up
up: ## Run backend + frontend together (docker-compose)
	docker compose up --build

.PHONY: clean
clean: ## Remove generated data and caches
	rm -rf data/seed/* data/cache/* .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
