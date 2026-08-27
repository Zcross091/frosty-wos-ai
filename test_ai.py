import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")

print("--- Testing Gemini ---")
gemini_models = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
for model in gemini_models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
    payload = {
        "contents": [{"parts": [{"text": "Hello, respond with 'Gemini is working perfectly!'"}]}]
    }
    try:
        res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
        print(f"Gemini ({model}) HTTP Status: {res.status_code}")
        if res.status_code == 200:
            print(f"Gemini Success: {res.json()['candidates'][0]['content']['parts'][0]['text']}")
            break
        else:
            print(f"Gemini Response: {res.text[:200]}")
    except Exception as e:
        print(f"Gemini Error ({model}): {e}")

print("\n--- Testing Groq Models List ---")
groq_models_url = "https://api.groq.com/openai/v1/models"
groq_headers = {
    "Authorization": f"Bearer {groq_key}",
    "Content-Type": "application/json"
}
try:
    res = requests.get(groq_models_url, headers=groq_headers, timeout=10)
    print(f"Groq Models HTTP Status: {res.status_code}")
    if res.status_code == 200:
        models_data = res.json().get("data", [])
        active_ids = [m["id"] for m in models_data]
        print(f"Active Groq Models on this account: {active_ids}")
    else:
        print(f"Groq Response: {res.text}")
except Exception as e:
    print(f"Groq Error: {e}")

