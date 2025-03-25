import pytest
from fastapi.testclient import TestClient
from agents import Agent
from app import app, get_agent
import json
from tests.fake_model import FakeModel
from tests.test_responses import (
    get_text_message,
    get_function_tool,
    get_function_tool_call,
)

client = TestClient(app)

@pytest.mark.anyio
async def test_conversation():
    tools = [
        get_function_tool(
            name="get_temperature",
            return_value="22°C"
        )
    ]

    model = FakeModel()

    agent = Agent(
        name="Test Agent",
        model=model,
        instructions="You are a helpful assistant.",
        tools=tools
    )
    
    app.dependency_overrides[get_agent] = lambda: agent
    
    try:
        model.add_multiple_turn_outputs([
            [get_function_tool_call("get_temperature", json.dumps({"room": "living room"}))],
            [get_text_message("The temperature in the living room is 22°C.")]
        ])

        response = client.post("/api/conversation", json={
            "text": "What's the temperature in the living room?",
            "conversation_id": "test-conversation-1",
            "language": "en"
        })
        assert response.status_code == 200
        assert "22°C" in response.json()["response"]    

    finally:
        app.dependency_overrides.clear()