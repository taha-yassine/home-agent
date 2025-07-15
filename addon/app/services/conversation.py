import logging
from typing import Any, Dict, List
import httpx
from openai import AsyncOpenAI
from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

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

from ..db.models import Trace
from ..models import (
    Conversation,
    ConversationList,
    ConversationRequest,
    ConversationResponse,
)
from ..tracing import HASpanExporter

_LOGGER = logging.getLogger('uvicorn.error')

def construct_prompt(ctx_wrapper: RunContextWrapper[Any], agent: Agent | None) -> str:
    """Construct prompt for the agent."""
    instructions = "You are a helpful assistant that helps with tasks around the home. You will be given instructions that you are asked to follow. You can use the tools provided to you to control devices in the home in order to complete the task. When you have completed the task, you should respond with a summary of the task and the result in first person (e.g. I turned on the lights)."

    home_state = ctx_wrapper.context["home_state"]

    return instructions + "\n\n" + str(home_state)

class ConversationService:
    """Service for handling agent conversations."""

    @staticmethod
    async def get_conversations(db: AsyncSession) -> ConversationList:
        """Get all conversations from the database."""
        conversations = []
        stmt = select(Trace).options(selectinload(Trace.spans))
        traces = (await db.execute(stmt)).unique().scalars().all()
        for trace in traces:
            first_generation_span = next(
                (span for span in trace.spans if span.span_type == "generation"),
                None,
            )

            if first_generation_span:
                try:
                    instruction = first_generation_span.span_data["input"][1]["content"]
                    conversations.append(
                        Conversation(
                            id=trace.id,
                            started_at=first_generation_span.started_at,
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
    async def process_conversation(
        conversation_request: ConversationRequest,
        openai_client: AsyncOpenAI,
        hass_client: httpx.AsyncClient,
        tools: List[Tool],
        model_id: str,
        db_engine: Engine,
    ) -> ConversationResponse:
        """Process a conversation with the agent."""
        set_trace_processors([BatchTraceProcessor(exporter=HASpanExporter(db_engine))])

        agent = Agent(
            name="Home Agent",
            model=OpenAIChatCompletionsModel(
                model=model_id,
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

        context: Dict[str, Any] = {
            "conversation_id": conversation_request.conversation_id,
            "language": conversation_request.language,
            "home_state": conversation_request.home_state,
            "hass_client": hass_client,
        }

        input = conversation_request.text

        try:
            result = await Runner.run(
                starting_agent=agent,
                input=input,
                context=context,
                max_turns=3,
            )
            return ConversationResponse(response=result.final_output)

        except Exception as e:
            _LOGGER.error(f"Error processing conversation: {e}")
            return ConversationResponse(
                response=f"I apologize, but I encountered an error: {str(e)}"
            ) 