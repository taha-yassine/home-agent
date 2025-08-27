ARG BUILD_FROM

FROM node:20-bullseye-slim AS frontend

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM $BUILD_FROM

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV APP_ENV=prod

WORKDIR /app

# --mount can't be used because Home Assistant doesn't support buildkit
# RUN --mount=type=bind,source=.python-version,target=.python-version \
#     uv python install
COPY .python-version .
RUN uv python install

# Install dependencies
# RUN --mount=type=cache,target=/root/.cache/uv \
#     --mount=type=bind,source=uv.lock,target=uv.lock \
#     --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
#     uv sync --locked --no-install-project --no-build
COPY uv.lock pyproject.toml ./
RUN uv sync --locked --no-install-project --no-build

COPY . /app
COPY --from=frontend /frontend/build /app/frontend/build
RUN chmod +x /app/run.sh

# Parsing the add-on config
# ENV CONFIG_PATH=/data/options.json

CMD [ "/app/run.sh" ]