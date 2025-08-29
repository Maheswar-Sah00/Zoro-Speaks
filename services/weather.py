import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenWeatherMap API
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY") or "f721dea50cfd26239e04c648291ecd30"
WEATHER_ENDPOINT = "http://api.openweathermap.org/data/2.5/weather"

def get_weather(city: str = "London"):
    print(f"🌤️ get_weather() called with city={city}")
    """
    Fetches real-time weather for the specified city.
    """
    if not WEATHER_API_KEY:
        return f"Weather service is not configured. Please check the API key configuration."
    
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(WEATHER_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()

        weather_desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]

        return (f"Weather in {city.title()}: {weather_desc}, "
                f"temperature {temp}°C (feels like {feels_like}°C), "
                f"humidity {humidity}%.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return f"Weather service API key is invalid or expired. Please update your WEATHER_API_KEY."
        elif e.response.status_code == 404:
            return f"City '{city}' not found. Please check the city name."
        else:
            return f"Weather service error: {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Network error while fetching weather: {e}"
    except KeyError as e:
        return f"Unexpected weather data format: {e}"
    except Exception as e:
        return f"Sorry, I couldn't fetch the weather right now. Error: {e}"
