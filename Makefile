.PHONY: help install setup run dashboard scheduler collect export test clean

PYTHON := python
PIP := pip
APP := main.py

help:
	@echo "Cannabis Data Aggregator - Available Commands"
	@echo "=============================================="
	@echo "  make install      Install Python dependencies"
	@echo "  make setup        Initialize database and seed sources"
	@echo "  make run          Run dashboard + scheduler (default)"
	@echo "  make dashboard    Run dashboard only"
	@echo "  make scheduler    Run scheduler only"
	@echo "  make collect      Run all enabled collectors once"
	@echo "  make collect SOURCE=co_med_licensees  Run specific source"
	@echo "  make export       Export all data to CSV/JSON"
	@echo "  make test         Run test suite"
	@echo "  make clean        Clean logs, temp files"
	@echo "  make docker-up    Start with Docker Compose"
	@echo "  make docker-down  Stop Docker Compose"

install:
	$(PIP) install -r requirements.txt

setup:
	$(PYTHON) scripts/setup_db.py
	$(PYTHON) scripts/seed_sources.py

run:
	$(PYTHON) $(APP) --mode all

dashboard:
	$(PYTHON) $(APP) --mode dashboard

scheduler:
	$(PYTHON) $(APP) --mode scheduler

collect:
ifdef SOURCE
	$(PYTHON) scripts/run_collector.py --source $(SOURCE)
else
	$(PYTHON) scripts/run_collector.py --all
endif

export:
	$(PYTHON) scripts/export_data.py

export-state:
ifdef STATE
	$(PYTHON) scripts/export_data.py --state $(STATE)
else
	@echo "Usage: make export-state STATE=CO"
endif

export-category:
ifdef CATEGORY
	$(PYTHON) scripts/export_data.py --category $(CATEGORY)
else
	@echo "Usage: make export-category CATEGORY=dispensaries"
endif

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	flake8 src/ scripts/ --max-line-length=120
	black --check src/ scripts/

format:
	black src/ scripts/
	isort src/ scripts/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -delete
	rm -rf .pytest_cache .coverage htmlcov/
	@echo "Cleaned up build artifacts"

clean-logs:
	rm -rf logs/*.log
	@echo "Cleared log files"

docker-up:
	docker-compose up -d

docker-up-postgres:
	docker-compose --profile postgres up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app

shell:
	$(PYTHON) -c "from src.storage.database import init_db; init_db(); import IPython; IPython.embed()"
