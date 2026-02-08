from typing import AsyncIterator
from uuid import uuid4

from langchain.messages import AIMessage, HumanMessage, ToolMessage

from src.core.agent import agent
from src.events import (
    VoiceAgentEvent,
    AgentChunkEvent,
    AgentEndEvent,
    ToolCallEvent,
    ToolResultEvent,
)


async def agent_stream(event_stream: AsyncIterator[VoiceAgentEvent]) -> AsyncIterator[VoiceAgentEvent]:

    thread_id = str(uuid4())

    async for event in event_stream:
        yield event

        if event.type == "stt_output":

            stream = agent.astream(
                {"messages": [HumanMessage(content=event.transcript)]},
                {"configurable": {"thread_id": thread_id}},
                stream_mode="messages",
            )

            async for message, _ in stream:

                if isinstance(message, AIMessage):
                    yield AgentChunkEvent.create(message.content)

                    if getattr(message, "tool_calls", None):
                        for tool_call in message.tool_calls:
                            yield ToolCallEvent.create(
                                id=tool_call.get("id", str(uuid4())),
                                name=tool_call.get("name", "unknown"),
                                args=tool_call.get("args", {}),
                            )

                if isinstance(message, ToolMessage):
                    yield ToolResultEvent.create(
                        tool_call_id=getattr(message, "tool_call_id", ""),
                        name=getattr(message, "name", "unknown"),
                        result=str(message.content or ""),
                    )

            yield AgentEndEvent.create()
