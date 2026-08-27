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
            # 1. Try Direct HTTP REST API (Fastest & most reliable across all key formats)
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_key}"
                full_text = f"{system_prompt}\n\nUser Question: {user_message}"
                payload = {
                    "contents": [{"parts": [{"text": full_text}]}],
                    "generationConfig": {"temperature": temperature}
                }
                res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            return parts[0]["text"], f"Gemini ({model_name})"
                else:
                    logger.debug(f"Gemini REST returned status {res.status_code}: {res.text}")
            except Exception as e:
                logger.debug(f"Gemini REST error ({model_name}): {e}")

            # 2. Try SDKs
            try:
                if self._gemini_client:
                    full_prompt = f"{system_prompt}\n\nUser Question: {user_message}"
                    response = self._gemini_client.models.generate_content(
                        model=model_name,
                        contents=full_prompt,
                    )
                    return response.text, f"Gemini ({model_name})"
                
                elif self._gemini_legacy:
                    model = self._gemini_legacy.GenerativeModel(model_name=model_name)
                    response = model.generate_content(f"{system_prompt}\n\n{user_message}")
                    return response.text, f"Gemini ({model_name})"
            except Exception as e:
                last_ex = e

        raise last_ex or RuntimeError("Gemini REST and SDK both failed")

    def _generate_groq(
        self, system_prompt: str, user_message: str, history: Optional[List[Dict[str, str]]], temperature: float
    ) -> Tuple[str, str]:
        models_to_test = [self.groq_model] + [m for m in GROQ_FALLBACKS if m != self.groq_model]
        last_ex = None

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for h in history[-4:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        for model_name in models_to_test:
            # 1. Try Direct REST
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature
                }
                res = requests.post(url, headers=headers, json=payload, timeout=25)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"], f"Groq ({model_name})"
                else:
                    logger.debug(f"Groq REST returned {res.status_code}: {res.text}")
            except Exception as e:
                logger.debug(f"Groq REST error ({model_name}): {e}")

            # 2. Try SDK
            try:
                if self._groq_client:
                    completion = self._groq_client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=temperature
                    )
                    return completion.choices[0].message.content, f"Groq ({model_name})"
            except Exception as e:
                last_ex = e

        raise last_ex or RuntimeError("Groq failed with all models")

    def _generate_ollama(
        self, system_prompt: str, user_message: str, history: Optional[List[Dict[str, str]]]
    ) -> Tuple[str, str]:
        """Runs inference against local Ollama instance with 15s timeout."""
        url = f"{self.ollama_host}/api/chat"
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for h in history[-4:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": 300, "temperature": 0.6}
        }

        response = requests.post(url, json=payload, timeout=18)
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"], f"Local Ollama ({self.ollama_model})"

    def _generate_local_fallback(self, system_prompt: str, user_message: str) -> Tuple[str, str]:
        """
        Smart Offline Tactical Synthesizer:
        Generates beautifully structured Whiteout Survival guidance directly from local archives.
        """
        q = user_message.lower()

        # 1. Lineup / Formation query
        if any(w in q for w in ["lineup", "formation", "ratio", "troops", "frontline", "deputy", "squad"]):
            output = (
                "### ⚔️ Tactical Doctrine: Hero Lineups & Troop Formations\n\n"
                "In **Whiteout Survival**, every march squad is composed of **3 Hero Slots** and **3 Troop Types**:\n\n"
                "**1. Hero Squad Structure (1 Leader + 2 Deputies):**\n"
                "• **Leader (Captain):** Position 1. Determines march capacity, main skill triggers, and rally leadership.\n"
                "• **Deputies (Left & Right):** Positions 2 & 3. Provide secondary combat stat bonuses and support.\n\n"
                "**2. The 3 Troop Roles:**\n"
                "• 🛡️ **Infantry (Frontline Shield):** Absorbs all incoming enemy damage. If your infantry dies, your backline falls immediately.\n"
                "• 🐎 **Lancers (Flankers / Mid-range):** Target backline marksmen and deal balanced burst DPS.\n"
                "• 🏹 **Marksmen / Sharpshooters (Backline High DPS):** Deliver massive sustained damage from safety.\n\n"
                "**3. Standard Tactical Troop Ratios:**\n"
                "• **Standard PvP / Field Battle:** `50% Infantry / 20% Lancer / 30% Marksman` (`50/20/30`)\n"
                "• **Heavy Defense / Castle Garrison:** `60% Infantry / 20% Lancer / 20% Marksman` (`60/20/20`)\n"
                "• **High Burst Attack / 4-1-1:** `40% Infantry / 10% Lancer / 50% Marksman` (`40/10/50`)\n"
                "• **Bear Trap (Max PvE Damage):** `10% Infantry / 10% Lancer / 80% Marksman` (`10/10/80`)\n\n"
                "---\n"
                "💡 **Grandmaster Tip:** *Always ensure your Infantry ratio is at least 40-50% in PvP so your Marksmen survive to deal full damage!*"
            )
            return output, "Frosty Local Tactical Core"

        # 2. Bear Trap query
        elif "bear" in q:
            output = (
                "### 🐻 Bear Trap Master Guide\n\n"
                "**1. Optimal Troop Ratio:**\n"
                "• Use `10% Infantry / 10% Lancer / 80% Marksman` (or `0/20/80`). The Bear does not kill troops, so maximize Marksmen DPS!\n\n"
                "**2. Critical Rally Joiner Rule (Top 4 Buffs):**\n"
                "• When joining alliance rallies, **always send Jessie as your 1st Hero** (gives +25% Damage Dealt buff to the entire rally!).\n"
                "• Other great joiner leads: **Seo-yoon** (+20% Attack) or **Jeronimo** (+15% Attack/Damage).\n\n"
                "**3. Rally Leader Setup:**\n"
                "• Your Rally Leader march should use your strongest Marksman/Lancer damage heroes (e.g. Flint/Alonso/Mia/Lynn/Wayne/Bradley).\n\n"
                "---\n"
                "💡 **Chief's Tip:** *Keep march times short (<15s) by gathering around the trap before starting!*"
            )
            return output, "Frosty Local Tactical Core"

        # 3. Crazy Joe query
        elif any(w in q for w in ["joe", "crazy joe"]):
            output = (
                "### 🎯 Crazy Joe Defense Strategy\n\n"
                "**1. Overview & Waves:**\n"
                "• 20 waves over ~40 minutes. Waves **10 & 20** are massive assaults on the **Alliance Headquarters (HQ)**!\n\n"
                "**2. Critical Troop Rules:**\n"
                "• ❌ **NEVER send Marksmen to allies or HQ.** Marksmen must stay home on your own barricade.\n"
                "• ✅ **Send ONLY Infantry & Lancers** to reinforce teammates and the Alliance HQ.\n\n"
                "**3. Empty City Scoring Trick:**\n"
                "• Send your troops out to reinforce online teammates. When Joe attacks your empty city, you still earn defense points while allies protect you.\n\n"
                "---\n"
                "💡 **HQ Checklist:** *Recall one march 5 minutes before Wave 10 and Wave 20 to reinforce the HQ with heavy Infantry!*"
            )
            return output, "Frosty Local Tactical Core"

        # 4. Extract from context
        context_split = system_prompt.split("=== CORE WHITEOUT SURVIVAL MECHANICS & DOCTRINE ===")
        context_body = context_split[1] if len(context_split) > 1 else system_prompt
        clean_context = context_body.replace("=== RETRIEVED WOS ARCHIVES & DATA ===", "").strip()

        output = (
            f"### ❄️ Frosty Tactical Advisory\n\n"
            f"{clean_context[:2500]}\n\n"
            f"---\n"
            f"💡 **Tactical Verdict:** *Synthesized directly from Frosty's Whiteout Survival strategy archives.*"
        )
        return output, "Frosty Local Tactical Core"

