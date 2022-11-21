dbuild:
	docker build -t ecco .

drun:
	docker run ecco

dbuildrun: dbuild drun

run:
	poetry run ecco

install:
	pip install .
