PY ?= python3
COMPOSE ?= docker compose

.PHONY: help install test lint fmt ci run dashboard up down logs seed login backup restore

help:
	@grep -E '^[a-z-]+:.*?##' $(MAKEFILE_LIST) | sed 's/:.*##\t/' | column -t -s $$'\t'

install:
	pip install -r requirements.txt pytest ruff pre-commit
	python -m playwright install --with-deps chromium
	pre-commit install

lint:
	ruff check .

fmt:
	ruff check --fix . && ruff format .

test:
	pytest -q

smoke:
	$(PY) -c "import fbm_core, tracking, accounts, suppliers, reprice, groups, \
crosslist, crosslist_post, inbox_poller, inbox_ai, insights, returns, tax, \
dashboard, deadman, metrics, fbm_validate, targets_builder, copy_generator, samples, session_guard"

ci: lint smoke test

seed:
	$(PY) bootstrap.py

login:
	$(PY) login_once.py --calibrate --orders

backup:
	$(PY) profile_backup.py backup

restore:
	$(PY) profile_backup.py restore

run:
	./run_all.sh

dashboard:
	$(PY) dashboard.py

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f worker