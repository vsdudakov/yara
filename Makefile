PACKAGE = yara


.PHONY: help  # Shows this message
help:
	@grep '^.PHONY: .* #' Makefile | sed 's/\.PHONY: \(.*\) # \(.*\)/\1	\2/' | expand -t20


.PHONY: clean  # Clean cache and build files
clean:
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf .coverage


.PHONY: check  # Runs linters
check:
	@echo "Run ruff"
	@exec poetry run ruff $(PACKAGE)
	@echo "Run isort"
	@exec poetry run isort --check-only $(PACKAGE)
	@echo "Run black"
	@exec poetry run black --check --diff $(PACKAGE)
	@echo "Run mypy"
	@exec poetry run mypy -p $(PACKAGE)


.PHONY: lint  # Runs linters and fixes auto-fixable errors
lint:
	@echo "Run ruff"
	@exec poetry run ruff --fix $(PACKAGE)
	@echo "Run isort"
	@exec poetry run isort $(PACKAGE)
	@echo "Run black"
	@exec poetry run black $(PACKAGE)
	@echo "Run mypy"
	@exec poetry run mypy -p $(PACKAGE)


.PHONY: test  # Runs tests
test:
	@echo "Run tests"
	poetry run pytest -vvv -rsxXA --log-level=DEBUG -n auto --cov $(PACKAGE) --cov-report term-missing $(args)


.PHONY: install  # Install
install:
	@echo "Upgrade pip"
	@exec pip install -U pip
	@echo "Install poetry"
	@exec pip install -U poetry
	@echo "Install packages"
	@exec poetry install --no-root


.PHONY: db-migrate  # Run db migrations
migrate:
	@echo "Run db migrations"
	@exec poetry run python manage.py migrate


.PHONY: dev  # Start dev server
dev:
	@echo "Start dev server"
	@exec poetry run python manage.py migrate
	@exec poetry run uvicorn $(PACKAGE).main:root_asgi_app --reload --host 0.0.0.0 --port 8000


.PHONY: start  # Start prod server
start:
	@echo "Start prod server"
	@exec poetry run uvicorn $(PACKAGE).main:root_asgi_app --host 0.0.0.0 --port 8000


.PHONY: worker-dev  # Start dev worker
worker-dev:
	@echo "Start dev worker"
	@exec poetry run watchmedo auto-restart --directory=./$(PACKAGE) --pattern=*.py --recursive -- celery -- -A $(PACKAGE).main:celery_asgi_app worker -l DEBUG -B --schedule-filename /tmp/celerybeat-schedule


.PHONY: worker  # Start prod worker
worker:
	@echo "Start prod worker"
	@exec poetry run celery -A $(PACKAGE).main:celery_asgi_app worker -l INFO -B  --schedule-filename /tmp/celerybeat-schedule


.PHONY: worker-purge  # Purge worker data
worker-purge:
	@echo "Purge worker data"
	@exec poetry run celery --app $(PACKAGE).main:celery_asgi_app purge
