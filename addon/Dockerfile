ARG BUILD_FROM
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


# Install requirements for add-on
# RUN \
#   apk add --no-cache \
#     example_alpine_package

COPY . /app
RUN chmod +x /app/run.sh

# Parsing the add-on config
# ENV CONFIG_PATH=/data/options.json

# CMD ["tail", "-f", "/dev/null"]
CMD [ "/app/run.sh" ]