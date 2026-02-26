import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiGetThreads, apiCreateThread } from "../api/auth";

export default function ThreadsPage() {
  const navigate = useNavigate();
  const username = localStorage.getItem("username");
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadThreads();
  }, []);

  async function loadThreads() {
    try {
      const data = await apiGetThreads();
      setThreads(data);
    } catch (err) {
      if (err.message === "UNAUTHORIZED") logout();
    } finally {
      setLoading(false);
    }
  }

  async function handleNewThread() {
    setCreating(true);
    try {
      const thread = await apiCreateThread();
      navigate("/agent", { state: { threadId: thread.thread_id } });
    } catch (err) {
      console.error(err);
    } finally {
      setCreating(false);
    }
  }

  function handleContinue(threadId) {
    navigate("/agent", { state: { threadId } });
  }

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    navigate("/login");
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-gray-900 rounded-2xl p-8 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-green-400">🎙 Aura</h1>
            <p className="text-gray-400 text-sm mt-1">
              Welcome back, {username}
            </p>
          </div>
          <button
            onClick={logout}
            className="text-gray-500 hover:text-red-400 text-sm transition-colors"
          >
            Logout
          </button>
        </div>

        {/* New conversation */}
        <button
          onClick={handleNewThread}
          disabled={creating}
          className="w-full py-3 bg-green-500 hover:bg-green-400 disabled:bg-green-800 text-black font-bold rounded-lg transition-colors mb-6"
        >
          {creating ? "Creating..." : "➕ New Conversation"}
        </button>

        {/* Previous conversations */}
        {loading ? (
          <p className="text-gray-500 text-sm text-center">Loading...</p>
        ) : threads.length > 0 ? (
          <div>
            <p className="text-gray-400 text-sm font-medium mb-3">
              Continue a previous conversation:
            </p>
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {threads.map((t) => (
                <button
                  key={t.id}
                  onClick={() => handleContinue(t.thread_id)}
                  className="w-full text-left px-4 py-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-green-600 rounded-lg transition-colors"
                >
                  <p className="text-white font-medium text-sm">{t.label}</p>
                  <p className="text-gray-500 text-xs mt-1">
                    {new Date(t.created_at).toLocaleString()}
                  </p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-gray-600 text-sm text-center">
            No previous conversations yet.
          </p>
        )}
      </div>
    </div>
  );
}
