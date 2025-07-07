"""Test to confirm external communication with the HASS instance."""
import dataclasses
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator
from homeassistant.core import HomeAssistant
from fastapi import FastAPI
from typing import Any

from home_assistant_datasets.agent import ConversationAgent
from home_assistant_datasets.datasets.assist_eval_task import EvalTask
from home_assistant_datasets.entity_state.diff import EntityStateDiffFixture
from home_assistant_datasets.scrape import ModelOutput, ModelOutputWriter

from custom_component.const import DOMAIN

# TODO: Some assist tests need to override validation to function
# @pytest.mark.parametrize("validate_entities", [None])
@pytest.mark.parametrize("expected_lingering_timers", [True])
@pytest.mark.parametrize("expected_lingering_tasks", [True])
async def test_assist_actions(
    hass: HomeAssistant,
    agent: ConversationAgent,
    model_id: str,
    model_output_writer: ModelOutputWriter,
    eval_task: EvalTask,
    entity_state_diff: EntityStateDiffFixture,
    addon_app: FastAPI,
    hass_client: ClientSessionGenerator,
) -> None:
    """Collects model responses for assist actions."""

    # Start async test client for the addon using AsyncClient with ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=addon_app), base_url="http://test"
    ) as async_client:
        # Find and inject the configured httpx client into the integration
        home_agent_entries = hass.config_entries.async_entries(DOMAIN)
        if not home_agent_entries:
            pytest.fail("No config entries found for home_agent")
        entry = home_agent_entries[0]
        # Replace the client in hass.data with our AsyncClient
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            old_client = hass.data[DOMAIN][entry.entry_id]
            await old_client.aclose()
            hass.data[DOMAIN][entry.entry_id] = async_client

        # Now run the original test logic
        task: dict[str, Any] = {"input_text": eval_task.input_text}
        if eval_task.action.expect_changes:
            task["expect_changes"] = {
                k: dataclasses.asdict(v)
                for k, v in (eval_task.action.expect_changes or {}).items()
            }
            entity_state_diff.prepare(
                eval_task.action.expect_changes or {}, eval_task.action.ignore_changes or {}
            )
        if eval_task.action.expect_response:
            task["expect_response"] = eval_task.action.expect_response
        if eval_task.action.expect_tool_call:
            task["expect_tool_call"] = eval_task.action.expect_tool_call

        # Run the conversation agent
        response = await agent.async_process(hass, eval_task.input_text)

        # Record the model output state
        context = {}
        if eval_task.action.expect_changes:
            context["unexpected_states"] = entity_state_diff.get_unexpected_changes()
        context.update(agent.trace_context())
        output = ModelOutput(
            uuid=str(uuid.uuid4()),  # Unique based on the model evaluated
            model_id=model_id,
            task_id=eval_task.task_id,
            category=eval_task.category,
            task=task,
            response=response,
            context=context,
        )
        model_output_writer.write(output)