"""
Frosty AI Engine
Multi-provider AI adapter supporting Google Gemini, Groq, and OpenAI with automated failover.
"""

import os
import time
import logging
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("FrostyAI.Engine")

# Supported Models
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_FALLBACKS = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_FALLBACKS = ["llama-3.3-70b-versatile", "deepseek-r1-distill-llama-70b", "mixtral-8x7b-32768", "llama3-70b-8192"]

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
OPENAI_FALLBACKS = ["gpt-4o-mini", "gpt-4o"]


class AIEngine:
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "gemini").lower()
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()

        self.gemini_model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
        self.groq_model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL
        self.openai_model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL

        # Sanitize known deprecated models automatically
        if "8b-instant" in self.groq_model or "llama-3.1-8b" in self.groq_model:
            logger.warning(f"Deprecated model {self.groq_model} detected; switching to {DEFAULT_GROQ_MODEL}")
            self.groq_model = DEFAULT_GROQ_MODEL

        # Auto-detect best provider if current has no key
        if self.provider == "gemini" and not self.gemini_key:
            if self.groq_key:
                self.provider = "groq"
            elif self.openai_key:
                self.provider = "openai"
        elif self.provider == "groq" and not self.groq_key:
            if self.gemini_key:
                self.provider = "gemini"
            elif self.openai_key:
                self.provider = "openai"

        # Initialize clients
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
                logger.debug(f"Modern google-genai init failed, trying legacy: {e}")
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
        if self.provider == "gemini":
            return f"Gemini ({self.gemini_model})"
        elif self.provider == "groq":
            return f"Groq ({self.groq_model})"
        elif self.provider == "openai":
            return f"OpenAI ({self.openai_model})"
        return "Unknown Provider"

    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.6
    ) -> Tuple[str, str, float]:
        """
        Generates an AI response.
        Returns: (response_text, model_used, elapsed_seconds)
        """
        start_time = time.time()
        providers_to_try = [self.provider]
        
        # Add fallback providers
        for p in ["gemini", "groq", "openai"]:
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
                elif current_provider == "openai" and (self._openai_client or self.openai_key):
                    res, model = self._generate_openai(system_prompt, user_message, history, temperature)
                    return res, model, time.time() - start_time
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {current_provider} failed: {e}. Attempting next provider...")

        # If everything failed:
        error_msg = (
            f"⚠️ **Frosty Tactical Core Error**: Unable to reach AI provider.\n"
            f"Details: `{str(last_error)}`\n\n"
            f"💡 *Tip: Check your API keys and model configuration in `.env`.*"
        )
        return error_msg, "Error", time.time() - start_time

    def _generate_gemini(
        self, system_prompt: str, user_message: str, history: Optional[List[Dict[str, str]]], temperature: float
    ) -> Tuple[str, str]:
        models_to_test = [self.gemini_model] + [m for m in GEMINI_FALLBACKS if m != self.gemini_model]
        last_ex = None

        for model_name in models_to_test:
            try:
                if self._gemini_client:
                    # Modern google-genai SDK
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
                    # Legacy google.generativeai
                    model = self._gemini_legacy.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_prompt
                    )
                    chat_history = []
                    if history:
                        for h in history[-4:]:
                            role = "user" if h.get("role") == "user" else "model"
                            chat_history.append({"role": role, "parts": [h.get("content", "")]})
                    
                    if chat_history:
                        chat = model.start_chat(history=chat_history)
                        response = chat.send_message(user_message)
                    else:
                        response = model.generate_content(user_message)
                    return response.text, f"Gemini ({model_name})"
            except Exception as e:
                last_ex = e
                logger.warning(f"Gemini model {model_name} failed: {e}")

        raise last_ex or RuntimeError("Gemini failed with all fallback models")

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
                logger.warning(f"Groq model {model_name} failed: {e}")

        raise last_ex or RuntimeError("Groq failed with all fallback models")

    def _generate_openai(
        self, system_prompt: str, user_message: str, history: Optional[List[Dict[str, str]]], temperature: float
    ) -> Tuple[str, str]:
        if not self._openai_client and self.openai_key:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=self.openai_key)

        models_to_test = [self.openai_model] + [m for m in OPENAI_FALLBACKS if m != self.openai_model]
        last_ex = None

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for h in history[-4:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        for model_name in models_to_test:
            try:
                completion = self._openai_client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature
                )
                return completion.choices[0].message.content, f"OpenAI ({model_name})"
            except Exception as e:
                last_ex = e
                logger.warning(f"OpenAI model {model_name} failed: {e}")

        raise last_ex or RuntimeError("OpenAI failed with all fallback models")
