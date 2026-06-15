.PHONY: api-install api-test api-lint api-run web-install web-build web-run test

api-install:
	cd apps/api && python3 -m pip install --user -e ".[dev]"

api-test:
	cd apps/api && python3 -m pytest

api-lint:
	cd apps/api && python3 -m ruff check src tests

api-run:
	cd apps/api && uvicorn pathogenradar_api.main:app --host 0.0.0.0 --port 8000 --reload

web-install:
	cd apps/web && npm install

web-build:
	cd apps/web && npm run build

web-run:
	cd apps/web && npm run dev -- --host 0.0.0.0

test: api-test api-lint web-build
