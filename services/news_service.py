import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variable
TAVILY_API_KEY = os.getenv("c") or "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"
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY environment variable is required")
TAVILY_ENDPOINT = "https://api.tavily.com/news"  # check Tavily docs for the correct endpoint

def get_real_time_news(topic="general", limit=5):
    """
    Fetches real-time news from Tavily for a given topic.
    Returns formatted news string.
    """
    params = {
        "api_key": TAVILY_API_KEY,
        "topic": topic,
        "limit": limit
    }

    try:
        response = requests.get(TAVILY_ENDPOINT, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors

        news_items = response.json().get("articles", [])
        if not news_items:
            return "No news found for this topic."

        # Format news nicely
        formatted_news = "\n".join([f"{i+1}. {item['title']}" for i, item in enumerate(news_items)])
        return formatted_news

    except requests.RequestException as e:
        return f"Sorry, I couldn't fetch the news at the moment. ({e})"