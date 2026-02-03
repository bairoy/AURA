# Aura — Voice Assistant

## Autonomous Understanding Reasoning Assistant

## Quick start

### Go to Backend Directory

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables in `.env`:
   - `ASSEMBLYAI_API_KEY`
   - `CARTESIA_API_KEY`
3. Run the server:

```bash
uvicorn src.main:app --reload --port 8000
```

## API

- WebSocket: `ws://<host>:8000/ws`
  - Send: binary audio frames (chunks from MediaRecorder or similar)
  - Receive: JSON events (see `Events`)

## Events

- `stt_chunk`, `stt_output` — interim / final transcriptions
- `agent_chunk`, `agent_end` — agent response chunks and completion
- `tts_chunk` — base64-encoded audio chunk
- `tool_call`, `tool_result` — tool invocation and results

## Important files

- `src/main.py` — pipeline and WebSocket endpoint
- `src/assemblyai_stt.py` — AssemblyAI STT client
- `src/cartesia_tts.py` — Cartesia TTS client
- `src/events.py` — event types and serialization
- `tests/ws_test.py` — basic connectivity test
- `frontend/test.html` — minimal browser client example

## Testing

- Connectivity test:

```bash
python3 tests/ws_test.py
```
