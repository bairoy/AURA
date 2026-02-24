from typing import AsyncIterator
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
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


# async def agent_stream(event_stream: AsyncIterator[VoiceAgentEvent]) -> AsyncIterator[VoiceAgentEvent]:
#     global _current_thread_id, _agent_instance
    
#     print("🔵 agent_stream called")
    
#     # Create thread_id only once per app lifecycle
#     if _current_thread_id is None:
#         _current_thread_id = str(uuid4())
#         print(f"🧵 New conversation thread: {_current_thread_id}")
#     else:
#         print(f"🧵 Continuing conversation thread: {_current_thread_id}")
    
#     # Initialize agent with checkpointer (reuse if already created)
#     if _agent_instance is None:
#         print("🔄 Initializing agent with checkpointer...")
#         _agent_instance = await get_agent_with_checkpointer()
#         print(f"🤖 Agent initialized: {type(_agent_instance)}")

#     async for event in event_stream:
#         yield event

#         if event.type == "stt_output":
#             print(f"💬 User said: '{event.transcript}' (thread: {_current_thread_id})")
            
#             try:
#                 stream = _agent_instance.astream(
#                     {"messages": [HumanMessage(content=event.transcript)]},
#                     {"configurable": {"thread_id": _current_thread_id}},
#                     stream_mode="messages",
#                 )

#                 response_text = ""
#                 async for message, _ in stream:

#                     if isinstance(message, AIMessage):
#                         if message.content:
#                             response_text += message.content
#                             yield AgentChunkEvent.create(message.content)

#                         if getattr(message, "tool_calls", None):
#                             for tool_call in message.tool_calls:
#                                 yield ToolCallEvent.create(
#                                     id=tool_call.get("id", str(uuid4())),
#                                     name=tool_call.get("name", "unknown"),
#                                     args=tool_call.get("args", {}),
#                                 )

#                     if isinstance(message, ToolMessage):
#                         yield ToolResultEvent.create(
#                             tool_call_id=getattr(message, "tool_call_id", ""),
#                             name=getattr(message, "name", "unknown"),
#                             result=str(message.content or ""),
#                         )

#                 print(f"🤖 Aura responded: '{response_text.strip()}'")
#             except Exception as e:
#                 print(f"❌ Error in agent stream: {e}")
#                 import traceback
#                 traceback.print_exc()
                
#             yield AgentEndEvent.create()



async def agent_stream(event_stream: AsyncIterator[VoiceAgentEvent]) -> AsyncIterator[VoiceAgentEvent]:
    global _current_thread_id, _agent_instance
    
    print("🔵 agent_stream called")
    
    if _current_thread_id is None:
        _current_thread_id = str(uuid4())
        print(f"🧵 New conversation thread: {_current_thread_id}")
    else:
        print(f"🧵 Continuing conversation thread: {_current_thread_id}")
    
    if _agent_instance is None:
        print("🔄 Initializing agent with checkpointer...")
        _agent_instance = await get_agent_with_checkpointer()
        print(f"🤖 Agent initialized: {type(_agent_instance)}")

    async for event in event_stream:
        yield event

        if event.type == "stt_output":
            print(f"💬 User said: '{event.transcript}' (thread: {_current_thread_id})")
            
            config = {"configurable": {"thread_id": _current_thread_id}}
            
            try:
                stream = _agent_instance.astream(
                    {"messages": [HumanMessage(content=event.transcript)]},
                    config,
                    stream_mode="messages",
                )

                response_text = ""
                pending_tool_calls = []  # track (id, name) of tool calls seen

                async for message, _ in stream:

                    if isinstance(message, AIMessage):
                        if message.content:
                            response_text += message.content
                            yield AgentChunkEvent.create(message.content)

                        if getattr(message, "tool_calls", None):
                            for tool_call in message.tool_calls:
                                pending_tool_calls.append({
                                    "id": tool_call.get("id"),
                                    "name": tool_call.get("name", "unknown"),
                                })
                                yield ToolCallEvent.create(
                                    id=tool_call.get("id", str(uuid4())),
                                    name=tool_call.get("name", "unknown"),
                                    args=tool_call.get("args", {}),
                                )

                    if isinstance(message, ToolMessage):
                        # Remove from pending as it completed successfully
                        pending_tool_calls = [
                            tc for tc in pending_tool_calls
                            if tc["id"] != message.tool_call_id
                        ]
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

                # ✅ KEY FIX: For every dangling tool call, inject an error ToolMessage
                # back into the checkpointer state so the graph isn't corrupted.
                if pending_tool_calls:
                    error_tool_messages = [
                        ToolMessage(
                            content=f"Tool execution failed with error: {str(e)}",
                            tool_call_id=tc["id"],
                            name=tc["name"],
                        )
                        for tc in pending_tool_calls
                    ]
                    # Update the graph state with the error messages
                    await _agent_instance.aupdate_state(
                        config,
                        {"messages": error_tool_messages},
                    )
                    print(f"🔧 Injected {len(error_tool_messages)} error ToolMessage(s) to fix state")
                    pending_tool_calls = []

                error_msg = "I tried to use a tool but it didn't work. Let me try answering directly."
                yield AgentChunkEvent.create(error_msg)

            yield AgentEndEvent.create()