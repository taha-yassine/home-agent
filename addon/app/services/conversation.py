import logging
from typing import Any, Dict, List
import httpx
from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent
from sqlalchemy import Engine, desc, func, select, asc
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
    RunConfig,
    set_trace_processors,
)
from agents.tracing.processors import BatchTraceProcessor
from agents.extensions.memory.sqlalchemy_session import SQLAlchemySession
from sqlalchemy.ext.asyncio import AsyncEngine

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
from ..settings import get_settings

_LOGGER = logging.getLogger('uvicorn.error')

def construct_prompt(home_entities: str) -> str:
    """Construct prompt for the agent."""
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

        # For each group_id, pick earliest generation span in the group for instruction
        # and earliest time as started_at. Then sort groups by latest generation span desc.

        # Rank generation spans per trace
        ranked_spans_subq = (
            select(
                Span,
                func.row_number()
                .over(
                    partition_by=Span.trace_id,
                    order_by=asc(Span.started_at),
                )
                .label("row_num_asc"),
                func.row_number()
                .over(
                    partition_by=Span.trace_id,
                    order_by=desc(Span.started_at),
                )
                .label("row_num_desc"),
            )
            .where(Span.span_type == "generation")
            .subquery("ranked_spans")
        )

        gen_span_asc = aliased(Span, ranked_spans_subq)
        gen_span_desc = aliased(Span, ranked_spans_subq)

        # Earliest generation span per trace
        earliest_gen_per_trace = (
            select(gen_span_asc.trace_id, gen_span_asc.started_at, gen_span_asc.span_data)
            .where(ranked_spans_subq.c.row_num_asc == 1)
            .subquery()
        )

        # Latest generation span time per trace
        latest_time_per_trace = (
            select(gen_span_desc.trace_id, gen_span_desc.started_at.label("latest_time"))
            .where(ranked_spans_subq.c.row_num_desc == 1)
            .subquery()
        )

        # Join traces to their group_id and aggregate by group
        group_agg = (
            select(
                Trace.group_id.label("group_id"),
                func.min(earliest_gen_per_trace.c.started_at).label("group_started_at"),
                func.max(latest_time_per_trace.c.latest_time).label("group_latest_time"),
                func.min(earliest_gen_per_trace.c.span_data).label("example_span_data"),
            )
            .join(earliest_gen_per_trace, earliest_gen_per_trace.c.trace_id == Trace.id)
            .join(latest_time_per_trace, latest_time_per_trace.c.trace_id == Trace.id)
            .group_by(Trace.group_id)
            .order_by(desc(func.max(latest_time_per_trace.c.latest_time)))
        )

        rows = (await db.execute(group_agg)).all()
        conversations: list[Conversation] = []
        for row in rows:
            group_id = row.group_id
            if not group_id:
                continue
            started_at = row.group_started_at.replace(tzinfo=timezone.utc)
            instruction = None
            try:
                # Pull instruction from the saved generation span format
                example_input = row.example_span_data["input"]
                if isinstance(example_input, list) and len(example_input) > 1:
                    instruction = example_input[1]["content"]
            except Exception:
                instruction = None

            conversations.append(
                Conversation(
                    group_id=group_id,
                    started_at=started_at,
                    instruction=instruction or "",
                )
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
        session_engine: AsyncEngine,
    ):
        """Process a conversation with the agent."""
        set_trace_processors([BatchTraceProcessor(exporter=HASpanExporter(db_engine))])

        active_connection: Connection | None = await ConnectionService.get_active_connection(db, mask_key=False)

        if not active_connection:
            yield "No active connection found. Please configure a connection."
            return
        
        def instructions(ctx_wrapper: RunContextWrapper[Any], agent: Agent | None) -> str:
            return construct_prompt(home_entities=ctx_wrapper.context["home_entities"])

        # We're constrained to creating a new httpx client for each connection because the base_url can't be changed at runtime
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
                instructions=instructions,
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
                settings = get_settings()
                session = SQLAlchemySession(
                    conversation_request.conversation_id,
                    engine=session_engine,
                    create_tables=True,
                )
                result = Runner.run_streamed(
                    starting_agent=agent,
                    input=input,
                    context=context,
                    max_turns=settings.max_turns,
                    session=session,
                    run_config=RunConfig(group_id=conversation_request.conversation_id),
                )
                async for event in result.stream_events():
                    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                        yield event.data.delta

                yield ""
            except Exception as e:
                _LOGGER.error(f"Error streaming conversation: {e}")
                yield f"I apologize, but I encountered an error: {str(e)}"