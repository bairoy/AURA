// let ws;
// let audioContext;
// let source;
// let processor;
// let audioQueue = [];
// let currentSource = null; // Track current playing source

// const logBox = document.getElementById("log");
// const startBtn = document.getElementById("start");
// const stopBtn = document.getElementById("stop");

// function log(text) {
//   logBox.textContent += text + "\n";
//   logBox.scrollTop = logBox.scrollHeight;
// }

// startBtn.onclick = async () => {
//   log("Starting...");

//   ws = new WebSocket("ws://localhost:8000/ws");
//   ws.binaryType = "arraybuffer";

//   ws.onopen = async () => {
//     log("WebSocket connected");

//     // Match Cartesia's sample rate
//     audioContext = new AudioContext({ sampleRate: 24000 });

//     const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

//     source = audioContext.createMediaStreamSource(stream);
//     processor = audioContext.createScriptProcessor(4096, 1, 1);

//     source.connect(processor);
//     processor.connect(audioContext.destination);

//     processor.onaudioprocess = (e) => {
//       const input = e.inputBuffer.getChannelData(0);
//       const buffer = new ArrayBuffer(input.length * 2);
//       const view = new DataView(buffer);

//       for (let i = 0; i < input.length; i++) {
//         let s = Math.max(-1, Math.min(1, input[i]));
//         view.setInt16(i * 2, s * 0x7fff, true);
//       }

//       if (ws.readyState === WebSocket.OPEN) {
//         ws.send(buffer);
//       }
//     };
//   };

//   ws.onmessage = async (event) => {
//     const msg = JSON.parse(event.data);

//     if (msg.type === "stt_chunk") {
//       log("STT: " + msg.transcript);
//     }

//     if (msg.type === "stt_output") {
//       log("FINAL: " + msg.transcript);
//     }

//     if (msg.type === "agent_chunk") {
//       log("AGENT: " + msg.text);
//     }

//     if (msg.type === "tts_chunk") {
//       const binary = atob(msg.audio);
//       const pcmBytes = new Uint8Array(binary.length);

//       for (let i = 0; i < binary.length; i++) {
//         pcmBytes[i] = binary.charCodeAt(i);
//       }

//       // PCM16 -> Float32
//       const samples = new Float32Array(pcmBytes.length / 2);
//       for (let i = 0; i < samples.length; i++) {
//         const lo = pcmBytes[i * 2];
//         const hi = pcmBytes[i * 2 + 1];
//         let val = (hi << 8) | lo;
//         if (val >= 0x8000) val -= 0x10000;
//         samples[i] = val / 32768;
//       }

//       audioQueue.push(samples);
//       playNextChunk(); // Always try to play
//     }
//   };

//   ws.onclose = () => log("WebSocket closed");
//   ws.onerror = () => log("WebSocket error");
// };

// stopBtn.onclick = () => {
//   log("Stopping...");

//   try {
//     if (currentSource) {
//       currentSource.stop();
//       currentSource = null;
//     }
//     processor?.disconnect();
//     source?.disconnect();
//   } catch {}

//   if (ws && ws.readyState === WebSocket.OPEN) {
//     ws.close();
//   }

//   audioQueue = [];
// };

// function playNextChunk() {
//   // Don't play if already playing
//   if (currentSource !== null) {
//     return;
//   }

//   if (audioQueue.length === 0) {
//     return;
//   }

//   const samples = audioQueue.shift();

//   const buffer = audioContext.createBuffer(1, samples.length, 24000);
//   buffer.getChannelData(0).set(samples);

//   const bufferSource = audioContext.createBufferSource();
//   bufferSource.buffer = buffer;
//   bufferSource.connect(audioContext.destination);

//   currentSource = bufferSource;

//   bufferSource.onended = () => {
//     currentSource = null;
//     playNextChunk(); // Play next chunk when this one ends
//   };

//   bufferSource.start(0);
// }
// ── State ──────────────────────────────────────────────────────────────────────
let token = localStorage.getItem("token");
let username = localStorage.getItem("username");
let currentThreadId = null;

let ws;
let audioContext;
let micSource;
let processor;
let audioQueue = [];
let currentAudioSource = null;

// ── DOM Ready ──────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  // Navigation
  document.getElementById("go-register").onclick = () =>
    showScreen("register-screen");
  document.getElementById("go-login").onclick = () =>
    showScreen("login-screen");
  document.getElementById("logout-btn").onclick = doLogout;
  document.getElementById("back-btn").onclick = goToThreadSelect;

  // Auth
  document.getElementById("login-btn").onclick = doLogin;
  document.getElementById("register-btn").onclick = doRegister;

  // Enter key on password fields
  document.getElementById("login-password").onkeydown = (e) => {
    if (e.key === "Enter") doLogin();
  };
  document.getElementById("reg-password").onkeydown = (e) => {
    if (e.key === "Enter") doRegister();
  };

  // Thread
  document.getElementById("new-thread-btn").onclick = startNewThread;

  // Agent controls
  document.getElementById("start").onclick = startListening;
  document.getElementById("stop").onclick = stopSession;

  // Boot
  if (token) {
    await showThreadSelect();
  } else {
    showScreen("login-screen");
  }
});

