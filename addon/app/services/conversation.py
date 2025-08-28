import logging
from typing import Any, Dict, List
import httpx
from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent
from sqlalchemy import Engine, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from datetime import timezone
from textwrap import dedent
import yaml

from agents import (
    Agent,
    Runner,
    OpenAIChatCompletionsModel,
    Tool,
    ModelSettings,
    RunContextWrapper,
    set_trace_processors,
)
from agents.tracing.processors import BatchTraceProcessor

from ..db import Span, Trace
from ..models import (
    Conversation,
    ConversationList,
    ConversationRequest,
    ConversationResponse,
    Connection,
)
from .connection import ConnectionService
from ..tracing import HASpanExporter

_LOGGER = logging.getLogger('uvicorn.error')

def construct_prompt(ctx_wrapper: RunContextWrapper[Any], agent: Agent | None) -> str:
    """Construct prompt for the agent."""
    home_entities = ctx_wrapper.context["home_entities"]

    prompt = dedent("""\
        You are a helpful assistant that helps with tasks around the home. You will be given instructions that you are asked to follow. You can use the tools provided to you to control devices in the home in order to complete the task. When you have completed the task, you should respond with a summary of the task and the result in first person (e.g. I turned on the lights).
        
        Following is a detailed list of entities and devices currently in the home. You can use the `get_state` tool to get the current state of an entity before taking action.
        """) + "\n" + home_entities
    
    return prompt

class ConversationService:
    """Service for handling agent conversations."""

    @staticmethod
    async def get_conversations(db: AsyncSession) -> ConversationList:
        """Get all conversations from the database."""
        # TODO: Implement proper sorting and pagination

        ranked_spans_subq = (
            select(
                Span,
                func.row_number()
                .over(
                    partition_by=Span.trace_id,
                    order_by=desc(Span.started_at),
                )
                .label("row_num"),
            )
            .where(Span.span_type == "generation")
            .subquery("ranked_spans")
        )

        latest_generation_span_alias = aliased(Span, ranked_spans_subq)

        stmt = (
            select(Trace, latest_generation_span_alias)
            .join(
                latest_generation_span_alias,
                Trace.id == latest_generation_span_alias.trace_id,
            )
            .where(ranked_spans_subq.c.row_num == 1)
            .order_by(desc(latest_generation_span_alias.started_at))
        )

        results = (await db.execute(stmt)).all()
        conversations = []
        for trace, latest_generation_span in results:
            try:
                instruction = latest_generation_span.span_data["input"][1]["content"]

                # sqlite3 strips timezone info from datetime objects so we need to add it back
                started_at = latest_generation_span.started_at.replace(
                    tzinfo=timezone.utc
                )

                conversations.append(
                    Conversation(
                        id=trace.id,
                        started_at=started_at,
                        instruction=instruction,
                    )
                )
            except (KeyError, IndexError):
                _LOGGER.warning(
                    f"Could not extract instruction for trace {trace.id}",
                    exc_info=True,
                )
        return ConversationList(conversations=conversations)

    @staticmethod
    async def fetch_home_entities(hass_client: httpx.AsyncClient) -> str:
        """Fetch the home entities from the Home Assistant API."""
        try:
            response = await hass_client.get("/home_agent/entities")
        except Exception as e:
            _LOGGER.error(f"Exception while fetching home entities: {e}", exc_info=True)
            raise RuntimeError("Failed to fetch home entities from Home Assistant API") from e

        if response.status_code != 200:
            message = f"Failed to fetch home entities: {response.status_code} {response.text}"
            _LOGGER.error(message)
            raise RuntimeError(message)

        try:
            data = response.json()
        except Exception as e:
            _LOGGER.error(f"Invalid JSON while fetching home entities: {e}", exc_info=True)
            raise RuntimeError("Received invalid JSON when fetching home entities") from e

        entities = data.get("entities") if isinstance(data, dict) else None

        if entities:
            return yaml.dump(list(entities.values()), sort_keys=False)
        
        _LOGGER.warning("No entities were found in the home.")
        return ""

    @staticmethod
    async def process_conversation(
        conversation_request: ConversationRequest,
        hass_client: httpx.AsyncClient,
        tools: List[Tool],
        db: AsyncSession,
        db_engine: Engine,
    ):
        """Process a conversation with the agent."""
        set_trace_processors([BatchTraceProcessor(exporter=HASpanExporter(db_engine))])

        active_connection: Connection | None = await ConnectionService.get_active_connection(db, mask_key=False)

        if not active_connection:
            yield "No active connection found. Please configure a connection."
            return

        # We're constrained to creating a new httpx client for each connection because the base_url can be changed at runtime
        async with AsyncOpenAI(
            base_url=active_connection.url,
            api_key=active_connection.api_key,
        ) as openai_client:
            agent = Agent(
                name="Home Agent",
                model=OpenAIChatCompletionsModel(
                    model=active_connection.model or "generic",
                    openai_client=openai_client,
                ),
                instructions=construct_prompt,
                tools=tools,
                model_settings=ModelSettings(
                    extra_body={
                        "chat_template_kwargs": {
                            "enable_thinking": False,
                        }
                    }
                ),
            )

            try:
                home_entities = await ConversationService.fetch_home_entities(hass_client)
            except Exception as e:
                _LOGGER.error(f"Unable to fetch home entities: {e}", exc_info=True)
                yield f"I apologize, but I could not fetch the home entities: {str(e)}"
                return

            context: Dict[str, Any] = {
                "conversation_id": conversation_request.conversation_id,
                "language": conversation_request.language,
                "home_entities": home_entities,
                "hass_client": hass_client,
            }

            input = conversation_request.text

            try:
                result = Runner.run_streamed(
                    starting_agent=agent,
                    input=input,
                    context=context,
                    max_turns=3,
                )
                async for event in result.stream_events():
                    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                        yield event.data.delta

                yield ""
            except Exception as e:
                _LOGGER.error(f"Error streaming conversation: {e}")
                yield f"I apologize, but I encountered an error: {str(e)}"