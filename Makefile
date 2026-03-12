.PHONY: install run docker-build docker-run

install:
	pip install -r requirements.txt

run:
	python app.py

docker-build:
	docker build -t codex-payrails .

docker-run:
	docker run --env-file .env -p 5000:5000 codex-payrails
