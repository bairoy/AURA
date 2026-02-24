// let ws;
// let audioContext;
// let source;
// let processor;
// let playtime = 0;
// const PLAY_AHEAD = 0.05;
// let ttsQueue = [];
// let isPlaying = false;

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

//     audioContext = new AudioContext({ sampleRate: 16000 });

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

//   // smooth TTS playback
//   let audioQueue = Promise.resolve();

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

//       ttsQueue.push(samples);

//       if (!isPlaying) {
//         playNextChunk();
//       }
//     }
//   };

//   ws.onclose = () => log("WebSocket closed");
//   ws.onerror = () => log("WebSocket error");
// };

// stopBtn.onclick = () => {
//   log("Stopping...");

//   try {
//     processor?.disconnect();
//     source?.disconnect();
//   } catch {}

//   if (ws && ws.readyState === WebSocket.OPEN) {
//     ws.close();
//   }
// };
// function playNextChunk() {
//   if (ttsQueue.length === 0) {
//     isPlaying = false;
//     return;
//   }

//   isPlaying = true;

//   const samples = ttsQueue.shift();

//   const buffer = audioContext.createBuffer(
//     1,
//     samples.length,
//     24000, // Cartesia sample rate
//   );

//   buffer.getChannelData(0).set(samples);

//   const source = audioContext.createBufferSource();
//   source.buffer = buffer;
//   source.connect(audioContext.destination);

//   source.onended = () => {
//     playNextChunk();
//   };

//   source.start();
// }

// let ws;
// let audioContext;
// let source;
// let processor;
// let audioQueue = [];
// let isPlaying = false;
// let nextStartTime = 0;

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

//     audioContext = new AudioContext({ sampleRate: 24000 });
//     nextStartTime = audioContext.currentTime;

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

//       // PCM16 -> Float 32

//       const samples = new Float32Array(pcmBytes.length / 2);
//       for (let i = 0; i < samples.length; i++) {
//         const lo = pcmBytes[i * 2];
//         const hi = pcmBytes[i * 2 + 1];
//         let val = (hi << 8) | lo;
//         if (val >= 0x8000) val -= 0x10000;
//         samples[i] = val / 32768;
//       }

//       audioQueue.push(samples);

//       if (!isPlaying) {
//         playNextChunk();
//       }
//     }
//   };
//   ws.onclose = () => log("WebSocked closed");
//   ws.onerror = () => log("WebSocekt error");
// };

// stopBtn.onclick = () => {
//   log("Stopping...");
//   try {
//     processor?.disconnect();
//     source?.disconnect();
//   } catch {}

//   if (ws && ws.readyState === WebSocket.OPEN) {
//     ws.close();
//   }

//   audioQueue = [];
//   isPlaying = false;
// };

// function playNextChunk() {
//   if (audioQueue.length === 0) {
//     isPlaying = false;
//     return;
//   }
//   isPlaying = true;
//   const samples = audioQueue.shift();

//   const buffer = audioContext.createBuffer(1, samples.length, 24000);
//   buffer.getChannelData(0).set(samples);

//   const bufferSource = audioContext.createBufferSource();
//   bufferSource.buffer = buffer;
//   bufferSource.connect(audioContext.destination);

//   const now = audioContext.currentTime;
//   const startTime = Math.max(now, nextStartTime);

//   bufferSource.start(startTime);
//   nextStartTime = startTime + buffer.duration;

//   bufferSource.onended = () => {
//     playNextChunk();
//   };
// }
let ws;
let audioContext;
let source;
let processor;
let audioQueue = [];
let currentSource = null; // Track current playing source

const logBox = document.getElementById("log");
const startBtn = document.getElementById("start");
const stopBtn = document.getElementById("stop");

function log(text) {
  logBox.textContent += text + "\n";
  logBox.scrollTop = logBox.scrollHeight;
}

startBtn.onclick = async () => {
  log("Starting...");

  ws = new WebSocket("ws://localhost:8000/ws");
  ws.binaryType = "arraybuffer";

  ws.onopen = async () => {
    log("WebSocket connected");

    // Match Cartesia's sample rate
    audioContext = new AudioContext({ sampleRate: 24000 });

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    source = audioContext.createMediaStreamSource(stream);
    processor = audioContext.createScriptProcessor(4096, 1, 1);

    source.connect(processor);
    processor.connect(audioContext.destination);

    processor.onaudioprocess = (e) => {
      const input = e.inputBuffer.getChannelData(0);
      const buffer = new ArrayBuffer(input.length * 2);
      const view = new DataView(buffer);

      for (let i = 0; i < input.length; i++) {
        let s = Math.max(-1, Math.min(1, input[i]));
        view.setInt16(i * 2, s * 0x7fff, true);
      }

      if (ws.readyState === WebSocket.OPEN) {
        ws.send(buffer);
      }
    };
  };

  ws.onmessage = async (event) => {
    const msg = JSON.parse(event.data);

    if (msg.type === "stt_chunk") {
      log("STT: " + msg.transcript);
    }

    if (msg.type === "stt_output") {
      log("FINAL: " + msg.transcript);
    }

    if (msg.type === "agent_chunk") {
      log("AGENT: " + msg.text);
    }

    if (msg.type === "tts_chunk") {
      const binary = atob(msg.audio);
      const pcmBytes = new Uint8Array(binary.length);

      for (let i = 0; i < binary.length; i++) {
        pcmBytes[i] = binary.charCodeAt(i);
      }

      // PCM16 -> Float32
      const samples = new Float32Array(pcmBytes.length / 2);
      for (let i = 0; i < samples.length; i++) {
        const lo = pcmBytes[i * 2];
        const hi = pcmBytes[i * 2 + 1];
        let val = (hi << 8) | lo;
        if (val >= 0x8000) val -= 0x10000;
        samples[i] = val / 32768;
      }

      audioQueue.push(samples);
      playNextChunk(); // Always try to play
    }
  };

  ws.onclose = () => log("WebSocket closed");
  ws.onerror = () => log("WebSocket error");
};

stopBtn.onclick = () => {
  log("Stopping...");

  try {
    if (currentSource) {
      currentSource.stop();
      currentSource = null;
    }
    processor?.disconnect();
    source?.disconnect();
  } catch {}

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.close();
  }

  audioQueue = [];
};

function playNextChunk() {
  // Don't play if already playing
  if (currentSource !== null) {
    return;
  }

  if (audioQueue.length === 0) {
    return;
  }

  const samples = audioQueue.shift();

  const buffer = audioContext.createBuffer(1, samples.length, 24000);
  buffer.getChannelData(0).set(samples);

  const bufferSource = audioContext.createBufferSource();
  bufferSource.buffer = buffer;
  bufferSource.connect(audioContext.destination);

  currentSource = bufferSource;

  bufferSource.onended = () => {
    currentSource = null;
    playNextChunk(); // Play next chunk when this one ends
  };

  bufferSource.start(0);
}
