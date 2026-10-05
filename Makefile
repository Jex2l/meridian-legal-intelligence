.PHONY: up down venv test

up:
	docker compose up -d

down:
	docker compose down

venv:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -q -r requirements.txt

test:
	cd backend && . .venv/bin/activate && python -m pytest -q
