FROM python:3.13-alpine3.21 AS dependencies
ARG PACKAGE="auth"

ENV PACKAGE=$PACKAGE
ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

# UV copies the package files from the cache into the virtual environment. 
# This uses more disk space but ensures full independence of the virtual environment from the cache.
ENV UV_LINK_MODE=copy

WORKDIR /app
COPY ./pyproject.toml ./uv.lock ./.python-version ./

WORKDIR /app/services
COPY ./services/ ./

WORKDIR /app

# --frozen - lock file will not be updated
# -- type=bind: This creates a bind mount, 
# which directly links a path on the host filesystem to a path inside the container. 
# Bind mounts are useful for sharing configuration files, source code, or other data 
# that needs to be directly accessible from the host.

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=./uv.lock,target=uv.lock \
    --mount=type=bind,source=./pyproject.toml,target=pyproject.toml \
    uv sync --frozen --package=$PACKAGE

FROM dependencies AS base

ARG SERVICE_COMMAND

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package=$PACKAGE

ENV RUN_CMD=services.$PACKAGE.src
# CMD [ "uv", "run", "-m", "services.${PACKAGE}.src" ]
CMD uv run -m $RUN_CMD
# CMD $RUN_CMD




