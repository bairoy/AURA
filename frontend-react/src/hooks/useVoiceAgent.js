import { useState, useRef, useCallback } from "react";

const WS_URL = "ws://localhost:8000/ws";

export function useVoiceAgent(threadId) {
  const [status, setStatus] = useState("idle"); // idle | connecting | active | stopped
  const [logs, setLogs] = useState([]);

  const wsRef = useRef(null);
  const audioCtxRef = useRef(null);
  const micSourceRef = useRef(null);
  const processorRef = useRef(null);
  const audioQueueRef = useRef([]);
  const currentSourceRef = useRef(null);

  function addLog(text) {
    setLogs((prev) => [...prev, { id: Date.now() + Math.random(), text }]);
  }

  // ── Audio playback ──────────────────────────────────────────────────────────
  function playNextChunk() {
    if (currentSourceRef.current || audioQueueRef.current.length === 0) return;

    const samples = audioQueueRef.current.shift();
    const ctx = audioCtxRef.current;
    if (!ctx) return;

    const buffer = ctx.createBuffer(1, samples.length, 24000);
    buffer.getChannelData(0).set(samples);

    const src = ctx.createBufferSource();
    src.buffer = buffer;
    src.connect(ctx.destination);
    currentSourceRef.current = src;

    src.onended = () => {
      currentSourceRef.current = null;
      playNextChunk();
    };
    src.start(0);
  }

  function handleTtsChunk(b64Audio) {
    const binary = atob(b64Audio);
    const pcmBytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) pcmBytes[i] = binary.charCodeAt(i);

    const samples = new Float32Array(pcmBytes.length / 2);
    for (let i = 0; i < samples.length; i++) {
      const lo = pcmBytes[i * 2];
      const hi = pcmBytes[i * 2 + 1];
      let val = (hi << 8) | lo;
      if (val >= 0x8000) val -= 0x10000;
      samples[i] = val / 32768;
    }

    audioQueueRef.current.push(samples);
    playNextChunk();
  }

  // ── Start ───────────────────────────────────────────────────────────────────
  const start = useCallback(async () => {
    if (!threadId) return;
    setStatus("connecting");
    setLogs([]);

    const token = localStorage.getItem("token");
    const ws = new WebSocket(`${WS_URL}?token=${token}&thread_id=${threadId}`);
    wsRef.current = ws;
    ws.binaryType = "arraybuffer";

    ws.onopen = async () => {
      addLog("🟢 Connected");
      setStatus("active");

      const ctx = new AudioContext({ sampleRate: 24000 });
      audioCtxRef.current = ctx;

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const micSource = ctx.createMediaStreamSource(stream);
      const processor = ctx.createScriptProcessor(4096, 1, 1);
      micSource.connect(processor);
      processor.connect(ctx.destination);
      micSourceRef.current = micSource;
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        const input = e.inputBuffer.getChannelData(0);
        const buf = new ArrayBuffer(input.length * 2);
        const view = new DataView(buf);
        for (let i = 0; i < input.length; i++) {
          const s = Math.max(-1, Math.min(1, input[i]));
          view.setInt16(i * 2, s * 0x7fff, true);
        }
        if (ws.readyState === WebSocket.OPEN) ws.send(buf);
      };
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "stt_chunk") addLog(`STT: ${msg.transcript}`);
      if (msg.type === "stt_output") addLog(`📝 ${msg.transcript}`);
      if (msg.type === "agent_chunk") addLog(`🤖 ${msg.text}`);
      if (msg.type === "tts_chunk") handleTtsChunk(msg.audio);
    };

    ws.onclose = () => {
      addLog("🔴 Disconnected");
      setStatus("stopped");
    };

    ws.onerror = () => {
      addLog("❌ WebSocket error");
      setStatus("stopped");
    };
  }, [threadId]);

  // ── Stop ────────────────────────────────────────────────────────────────────
  const stop = useCallback(() => {
    try {
      if (currentSourceRef.current) {
        currentSourceRef.current.stop();
        currentSourceRef.current = null;
      }
      processorRef.current?.disconnect();
      micSourceRef.current?.disconnect();
      audioCtxRef.current?.close();
    } catch {}
    if (wsRef.current?.readyState === WebSocket.OPEN) wsRef.current.close();
    audioQueueRef.current = [];
    setStatus("stopped");
    addLog("⏹ Stopped");
  }, []);

  return { status, logs, start, stop };
}
