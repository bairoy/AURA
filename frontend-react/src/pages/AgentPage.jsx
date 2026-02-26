import { useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useVoiceAgent } from "../hooks/useVoiceAgent";

export default function AgentPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const threadId = location.state?.threadId;
  const username = localStorage.getItem("username");
  const logEndRef = useRef(null);

  const { status, logs, start, stop } = useVoiceAgent(threadId);

  // Redirect if no threadId passed
  useEffect(() => {
    if (!threadId) navigate("/threads");
  }, [threadId]);

  // Auto-scroll log
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  function handleBack() {
    stop();
    navigate("/threads");
  }

  const isActive = status === "active";
  const isConnecting = status === "connecting";

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-xl bg-gray-900 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
        {/* Top bar */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-green-400">🎙 Aura</h1>
            <p className="text-gray-500 text-xs mt-0.5">👤 {username}</p>
          </div>
          <button
            onClick={handleBack}
            className="text-gray-500 hover:text-white text-sm transition-colors"
          >
            ← Back
          </button>
        </div>

        {/* Status indicator */}
        <div className="flex items-center gap-2">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              isActive
                ? "bg-green-400 animate-pulse"
                : isConnecting
                  ? "bg-yellow-400 animate-pulse"
                  : "bg-gray-600"
            }`}
          />
          <span className="text-gray-400 text-sm capitalize">
            {status === "idle"
              ? "Ready to start"
              : status === "connecting"
                ? "Connecting..."
                : status === "active"
                  ? "Listening..."
                  : "Stopped"}
          </span>
        </div>

        {/* Log window */}
        <div className="bg-gray-950 rounded-xl p-4 h-64 overflow-y-auto font-mono text-xs">
          {logs.length === 0 ? (
            <p className="text-gray-700">Press Start and speak...</p>
          ) : (
            logs.map((l) => (
              <div key={l.id} className="text-green-300 mb-0.5 leading-relaxed">
                {l.text}
              </div>
            ))
          )}
          <div ref={logEndRef} />
        </div>

        {/* Controls */}
        <div className="flex gap-3">
          <button
            onClick={start}
            disabled={isActive || isConnecting}
            className="flex-1 py-3 bg-green-500 hover:bg-green-400 disabled:bg-gray-700 disabled:text-gray-500 text-black font-bold rounded-lg transition-colors"
          >
            {isConnecting ? "Connecting..." : "▶ Start"}
          </button>
          <button
            onClick={stop}
            disabled={status === "idle" || status === "stopped"}
            className="flex-1 py-3 bg-red-600 hover:bg-red-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-bold rounded-lg transition-colors"
          >
            ⏹ Stop
          </button>
        </div>
      </div>
    </div>
  );
}
