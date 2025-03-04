# This dockerfile should be built from the root of the project
# docker build -f tests/test-project/Dockerfile -t test-project .
FROM python:3.11-slim-bullseye
WORKDIR /app
COPY tests/test-project/pyproject.toml ./

ARG POETRY_VERSION

RUN pip install "poetry==$POETRY_VERSION"
# we make the lockfile inside the image, to make it compatible with whatever poetry version is installed
RUN poetry update
# we copy the plugin to the image so we can install it
COPY ./poetry_lock_listener /poetry-self-plugin/poetry_lock_listener
COPY ./pyproject.toml ./README.md /poetry-self-plugin/
RUN poetry self add /poetry-self-plugin
COPY tests/test-project/. .