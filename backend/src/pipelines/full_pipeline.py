from langchain_core.runnables import RunnableGenerator
from src.pipelines.stt_pipeline import stt_stream
from src.pipelines.agent_pipeline import agent_stream
from src.pipelines.tts_pipeline import tts_stream

pipeline = (
  RunnableGenerator(stt_stream) | RunnableGenerator(agent_stream) | RunnableGenerator(tts_stream)
)