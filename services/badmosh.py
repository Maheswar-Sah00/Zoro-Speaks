import asyncio
import websockets
import json
import os
import time
from fastapi import WebSocket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MURF_WS_URL = "wss://api.murf.ai/v1/speech/stream-input"


class MurfStreamer:
    def __init__(self, voice_id="en-US-carter", context_id="static-context-123"):
        self.voice_id = voice_id
        self.context_id = context_id
        # Get API key during initialization
        self.murf_api_key = os.getenv("MURF_API_KEY") or "ap2_429c402a-ce5e-4a95-b090-49ef79dc7727"
        if not self.murf_api_key:
            raise ValueError("MURF_API_KEY environment variable is required")
        
        # Add semaphore to limit concurrent connections
        self._connection_semaphore = asyncio.Semaphore(1)  # Only 1 concurrent TTS at a time
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Minimum 1 second between requests

    async def stream_tts(self, text: str, websocket: WebSocket, final=False):
        """Create a new WebSocket connection for each TTS request to avoid concurrency issues"""
        # Use semaphore to limit concurrent connections
        async with self._connection_semaphore:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < self._min_request_interval:
                sleep_time = self._min_request_interval - time_since_last
                print(f"🕰️ Rate limiting: sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
            
            self._last_request_time = time.time()
            
            murf_ws = None
            max_retries = 3
            retry_count = 0
            
            # Connection retry loop
            while retry_count < max_retries:
                try:
                    # Create a new WebSocket connection for this TTS request
                    print(f"🔌 Connecting to Murf WebSocket (attempt {retry_count + 1})...")
                    murf_ws = await asyncio.wait_for(
                        websockets.connect(
                            f"{MURF_WS_URL}?api-key={self.murf_api_key}&sample_rate=44100&channel_type=MONO&format=WAV&context_id={self.context_id}",
                            ping_interval=20,
                            ping_timeout=20,
                            close_timeout=10
                        ),
                        timeout=10.0
                    )
                    break  # Connection successful
                except (asyncio.TimeoutError, websockets.exceptions.WebSocketException) as e:
                    retry_count += 1
                    print(f"⚠️ Murf connection failed (attempt {retry_count}): {e}")
                    if retry_count >= max_retries:
                        print("❌ Max retries reached, giving up on Murf connection")
                        return
                    await asyncio.sleep(1.0)  # Wait before retry
            
            # TTS streaming logic
            try:
                # Send voice configuration
                voice_config_msg = {
                    "voice_config": {
                        "voiceId": self.voice_id,
                        "rate": 0,
                        "pitch": 0,
                        "variation": 1,
                        "style": "Conversational",
                    }
                }
                await murf_ws.send(json.dumps(voice_config_msg))
                print("✅ Voice config sent to Murf")

                # Send text chunk
                text_msg = {
                    "text": text,
                    "end": True  # Always end each request to get complete audio
                }
                await murf_ws.send(json.dumps(text_msg))
                print(f"📨 Sent text to Murf: {text[:50]}{'...' if len(text) > 50 else ''}")

                # Read responses until final with timeout
                timeout_count = 0
                max_timeouts = 10
                
                while True:
                    try:
                        # Add timeout to prevent hanging
                        response = await asyncio.wait_for(murf_ws.recv(), timeout=5.0)
                        data = json.loads(response)
                        timeout_count = 0  # Reset timeout counter on successful receive

                        if "audio" in data:
                            print(f"🎶 Received audio chunk (len={len(data['audio'])})")
                            try:
                                # Check if client websocket is still connected
                                if websocket.client_state.name != "DISCONNECTED":
                                    await websocket.send_json({
                                        "type": "audio_chunk",
                                        "audio": data["audio"]
                                    })
                                else:
                                    print("⚠️ Client disconnected, stopping audio stream")
                                    break
                            except Exception as e:
                                print(f"⚠️ Failed to send audio to client: {e}")
                                break

                        if data.get("final"):
                            print("🏁 Murf marked response as final")
                            break
                            
                    except asyncio.TimeoutError:
                        timeout_count += 1
                        print(f"⚠️ Murf response timeout ({timeout_count}/{max_timeouts})")
                        if timeout_count >= max_timeouts:
                            print("❌ Max timeouts reached, ending stream")
                            break
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        print("⚠️ Murf WebSocket connection closed")
                        break
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Failed to parse Murf response: {e}")
                        break
                    except Exception as e:
                        print(f"⚠️ Error in TTS streaming: {e}")
                        break
                        
            except Exception as e:
                print(f"⚠️ Error in stream_tts: {e}")
            finally:
                # Always close the WebSocket connection
                if murf_ws:
                    try:
                        await murf_ws.close()
                        print("🔒 Murf WebSocket closed")
                    except:
                        pass


