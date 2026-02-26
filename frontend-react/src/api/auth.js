const BASE = "http://localhost:8000";

function authHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  };
}

export async function apiLogin(username, password) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Login failed");
  return data; // { token, username, user_id }
}

export async function apiRegister(username, password) {
  const res = await fetch(`${BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Registration failed");
  return data; // { token, username, user_id }
}

export async function apiGetThreads() {
  const res = await fetch(`${BASE}/auth/threads`, { headers: authHeaders() });
  if (res.status === 401) throw new Error("UNAUTHORIZED");
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to load threads");
  return data.threads; // [{ id, thread_id, label, created_at }]
}

export async function apiCreateThread(label = null) {
  const res = await fetch(`${BASE}/auth/threads`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ label }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to create thread");
  return data; // { id, thread_id, label, created_at }
}
