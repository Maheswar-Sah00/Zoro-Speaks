import os
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from Routes import agent_chat
from utils.logging import setup_logger
from Routes.transcriber import AssemblyAIStreamingTranscriber

# Load environment variables from .env file
load_dotenv()

setup_logger()

app = FastAPI()

OUTPUT_DIR = os.path.join("Agent", "Output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.get("/")
def get_homepage():
    return FileResponse("index.html", media_type="text/html")


@app.get("/style.css")
def get_style():
    return FileResponse("style.css", media_type="text/css")


@app.get("/script.js")
def get_script():
    return FileResponse("script.js", media_type="application/javascript")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    transcriber = None
    try:
        await websocket.accept()
        print("🎤 Client connected")

        loop = asyncio.get_running_loop()
        transcriber = AssemblyAIStreamingTranscriber(
            websocket, loop, sample_rate=16000)

        while True:
            try:
                # Add timeout to prevent hanging indefinitely
                data = await asyncio.wait_for(websocket.receive_bytes(), timeout=60.0)
                if data:
                    transcriber.stream_audio(data)
                else:
                    print("⚠️ Received empty audio data")
                    
            except asyncio.TimeoutError:
                print("⚠️ WebSocket receive timeout - connection may be idle")
                # Send ping to check connection
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    print("⚠️ Ping failed, connection lost")
                    break
            except asyncio.CancelledError:
                print("⚠️ WebSocket task was cancelled")
                break
            except Exception as e:
                print(f"⚠️ Error processing audio data: {e}")
                break

    except Exception as e:
        print(f"⚠️ WebSocket connection error: {e}")
        
    finally:
        if transcriber:
            try:
                transcriber.close()
            except Exception as e:
                print(f"⚠️ Error closing transcriber: {e}")
        
        # Clean close
        if websocket.client_state.name != "DISCONNECTED":
            try:
                await websocket.close(code=1000)
            except:
                pass
        
        print("🔌 Client disconnected")


# Include API routes
app.include_router(agent_chat.router)