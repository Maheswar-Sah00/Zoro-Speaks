from fastapi import APIRouter, HTTPException, File, UploadFile
from services.stt_service import transcribe_audio
from services.tts_service import generate_speech
from services.gemini_service import get_agent_response

router = APIRouter()

# Store conversation history per session
chat_store = {}

# Allowed audio types
ALLOWED_AUDIO_TYPES = ["audio/mp3", "audio/webm", "audio/wav", "audio/ogg"]


@router.post("/agent/chat/{session_id}")
async def chat_with_history(session_id: str, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type")

    try:
        # 1️⃣ Read and transcribe audio
        audio_bytes = await file.read()
        transcription = transcribe_audio(audio_bytes)

        # 2️⃣ Save user message to history
        user_message = {"role": "user", "text": transcription}
        chat_store.setdefault(session_id, []).append(user_message)

        # 3️⃣ Get AI response (handles both weather and general queries with character)
        ai_reply = get_agent_response(chat_store[session_id], transcription)
        
        # 4️⃣ Generate speech audio
        audio_url = generate_speech(ai_reply)


        return {
            "audio_url": audio_url,
            "text": ai_reply,
            "history": chat_store[session_id]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
