#!/usr/bin/with-contenv bashio

bashio::log.info "Starting Home Agent addon..."

bashio::log.info "Loading configuration..."
MAX_TURNS=$(bashio::config 'max_turns')
export HOME_AGENT_MAX_TURNS="${MAX_TURNS}"

bashio::log.info "Starting Uvicorn server."

exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000