#!/usr/bin/with-contenv bashio

bashio::log.info "Starting Home Agent addon..."

bashio::log.info "Starting Uvicorn server."

exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000