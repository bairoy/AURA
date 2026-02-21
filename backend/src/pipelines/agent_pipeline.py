from typing import AsyncIterator
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.core.agent import get_agent_with_checkpointer
from src.events import (
    VoiceAgentEvent,
    AgentChunkEvent,
    AgentEndEvent,
    ToolCallEvent,
    ToolResultEvent,
)


# Store thread_id at module level so it persists across websocket reconnections
_current_thread_id = None
_agent_instance = None


async def agent_stream(event_stream: AsyncIterator[VoiceAgentEvent]) -> AsyncIterator[VoiceAgentEvent]:
    global _current_thread_id, _agent_instance
    
    print("🔵 agent_stream called")
    
    # Create thread_id only once per app lifecycle
    if _current_thread_id is None:
        _current_thread_id = str(uuid4())
        print(f"🧵 New conversation thread: {_current_thread_id}")
    else:
        print(f"🧵 Continuing conversation thread: {_current_thread_id}")
    
    # Initialize agent with checkpointer (reuse if already created)
    if _agent_instance is None:
        print("🔄 Initializing agent with checkpointer...")
        _agent_instance = await get_agent_with_checkpointer()
        print(f"🤖 Agent initialized: {type(_agent_instance)}")

    async for event in event_stream:
        yield event

        if event.type == "stt_output":
            print(f"💬 User said: '{event.transcript}' (thread: {_current_thread_id})")
            
            try:
                stream = _agent_instance.astream(
                    {"messages": [HumanMessage(content=event.transcript)]},
                    {"configurable": {"thread_id": _current_thread_id}},
                    stream_mode="messages",
                )

                response_text = ""
                async for message, _ in stream:

                    if isinstance(message, AIMessage):
                        if message.content:
                            response_text += message.content
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

                print(f"🤖 Aura responded: '{response_text.strip()}'")
            except Exception as e:
                print(f"❌ Error in agent stream: {e}")
                import traceback
                traceback.print_exc()
                
            yield AgentEndEvent.create()