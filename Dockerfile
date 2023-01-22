FROM python:3.10-alpine

WORKDIR /app/ecco
RUN apk add gcc clang lld musl-dev compiler-rt
RUN pip install poetry
ADD . /app/ecco

RUN poetry install

ENTRYPOINT ["poetry", "run", "ecco"]
