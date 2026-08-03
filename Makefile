.PHONY: setup dev test lint eval migrate seed docker-build clean

setup:
	pip install -e .[dev]
	cd ../frontend && npm install

dev:
	docker-compose up --build

test:
	pytest tests/ -v

lint:
	ruff check app/ tests/ && mypy app/ --strict
	cd ../frontend && npm run lint

eval:
	python scripts/run_eval_cli.py

migrate:
	alembic upgrade head

seed:
	python scripts/seed_dataset.py

docker-build:
	docker build -t mrd-backend -f Dockerfile .
	docker build -t mrd-frontend -f ../frontend/Dockerfile ../frontend

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	rm -rf reports/*.html
