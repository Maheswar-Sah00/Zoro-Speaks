import requests
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def generate_speech(text: str, voice_id: str = "en-US-ken") -> str:
    murf_api_key = os.getenv("MURF_API_KEY") or "ap2_429c402a-ce5e-4a95-b090-49ef79dc7727"
    if not murf_api_key:
        logger.error("MURF_API_KEY environment variable not set")
        raise ValueError("MURF_API_KEY environment variable is required")
        
    response = requests.post(
        "https://api.murf.ai/v1/speech/generate",
        headers={
            "api-key": murf_api_key,
            "Content-Type": "application/json"
        },
        json={
            "text": text,
            "voiceId": voice_id
        }
    )
    if response.status_code != 200:
        logger.error(f"Murf API failed: {response.text}")
        raise ValueError(f"Murf API failed: {response.text}")
    return response.json().get("audioFile")

