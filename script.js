const startAndstopBtn = document.getElementById('startAndstopBtn');
const chatLog = document.getElementById('chat-log');
const loadingIndicator = document.getElementById('loading');

let isRecording = false;
let ws = null;
let stream;
let audioCtx;
let source;
let processor;

// audio state
let audioContext;
let playheadTime = 0;

/* ---------------- Session ---------------- */
function getSessionId() {
    const params = new URLSearchParams(window.location.search);
    let id = params.get("session");
    if (!id) {
        id = crypto.randomUUID();
        params.set("session", id);
        window.history.replaceState({}, "", `${location.pathname}?${params}`);
    }
    return id;
}
const sessionId = getSessionId();

/* ---------------- Chat History (localStorage) ---------------- */
function saveChatHistory() {
    const messages = [...chatLog.querySelectorAll(".message")].map(msg => ({
        text: msg.dataset.text || msg.textContent,
        type: msg.classList.contains("sent") ? "sent" : "received"
    }));
    localStorage.setItem("chatHistory", JSON.stringify(messages));
}

function loadChatHistory() {
    const saved = localStorage.getItem("chatHistory");
    if (!saved) return;
    const messages = JSON.parse(saved);
    messages.forEach(m => addTextMessage(m.text, m.type, false)); // don’t double-save
}

function clearChat() {
    chatLog.innerHTML = "";
    localStorage.removeItem("chatHistory");
    addTextMessage("Chat cleared. Start recording to begin again.", "received", false);
}

/* ---------------- Chat UI helpers ---------------- */
function addTextMessage(text, type, save = true) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', type);
    messageDiv.textContent = text;
    messageDiv.dataset.text = text;
    chatLog.appendChild(messageDiv);
    chatLog.scrollTop = chatLog.scrollHeight;

    if (save) saveChatHistory();
}

function addAudioMessage(audioUrl, type) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', type);

    const audioPlayer = document.createElement('audio');
    audioPlayer.controls = true;
    audioPlayer.src = audioUrl;

    messageDiv.appendChild(audioPlayer);
    chatLog.appendChild(messageDiv);

    if (type === 'received') {
        audioPlayer.play();
    }
    chatLog.scrollTop = chatLog.scrollHeight;
    saveChatHistory();
}

/* ---------------- Audio Encoding Helpers ---------------- */
function floatTo16BitPCM(float32Array) {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);
    let offset = 0;
    for (let i = 0; i < float32Array.length; i++, offset += 2) {
        let s = Math.max(-1, Math.min(1, float32Array[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    return buffer;
}

/* ---------------- Real-time playback ---------------- */
function base64ToPCMFloat32(base64) {
    const binary = atob(base64);
    let offset = 0;

    // Skip WAV header if present
    if (binary.length > 44 && binary.slice(0, 4) === "RIFF") {
        offset = 44;
    }

    const length = binary.length - offset;
    const byteArray = new Uint8Array(length);
    for (let i = 0; i < length; i++) {
        byteArray[i] = binary.charCodeAt(i + offset);
    }

    const view = new DataView(byteArray.buffer);
    const sampleCount = byteArray.length / 2;
    const float32Array = new Float32Array(sampleCount);

    for (let i = 0; i < sampleCount; i++) {
        const int16 = view.getInt16(i * 2, true);
        float32Array[i] = int16 / 32768;
    }
    return float32Array;
}

function playAudioChunk(base64Audio) {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 44100 });
        playheadTime = audioContext.currentTime;
    }

    const float32Array = base64ToPCMFloat32(base64Audio);
    if (!float32Array) return;

    const buffer = audioContext.createBuffer(1, float32Array.length, 44100);
    buffer.copyToChannel(float32Array, 0);

    const source = audioContext.createBufferSource();
    source.buffer = buffer;
    source.connect(audioContext.destination);

    const now = audioContext.currentTime;
    if (playheadTime < now + 0.15) {
        playheadTime = now + 0.15;
    }

    source.start(playheadTime);
    playheadTime += buffer.duration;
}

/* ---------------- Recording ---------------- */
async function startRecording() {
    ws = new WebSocket("ws://127.0.0.1:8000/ws");

    ws.onopen = () => console.log("✅ WebSocket connected");
    ws.onclose = () => console.log("❌ WebSocket closed");
    ws.onerror = (err) => console.error("⚠️ WebSocket error", err);

    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);

            if (msg.type === "transcript") {
                console.log(`you: "${msg.text}"`);
                addTextMessage(msg.text, "sent");

            } else if (msg.type === "ai_response") {
                console.log(`voice_agent: "${msg.text}"`);
                addTextMessage(msg.text, "received");

            } else if (msg.type === "audio_chunk") {
                console.log(`🎵 Received audio chunk (${msg.audio ? msg.audio.length : 0} chars)`);
                try {
                    playAudioChunk(msg.audio);
                } catch (err) {
                    console.error('❌ Audio playback error:', err);
                }
            } else {
                console.warn("Unknown message type:", msg);
            }

        } catch (err) {
            console.error("Failed to parse server message", err, event.data);
        }
    };

    stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    audioCtx = new AudioContext({ sampleRate: 16000 });
    source = audioCtx.createMediaStreamSource(stream);
    
    // Use modern AudioWorklet if available, fallback to ScriptProcessor
    if (audioCtx.audioWorklet && window.AudioWorkletNode) {
        try {
            // Note: In a real implementation, you'd need to add the worklet module
            // For now, fallback to ScriptProcessor with a warning
            console.warn('AudioWorklet available but worklet module not loaded, using ScriptProcessor fallback');
            throw new Error('Worklet not loaded');
        } catch {
            // Fallback to ScriptProcessor with deprecation warning
            console.warn('Using deprecated ScriptProcessor API. Consider implementing AudioWorklet for better performance.');
            processor = audioCtx.createScriptProcessor(4096, 1, 1);
            
            source.connect(processor);
            processor.connect(audioCtx.destination);
            
            processor.onaudioprocess = (e) => {
                const inputData = e.inputBuffer.getChannelData(0);
                const pcm16 = floatTo16BitPCM(inputData);
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(pcm16);
                }
            };
        }
    } else {
        // Fallback for older browsers
        console.warn('Using deprecated ScriptProcessor API. Consider implementing AudioWorklet for better performance.');
        processor = audioCtx.createScriptProcessor(4096, 1, 1);
        
        source.connect(processor);
        processor.connect(audioCtx.destination);
        
        processor.onaudioprocess = (e) => {
            const inputData = e.inputBuffer.getChannelData(0);
            const pcm16 = floatTo16BitPCM(inputData);
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(pcm16);
            }
        };
    }
}

function stopRecording() {
    if (processor) {
        processor.disconnect();
        processor.onaudioprocess = null;
    }
    if (source) source.disconnect();
    if (audioCtx) audioCtx.close();

    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    if (ws) ws.close();
}

/* ---------------- Button Actions ---------------- */
startAndstopBtn.addEventListener("click", async (e) => {
    e.preventDefault();

    if (!isRecording) {
        try {
            await startRecording();
            isRecording = true;
            startAndstopBtn.textContent = "Stop Recording";
            startAndstopBtn.classList.add("recording");
        } catch (err) {
            console.error("Mic error", err);
            alert("Microphone access denied.");
        }
    } else {
        stopRecording();
        isRecording = false;
        startAndstopBtn.textContent = "Start Recording";
        startAndstopBtn.classList.remove("recording");
    }
});

/* ---------------- Audio Context Activation ---------------- */
function initAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 44100 });
        playheadTime = audioContext.currentTime;
        console.log('🔊 Audio context initialized');
    }
    if (audioContext.state === 'suspended') {
        audioContext.resume().then(() => {
            console.log('🔊 Audio context resumed');
        });
    }
}

/* ---------------- Init ---------------- */
window.addEventListener("DOMContentLoaded", () => {
    loadChatHistory();

    // Add Clear Chat button dynamically
    const clearBtn = document.createElement("button");
    clearBtn.textContent = "Clear Chat";
    clearBtn.classList.add("clear-btn");
    clearBtn.addEventListener("click", clearChat);
    document.querySelector(".controls").appendChild(clearBtn);
    
    // Add Audio Enable button
    const audioBtn = document.createElement("button");
    audioBtn.textContent = "Enable Audio";
    audioBtn.classList.add("audio-enable-btn");
    audioBtn.addEventListener("click", initAudioContext);
    document.querySelector(".controls").appendChild(audioBtn);
    
    // Initialize audio context on any user interaction
    document.addEventListener('click', initAudioContext, { once: true });
});
// your existing script.js code stays above ↓

// Sidebar toggle
const configToggle = document.getElementById('configToggle');
const configSidebar = document.getElementById('configSidebar');
const closeSidebar = document.getElementById('closeSidebar');
const saveKeysBtn = document.getElementById('saveKeysBtn');

configToggle.addEventListener('click', () => {
  configSidebar.classList.add('open');
});

closeSidebar.addEventListener('click', () => {
  configSidebar.classList.remove('open');
});

// Save keys to localStorage
saveKeysBtn.addEventListener('click', () => {
  const keys = {
    murf: document.getElementById('murfKey').value,
    assembly: document.getElementById('assemblyKey').value,
    gemini: document.getElementById('geminiKey').value,
    news: document.getElementById('newsKey').value,
    weather: document.getElementById('weatherKey').value,
  };
  localStorage.setItem('apiKeys', JSON.stringify(keys));
  alert('✅ API Keys saved!');
  configSidebar.classList.remove('open');
});

// Load saved keys on startup
window.addEventListener("DOMContentLoaded", () => {
  loadChatHistory();

  const savedKeys = JSON.parse(localStorage.getItem('apiKeys') || '{}');
  if (savedKeys.murf) document.getElementById('murfKey').value = savedKeys.murf;
  if (savedKeys.assembly) document.getElementById('assemblyKey').value = savedKeys.assembly;
  if (savedKeys.gemini) document.getElementById('geminiKey').value = savedKeys.gemini;
  if (savedKeys.news) document.getElementById('newsKey').value = savedKeys.news;
  if (savedKeys.weather) document.getElementById('weatherKey').value = savedKeys.weather;
});
