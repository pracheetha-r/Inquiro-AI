import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

try:
    client = genai.Client(api_key=api_key)
    for m in client.models.list():
        print(m.name)
except Exception as e:
    print(f"Exception: {e}")
