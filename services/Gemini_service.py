import google.generativeai as genai
import os
import logging
import re
from dotenv import load_dotenv
from .weather import get_weather

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# --- Zoro Persona Prompt ---
ZORO_PERSONA = """
You are Roronoa Zoro from One Piece. 
- Speak bluntly and directly, like a swordsman. 
- Show loyalty to your crew but act tough. 
- Occasionally reference swords, training, or getting lost. 
- Tone: stoic, confident, sometimes sarcastic. 
- Never break character.
"""


def get_response_from_gemini(conversation_history: list) -> str:
    try:
        # Configure API key
        my_api_key = os.getenv("GEMINI_API_KEY") or "AIzaSyAto87Z_MLCfW-67KaVAAO373dmDvuGSUY"
        if not my_api_key:
            logger.error("GEMINI_API_KEY environment variable not set")
            raise ValueError("GEMINI_API_KEY environment variable is required")
        genai.configure(api_key=my_api_key)
        
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Insert Zoro persona as the first "system" message
        messages = [{"role": "user", "parts": [ZORO_PERSONA]}]

        # Convert conversation history into Gemini format
        for msg in conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            messages.append({"role": role, "parts": [msg["text"]]})

        # Generate response
        response = model.generate_content(messages)
        return response.text.strip()

    except Exception as e:
        error_str = str(e)
        logger.error(f"Gemini error: {e}")
        
        # Handle specific error types
        if "429" in error_str or "quota" in error_str.lower():
            return "Tch. Looks like I've used up my daily energy. The Gemini API quota is maxed out. Try again tomorrow, or get the crew to upgrade the API plan."
        elif "401" in error_str or "unauthorized" in error_str.lower():
            return "Oi! The API key seems to be invalid. Someone needs to check the credentials."
        else:
            return "Sorry, I couldn't process that."


def detect_weather_query(text: str) -> str:
    """
    Detects if user is asking about weather and extracts city name.
    Returns city name if weather query detected, None otherwise.
    """
    weather_keywords = ['weather', 'temperature', 'temp', 'hot', 'cold', 'rain', 'sunny', 'cloudy', 'forecast']
    text_lower = text.lower()
    
    # Check if any weather keywords are present
    if not any(keyword in text_lower for keyword in weather_keywords):
        return None
    
    # Common city extraction patterns
    city_patterns = [
        r'weather in ([a-zA-Z\s]+)',
        r'temperature in ([a-zA-Z\s]+)',
        r'how.*(?:hot|cold|warm).*in ([a-zA-Z\s]+)',
        r'what.*weather.*([a-zA-Z\s]+)',
        r'forecast.*([a-zA-Z\s]+)'
    ]
    
    for pattern in city_patterns:
        match = re.search(pattern, text_lower)
        if match:
            city = match.group(1).strip()
            # Remove common words that aren't cities
            city = re.sub(r'\b(the|is|like|for|today|tomorrow)\b', '', city).strip()
            if city and len(city) > 1:
                return city
    
    # If no city found but weather query detected, default to Tokyo
    return "Tokyo"


def get_agent_response(conversation_history: list, user_input: str = "") -> str:
    """
    Main function used by agent_chat.py to get AI response.
    Enhanced with weather detection and real data integration.
    """
    try:
        # Get the current query text
        query_text = user_input
        if not query_text and conversation_history:
            # Get the last user message if user_input is not provided
            for msg in reversed(conversation_history):
                if msg["role"] == "user":
                    query_text = msg["text"]
                    break
        
        # Always check the current query for weather detection
        city = detect_weather_query(query_text) if query_text else None
        
        if city:
            # Get real weather data
            logger.info(f"Weather query detected for city: {city}")
            weather_info = get_weather(city)
            
            # Enhanced Zoro persona that incorporates weather data
            weather_persona = f"""
You are Roronoa Zoro from One Piece.
- Speak bluntly and directly, like a swordsman.
- Show loyalty to your crew but act tough.
- Occasionally reference swords, training, or getting lost.
- Tone: stoic, confident, sometimes sarcastic.
- Never break character.

The user asked about weather. Here's the actual weather data: {weather_info}

Respond with the weather information but stay in character as Zoro. 
You can be dismissive about caring about weather while still providing the info.
Keep your response concise and in Zoro's speaking style.
"""
            
            # Configure API key
            my_api_key = os.getenv("GEMINI_API_KEY")
            if not my_api_key:
                logger.error("GEMINI_API_KEY environment variable not set")
                raise ValueError("GEMINI_API_KEY environment variable is required")
            genai.configure(api_key=my_api_key)
            
            model = genai.GenerativeModel("gemini-1.5-flash")
            messages = [{"role": "user", "parts": [weather_persona]}]
            
            # Add the specific weather question
            messages.append({"role": "user", "parts": [query_text]})
            
            response = model.generate_content(messages)
            
            # Save the AI response to conversation history
            if conversation_history:
                conversation_history.append({"role": "assistant", "text": response.text.strip()})
            
            return response.text.strip()
        
        else:
            # Normal conversation without weather
            response = get_response_from_gemini(conversation_history)
            
            # Save the AI response to conversation history
            if conversation_history:
                conversation_history.append({"role": "assistant", "text": response})
            
            return response
            
    except Exception as e:
        error_str = str(e)
        logger.error(f"Agent response error: {e}")
        
        # Handle specific error types
        if "429" in error_str or "quota" in error_str.lower():
            return "Tch. Looks like I've used up my daily energy. The Gemini API quota is maxed out. Try again tomorrow, or get the crew to upgrade the API plan."
        elif "401" in error_str or "unauthorized" in error_str.lower():
            return "Oi! The API key seems to be invalid. Someone needs to check the credentials."
        else:
            return "Tch. Something went wrong with my response. Try asking again."


