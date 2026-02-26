import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiLogin, apiRegister } from "../api/auth";

export default function LoginPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const fn = mode === "login" ? apiLogin : apiRegister;
      const data = await fn(username.trim(), password);
      localStorage.setItem("token", data.token);
      localStorage.setItem("username", data.username);
      navigate("/threads");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-gray-900 rounded-2xl p-8 shadow-xl">
        {/* Header */}
        <h1 className="text-3xl font-bold text-green-400 mb-1">🎙 Aura</h1>
        <p className="text-gray-400 text-sm mb-8">
          {mode === "login"
            ? "Sign in to your account"
            : "Create a new account"}
        </p>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-green-500"
            required
            autoFocus
          />
          <input
            type="password"
            placeholder={
              mode === "register" ? "Password (min 6 chars)" : "Password"
            }
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-green-500"
            required
          />

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-green-500 hover:bg-green-400 disabled:bg-green-800 text-black font-bold rounded-lg transition-colors"
          >
            {loading
              ? "Please wait..."
              : mode === "login"
                ? "Login"
                : "Register"}
          </button>
        </form>

        {/* Toggle */}
        <p className="text-gray-500 text-sm text-center mt-6">
          {mode === "login" ? (
            <>
              No account?{" "}
              <button
                onClick={() => {
                  setMode("register");
                  setError("");
                }}
                className="text-green-400 hover:underline"
              >
                Register
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button
                onClick={() => {
                  setMode("login");
                  setError("");
                }}
                className="text-green-400 hover:underline"
              >
                Login
              </button>
            </>
          )}
        </p>
      </div>
    </div>
  );
}
