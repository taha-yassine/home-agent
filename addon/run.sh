#!/usr/bin/with-contenv bashio

bashio::log.info "Starting Home Agent addon..."

export HOME_AGENT_LLM_SERVER_URL=$(bashio::config 'llm_server_url')
export HOME_AGENT_LLM_SERVER_API_KEY=$(bashio::config 'llm_server_api_key')
export HOME_AGENT_LLM_SERVER_PROXY=$(bashio::config 'llm_server_proxy')

bashio::log.info "Starting Uvicorn server."

exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000