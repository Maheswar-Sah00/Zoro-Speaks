import assemblyai as aai
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load variables from .env file
load_dotenv()

# Load API key from environment variable
assemblyai_api_key = os.getenv("ASSEMBLYAI_API_KEY") or "4a792c3cad1d40c38b51f210e907a3ee"
if not assemblyai_api_key:
    logger.error("ASSEMBLYAI_API_KEY environment variable not set")
    raise ValueError("ASSEMBLYAI_API_KEY environment variable is required")

aai.settings.api_key = assemblyai_api_key


def transcribe_audio(audio_bytes: bytes) -> str:
    try:
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_bytes)
        if transcript.status == "error":
            logger.error(f"AssemblyAI error: {transcript.error}")
            raise ValueError(f"AssemblyAI error: {transcript.error}")
        return transcript.text
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise
