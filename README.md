# [🎙️ AI Voice Agent (Realtime)]((https://github.com/Maheswar-Sah00/Zoro-Speaks))
[![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![WebSockets](https://img.shields.io/badge/-WebSockets-000000?style=flat-square&logo=websocket&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
[![AssemblyAI](https://img.shields.io/badge/-AssemblyAI-000000?style=flat-square&logo=assemblyai&logoColor=white)](https://www.assemblyai.com/)
[![Gemini](https://img.shields.io/badge/-Gemini-6CC24A?style=flat-square)](https://developers.google.com/)

---

## 📌 Project Overview

The **AI Voice Agent (Realtime)** is a full-stack application for seamless real-time voice interaction. Users speak, and the system:

1. Records your voice.
2. Transcribes it to text using **AssemblyAI**.
3. Sends the text to an LLM (**Gemini**) to generate a response.
4. Converts the response back to speech with **Murf TTS**.

Built with **FastAPI** and **WebSockets**, this project integrates multiple AI APIs to provide a smooth, interactive conversational experience.

---

## 🚀 Features

- 🎤 **Voice Input** → Records audio in real-time.  
- 📝 **Speech-to-Text (STT)** → Powered by [AssemblyAI](https://www.assemblyai.com/) for transcription.  
- 🧠 **AI Reasoning** → Queries handled by [Google Gemini](https://developers.google.com/) LLM.  
- 🔊 **Text-to-Speech (TTS)** → Responses converted to speech via [Murf AI](https://murf.ai/).  
- 🌍 **Weather updates** → Get real-time weather information for any city using [OpenWeatherMap](https://openweathermap.org/).   
- 📂 **news updates** → Fetch latest news by topic using [Tavily](https://tavily.com/).
- ⚡ **FastAPI + WebSockets** → Enables real-time communication between client and server.  

---

## 📂 Project Structure
```
Zoro-Speaks/
├── Routes/
│   ├── agent_chat.py
│   ├── transcriber.py
│   └── config.py
├── Services/
│   ├── gemini_services.py
│   ├── tts_services.py
│   ├── stt_services.py
│   ├── streamer.py
│   ├── weather.py
│   └── news_services.py
├── Utils/
│   └── logging.py
├── index.html
├── main.py
├── script.js
└── style.css
```
## ⚙️ Setup & Installation
---
### 1️⃣ Clone the Repository
```
git clone https://github.com/Maheswar-Sah00/Zoro-Speaks.git
cd Zoro-Speaks
```

### 2️⃣ Create a Virtual Environment
` python -m venv venv `
Activate it:
- windows
  `venv\Scripts\activate`
- Mac/Linux
  `source venv/bin/activate`

### 3️⃣ Install Dependencies
`pip install -r requirements.txt`

### 4️⃣ Configure Environment Variables
Create a  `.env` file with your API keys:
```
ASSEMBLYAI_API_KEY=your_assemblyai_api_key
GEMINI_API_KEY=your_gemini_api_key
MURF_API_KEY=your_murf_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
TAVILY_API_KEY=your_tavily_api_key
```

### 5️⃣ Run the Server
`uvicorn main:app --reload`
- Server runs at: http://127.0.0.1:8000
- Open `index.html` in your browser to test the app.
  
### 6️⃣ Optional: Install Frontend Dependencies
If your JS frontend needs `npm` packages:
```
npm install
npm run dev
```

