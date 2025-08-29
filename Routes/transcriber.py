import time
import google.generativeai as genai
import asyncio
import assemblyai as aai
from services.badmosh import MurfStreamer
from services.gemini_service import get_agent_response

from assemblyai.streaming.v3 import (
    StreamingClient, StreamingClientOptions,
    StreamingParameters, StreamingSessionParameters,
    StreamingEvents, BeginEvent, TurnEvent,
    TerminationEvent, StreamingError
)
from fastapi import WebSocket


import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY") or "4a792c3cad1d40c38b51f210e907a3ee"
genai.configure(api_key=os.getenv("GEMINI_API_KEY")) or "AIzaSyAto87Z_MLCfW-67KaVAAO373dmDvuGSUY"
gemini_model = genai.GenerativeModel("gemini-1.5-flash")


class AssemblyAIStreamingTranscriber:
    def __init__(self, websocket: WebSocket, loop, sample_rate=16000):
        self.murf = MurfStreamer()
        self.websocket = websocket
        self.loop = loop

        self.client = StreamingClient(
            StreamingClientOptions(
                api_key=aai.settings.api_key,
                api_host="streaming.assemblyai.com"
            )
        )

        self.client.on(StreamingEvents.Begin, self.on_begin)
        self.client.on(StreamingEvents.Turn, self.on_turn)
        self.client.on(StreamingEvents.Termination, self.on_termination)
        self.client.on(StreamingEvents.Error, self.on_error)

    
        self.client.connect(
            StreamingParameters(sample_rate=sample_rate, format_turns=True)
        )

    def on_begin(self, client, event: BeginEvent):
        print(f"🎤 Session started: {event.id}")

    def on_turn(self, client, event: TurnEvent):
        """
        Fire Gemini/Murf ONLY when the turn is formatted (clean sentence),
        and it's the end of user turn.
        """
        print(
            f"{event.transcript} (end_of_turn={event.end_of_turn}, formatted={event.turn_is_formatted})")

        if not event.end_of_turn:
            return

        # If this end-of-turn isn't formatted, request formatting and wait
        if not event.turn_is_formatted:
            client.set_params(StreamingSessionParameters(format_turns=True))
            return

        # Now we have a formatted sentence ayyoooo send to UI and trigger AI response + TTS
        text = (event.transcript or "").strip()
        if not text:
            return

        try:
            # Send transcript to UI
            future = asyncio.run_coroutine_threadsafe(
                self.websocket.send_json({"type": "transcript", "text": text}),
                self.loop
            )
            # Don't wait for result to prevent blocking
            
            # Start streaming AI response in background
            asyncio.run_coroutine_threadsafe(
                self._handle_ai_response(text),
                self.loop
            )
        except Exception as e:
            print("⚠️ Failed in on_turn:", e)

    async def _handle_ai_response(self, user_text: str):
        """
        Async method to handle AI response and TTS streaming without blocking.
        """
        try:
            # Check if WebSocket is still connected
            if self.websocket.client_state.name == "DISCONNECTED":
                print("⚠️ Client disconnected, skipping AI response")
                return
            
            # Use the weather-aware service to get the complete response
            conversation_history = [{"role": "user", "text": user_text}]
            ai_response = get_agent_response(conversation_history, user_text)
            
            # Send the AI response to the UI
            await self.websocket.send_json({
                "type": "ai_response", 
                "text": ai_response
            })
            print(f"✅ AI response sent: {ai_response[:100]}{'...' if len(ai_response) > 100 else ''}")
            
            # Stream TTS audio
            await self.murf.stream_tts(ai_response, self.websocket)
            print("✅ TTS streaming completed")
            
        except asyncio.CancelledError:
            print("⚠️ AI response task was cancelled")
        except Exception as e:
            print(f"⚠️ AI response error: {e}")


    def on_termination(self, client, event: TerminationEvent):
        print(f"🛑 Session terminated after {event.audio_duration_seconds} s")

    def on_error(self, client, error: StreamingError):
        print("❌ Error:", error)

    def stream_audio(self, audio_chunk: bytes):
        self.client.stream(audio_chunk)

    def close(self):
        self.client.disconnect(terminate=True)