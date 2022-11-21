FROM python:3.10-alpine

WORKDIR /app/ecco
RUN pip install poetry
ADD . /app/ecco

RUN poetry install

ENTRYPOINT ["poetry", "run", "ecco"]