// ── Screen helper ──────────────────────────────────────────────────────────────
function showScreen(id) {
  document
    .querySelectorAll(".screen")
    .forEach((s) => s.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

function log(text) {
  const box = document.getElementById("log");
  box.textContent += text + "\n";
  box.scrollTop = box.scrollHeight;
}

// ── Auth ───────────────────────────────────────────────────────────────────────
async function doLogin() {
  const u = document.getElementById("login-username").value.trim();
  const p = document.getElementById("login-password").value;
  document.getElementById("login-error").textContent = "";

  if (!u || !p) {
    document.getElementById("login-error").textContent =
      "Please enter username and password";
    return;
  }

  const res = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: u, password: p }),
  });

  const data = await res.json();
  if (!res.ok) {
    document.getElementById("login-error").textContent =
      data.detail || "Login failed";
    return;
  }

  saveAuth(data.token, data.username);
  await showThreadSelect();
}

async function doRegister() {
  const u = document.getElementById("reg-username").value.trim();
  const p = document.getElementById("reg-password").value;
  document.getElementById("register-error").textContent = "";

  if (!u || !p) {
    document.getElementById("register-error").textContent =
      "Please fill in all fields";
    return;
  }

  const res = await fetch("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: u, password: p }),
  });

  const data = await res.json();
  if (!res.ok) {
    document.getElementById("register-error").textContent =
      data.detail || "Registration failed";
    return;
  }

  saveAuth(data.token, data.username);
  await showThreadSelect();
}

function saveAuth(t, u) {
  token = t;
  username = u;
  localStorage.setItem("token", t);
  localStorage.setItem("username", u);
}

function doLogout() {
  localStorage.removeItem("token");
  localStorage.removeItem("username");
  token = null;
  username = null;
  currentThreadId = null;
  stopSession();
  showScreen("login-screen");
}

// ── Thread Select ──────────────────────────────────────────────────────────────
async function showThreadSelect() {
  showScreen("thread-screen");

  const res = await fetch("/auth/threads", {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    doLogout();
    return;
  }

  const data = await res.json();
  const threads = data.threads || [];

  const container = document.getElementById("thread-list-container");
  const list = document.getElementById("thread-list");
  list.innerHTML = "";

  if (threads.length > 0) {
    container.style.display = "block";
    threads.forEach((t) => {
      const item = document.createElement("div");
      item.className = "thread-item";
      item.innerHTML = `
        <div class="label">${t.label}</div>
        <div class="date">${new Date(t.created_at).toLocaleString()}</div>
      `;
      item.onclick = () => startSession(t.thread_id);
      list.appendChild(item);
    });
  } else {
    container.style.display = "none";
  }
}

async function startNewThread() {
  const res = await fetch("/auth/threads", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({}),
  });

  const thread = await res.json();
  startSession(thread.thread_id);
}

function goToThreadSelect() {
  stopSession();
  showThreadSelect();
}

// ── Agent Session ──────────────────────────────────────────────────────────────
function startSession(threadId) {
  currentThreadId = threadId;
  document.getElementById("user-label").textContent = `👤 ${username}`;
  document.getElementById("log").textContent = "";
  showScreen("agent-screen");
}

async function startListening() {
  if (!currentThreadId) {
    log("No thread selected.");
    return;
  }
  log("Starting...");

  const wsUrl = `ws://localhost:8000/ws?token=${token}&thread_id=${currentThreadId}`;
  ws = new WebSocket(wsUrl);
  ws.binaryType = "arraybuffer";

  ws.onopen = async () => {
    log("WebSocket connected");
    audioContext = new AudioContext({ sampleRate: 24000 });
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    micSource = audioContext.createMediaStreamSource(stream);
    processor = audioContext.createScriptProcessor(4096, 1, 1);
    micSource.connect(processor);
    processor.connect(audioContext.destination);

    processor.onaudioprocess = (e) => {
      const input = e.inputBuffer.getChannelData(0);
      const buffer = new ArrayBuffer(input.length * 2);
      const view = new DataView(buffer);
      for (let i = 0; i < input.length; i++) {
        let s = Math.max(-1, Math.min(1, input[i]));
        view.setInt16(i * 2, s * 0x7fff, true);
      }
      if (ws.readyState === WebSocket.OPEN) ws.send(buffer);
    };
  };

  ws.onmessage = async (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === "stt_chunk") log("STT: " + msg.transcript);
    if (msg.type === "stt_output") log("FINAL: " + msg.transcript);
    if (msg.type === "agent_chunk") log("AGENT: " + msg.text);

    if (msg.type === "tts_chunk") {
      const binary = atob(msg.audio);
      const pcmBytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++)
        pcmBytes[i] = binary.charCodeAt(i);

      const samples = new Float32Array(pcmBytes.length / 2);
      for (let i = 0; i < samples.length; i++) {
        const lo = pcmBytes[i * 2];
        const hi = pcmBytes[i * 2 + 1];
        let val = (hi << 8) | lo;
        if (val >= 0x8000) val -= 0x10000;
        samples[i] = val / 32768;
      }
      audioQueue.push(samples);
      playNextChunk();
    }
  };

  ws.onclose = () => log("WebSocket closed");
  ws.onerror = () => log("WebSocket error");
}

function stopSession() {
  try {
    if (currentAudioSource) {
      currentAudioSource.stop();
      currentAudioSource = null;
    }
    processor?.disconnect();
    micSource?.disconnect();
  } catch {}
  if (ws && ws.readyState === WebSocket.OPEN) ws.close();
  audioQueue = [];
}

function playNextChunk() {
  if (currentAudioSource !== null || audioQueue.length === 0) return;

  const samples = audioQueue.shift();
  const buffer = audioContext.createBuffer(1, samples.length, 24000);
  buffer.getChannelData(0).set(samples);

  const src = audioContext.createBufferSource();
  src.buffer = buffer;
  src.connect(audioContext.destination);
  currentAudioSource = src;

  src.onended = () => {
    currentAudioSource = null;
    playNextChunk();
  };
  src.start(0);
}
