PY ?= python3
COMPOSE ?= docker compose

.PHONY: help install test lint fmt ci run dashboard up down logs seed login backup restore

help:            ## list targets
	@grep -E '^[a-z-]+:.*?##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/' | column -t -s $$'\t'

install:         ## dev deps + browsers
	pip install -r requirements.txt pytest ruff pre-commit
	python -m playwright install --with-deps chromium
	pre-commit install

lint:            ## ruff check
	ruff check .

fmt:             ## ruff format + autofix
	ruff check --fix . && ruff format .

test:            ## unit tests
	pytest -q

smoke:           ## import every module (fast breakage catch)
	$(PY) -c "import fbm_core, tracking, accounts, suppliers, reprice, groups, \
crosslist, crosslist_post, inbox_poller, inbox_ai, insights, returns, tax, \
dashboard, deadman, metrics, fbm_validate, targets_builder, copy_generator, samples, session_guard"

ci: lint smoke test   ## what CI runs

seed:            ## bootstrap the database
	$(PY) bootstrap.py

login:           ## one-time login + selector calibration
	$(PY) login_once.py --calibrate --orders

backup:          ## encrypted profile + db backup
	$(PY) profile_backup.py backup

restore:         ## restore latest backup
	$(PY) profile_backup.py restore

run:             ## full pipeline locally
	./run_all.sh

dashboard:       ## dashboard only
	$(PY) dashboard.py

up:              ## prod compose
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f worker
