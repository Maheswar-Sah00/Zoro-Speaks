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
` Zoro-speaks
│
├─ Routes
│ ├─ agent_chat.py
│ ├─ config.py
│ └─ transcriber.py
│
├─ services
│ ├─ streamer.py
│ ├─ stt_services.py
│ ├─ tts_services.py
│ ├─ gemini_services.py
│ ├─ weather.py
│ └─ news_services.py
│
├─ utils
│ └─ logging.py
│
├─ index.html
├─ main.py
├─ style.css
└─ script.js
`

