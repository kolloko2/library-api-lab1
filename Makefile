PYTHON ?= python
.PHONY: setup run test quality migrate backup restore verify up down container-check
setup:
	$(PYTHON) -m pip install -r requirements.txt
run:
	$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0
test:
	$(PYTHON) -m pytest --cov=app --cov-fail-under=40 --cov-report=xml:artifacts/coverage.xml --junitxml=artifacts/junit.xml
quality:
	$(PYTHON) -m ruff check app tests migrations scripts
	$(PYTHON) -m ruff format --check app tests migrations scripts
	$(PYTHON) -m bandit -r app scripts -ll
migrate:
	$(PYTHON) -m alembic upgrade head
backup:
	$(PYTHON) scripts/database.py backup $(FILE)
restore:
	$(PYTHON) scripts/database.py restore $(FILE)
verify: quality test
	$(PYTHON) -m compileall -q app migrations scripts
	$(PYTHON) -m pip_audit -r requirements.txt
	$(PYTHON) scripts/mutation_check.py
up:
	docker compose up -d --build --wait
down:
	docker compose down
container-check:
	$(PYTHON) scripts/container_check.py
