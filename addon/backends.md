# Comparison of different LLM backends

## llama.cpp
- Best option currently
- Only supports GGUF models

## Ollama
- Doesn't support `tool_choice="required"`. See https://github.com/ollama/ollama/blob/main/docs/openai.md

## vLLM
- Doesn't support `tool_choice="required"`, which is required by `smolagents`

## TGI
- Not clear if it can be run on CPU easily