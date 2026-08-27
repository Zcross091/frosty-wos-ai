import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")

print("--- Testing Gemini ---")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
payload = {
    "contents": [{"parts": [{"text": "Hello, respond with 'Gemini is working'"}]}]
}
try:
    res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
    print(f"Gemini HTTP Status: {res.status_code}")
    print(f"Gemini Response: {res.text[:300]}")
except Exception as e:
    print(f"Gemini Error: {e}")

print("\n--- Testing Groq ---")
groq_url = "https://api.groq.com/openai/v1/chat/completions"
groq_payload = {
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "Hello, respond with 'Groq is working'"}],
    "temperature": 0.5
}
groq_headers = {
    "Authorization": f"Bearer {groq_key}",
    "Content-Type": "application/json"
}
try:
    res = requests.post(groq_url, json=groq_payload, headers=groq_headers, timeout=10)
    print(f"Groq HTTP Status: {res.status_code}")
    print(f"Groq Response: {res.text[:300]}")
except Exception as e:
    print(f"Groq Error: {e}")
