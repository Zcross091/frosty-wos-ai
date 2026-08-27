"""
Frosty AI Engine
Multi-provider AI adapter supporting:
1. Google Gemini (Free API from Google AI Studio)
2. Groq (Free fast API from Groq Console)
3. Ollama (Local Small AI Models: llama3.2, qwen2.5, phi3)
4. OpenRouter (Free community AI models)
5. OpenAI
6. Zero-Key Direct Knowledge Synthesizer (Offline RAG fallback when no API key is set)
"""

import os
import time
import json
import logging
import requests
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("FrostyAI.Engine")

# Supported Models
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_FALLBACKS = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-lite-preview-02-05"]

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_FALLBACKS = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama-3.2-3b-preview", "llama-3.2-1b-preview", "qwen-2.5-32b", "deepseek-r1-distill-llama-70b", "gemma2-9b-it"]

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
OPENAI_FALLBACKS = ["gpt-4o-mini", "gpt-4o"]

DEFAULT_OLLAMA_MODEL = "llama3.2:1b"
DEFAULT_OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct:free"


class AIEngine:
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "gemini").lower()
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()

        self.gemini_model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
        self.groq_model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL
        self.openai_model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL
        
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip()
        self.ollama_model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip() or DEFAULT_OLLAMA_MODEL
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL).strip() or DEFAULT_OPENROUTER_MODEL

        # Sanitize known deprecated models
        if "8b-instant" in self.groq_model or "llama-3.1-8b" in self.groq_model:
            self.groq_model = DEFAULT_GROQ_MODEL

        # Auto-detect best available provider
        if not self.gemini_key and not self.groq_key and not self.openai_key and not self.openrouter_key:
            if self.provider not in ["ollama", "local"]:
                # Check if local ollama is running, else use local extractor
                self.provider = "local"

        self._gemini_client = None
        self._gemini_legacy = None
        self._groq_client = None
        self._openai_client = None

        self._init_clients()

    def _init_clients(self):
        # 1. Initialize Gemini
        if self.gemini_key:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=self.gemini_key)
                logger.info("Initialized Google GenAI (modern SDK)")
            except Exception as e:
                try:
                    import google.generativeai as genai_legacy
                    genai_legacy.configure(api_key=self.gemini_key)
                    self._gemini_legacy = genai_legacy
                    logger.info("Initialized Google GenerativeAI (legacy SDK)")
                except Exception as ex:
                    logger.error(f"Failed to initialize Gemini: {ex}")

        # 2. Initialize Groq
        if self.groq_key:
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=self.groq_key)
                logger.info("Initialized Groq client")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")

        # 3. Initialize OpenAI
        if self.openai_key:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=self.openai_key)
                logger.info("Initialized OpenAI client")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

    def get_active_model_name(self) -> str:
        if self.provider == "gemini" and self.gemini_key:
            return f"Gemini ({self.gemini_model})"
        elif self.provider == "groq" and self.groq_key:
            return f"Groq ({self.groq_model})"
        elif self.provider == "ollama":
            return f"Local Ollama ({self.ollama_model})"
        elif self.provider == "openrouter":
            return f"OpenRouter ({self.openrouter_model})"
        elif self.provider == "openai" and self.openai_key:
            return f"OpenAI ({self.openai_model})"
        return "Frosty Local Tactical Core (No API Key Required)"

    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.6
    ) -> Tuple[str, str, float]:
        """
        Generates response using available cloud AI, local Ollama, or built-in Tactical RAG extractor.
        """
        start_time = time.time()
        providers_to_try = [self.provider]

        for p in ["gemini", "groq", "ollama", "openrouter", "openai", "local"]:
            if p not in providers_to_try:
                providers_to_try.append(p)

        last_error = None

        for current_provider in providers_to_try:
            try:
                if current_provider == "gemini" and (self._gemini_client or self._gemini_legacy or self.gemini_key):
                    res, model = self._generate_gemini(system_prompt, user_message, history, temperature)
                    return res, model, time.time() - start_time
                
                elif current_provider == "groq" and (self._groq_client or self.groq_key):
                    res, model = self._generate_groq(system_prompt, user_message, history, temperature)
                    return res, model, time.time() - start_time
                
                elif current_provider == "ollama":
                    res, model = self._generate_ollama(system_prompt, user_message, history)
                    return res, model, time.time() - start_time
                
                elif current_provider == "openrouter" and self.openrouter_key:
                    res, model = self._generate_openrouter(system_prompt, user_message, history, temperature)
                    return res, model, time.time() - start_time
                
                elif current_provider == "openai" and (self._openai_client or self.openai_key):
                    res, model = self._generate_openai(system_prompt, user_message, history, temperature)
                    return res, model, time.time() - start_time
                
                elif current_provider == "local":
                    res, model = self._generate_local_fallback(system_prompt, user_message)
                    return res, model, time.time() - start_time

            except Exception as e:
                last_error = e
                logger.warning(f"Provider {current_provider} failed: {e}. Trying next option...")

        # Ultimate fallback
        res, model = self._generate_local_fallback(system_prompt, user_message)
        return res, model, time.time() - start_time

    def _generate_gemini(
        self, system_prompt: str, user_message: str, history: Optional[List[Dict[str, str]]], temperature: float
    ) -> Tuple[str, str]:
        models_to_test = [self.gemini_model] + [m for m in GEMINI_FALLBACKS if m != self.gemini_model]
        last_ex = None

        for model_name in models_to_test:
            try:
                if self._gemini_client:
                    full_prompt = f"{system_prompt}\n\nUser Question: {user_message}"
                    if history:
                        hist_text = "\n".join([f"{h.get('role', 'user').title()}: {h.get('content', '')}" for h in history[-4:]])
                        full_prompt = f"{system_prompt}\n\nRecent Conversation:\n{hist_text}\n\nUser Question: {user_message}"
                    
                    response = self._gemini_client.models.generate_content(
                        model=model_name,
                        contents=full_prompt,
                    )
                    return response.text, f"Gemini ({model_name})"
                
                elif self._gemini_legacy:
                    model = self._gemini_legacy.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_prompt
                    )
                    response = model.generate_content(user_message)
                    return response.text, f"Gemini ({model_name})"
            except Exception as e:
                last_ex = e

        raise last_ex or RuntimeError("Gemini failed")

    def _generate_groq(
        self, system_prompt: str, user_message: str, history: Optional[List[Dict[str, str]]], temperature: float
    ) -> Tuple[str, str]:
        if not self._groq_client and self.groq_key:
            from groq import Groq
            self._groq_client = Groq(api_key=self.groq_key)

        models_to_test = [self.groq_model] + [m for m in GROQ_FALLBACKS if m != self.groq_model]
        last_ex = None

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for h in history[-4:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        for model_name in models_to_test:
            try:
                completion = self._groq_client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature
                )
                return completion.choices[0].message.content, f"Groq ({model_name})"
            except Exception as e:
                last_ex = e

        raise last_ex or RuntimeError("Groq failed")

    def _generate_ollama(
        self, system_prompt: str, user_message: str, history: Optional[List[Dict[str, str]]]
    ) -> Tuple[str, str]:
        """Runs inference against local Ollama instance (0 cost, 0 API key)."""
        url = f"{self.ollama_host}/api/chat"
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for h in history[-4:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False
        }

        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"], f"Local Ollama ({self.ollama_model})"

    def _generate_openrouter(
        self, system_prompt: str, user_message: str, history: Optional[List[Dict[str, str]]], temperature: float
    ) -> Tuple[str, str]:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "HTTP-Referer": "https://github.com/Zcross091/frosty-wos-ai",
            "X-Title": "Frosty WOS AI"
        }
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for h in history[-4:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.openrouter_model,
            "messages": messages,
            "temperature": temperature
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"], f"OpenRouter ({self.openrouter_model})"

    def _generate_openai(
        self, system_prompt: str, user_message: str, history: Optional[List[Dict[str, str]]], temperature: float
    ) -> Tuple[str, str]:
        if not self._openai_client and self.openai_key:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=self.openai_key)

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for h in history[-4:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        completion = self._openai_client.chat.completions.create(
            model=self.openai_model,
            messages=messages,
            temperature=temperature
        )
        return completion.choices[0].message.content, f"OpenAI ({self.openai_model})"

    def _generate_local_fallback(self, system_prompt: str, user_message: str) -> Tuple[str, str]:
        """
        Zero-API-Key Direct Knowledge Synthesizer:
        Extracts and formats relevant strategy from the knowledge base directly.
        """
        # Parse context from system prompt
        context_split = system_prompt.split("### REFERENCE DATA CONTEXT:")
        context = context_split[1].strip() if len(context_split) > 1 else system_prompt

        # Clean markers
        clean_context = context.replace("=== CORE WHITEOUT SURVIVAL MECHANICS & DOCTRINE ===", "")
        clean_context = clean_context.replace("=== RETRIEVED WOS ARCHIVES & DATA ===", "")
        clean_context = clean_context.strip()

        # Format clean markdown output
        output = (
            f"### 🛡️ Frosty Tactical Advisory\n\n"
            f"{clean_context[:3000]}\n\n"
            f"---\n"
            f"💡 **Chief's Tip:** *This response was served directly from Frosty's local tactical archives.*"
        )
        return output, "Frosty Local Tactical Core"
