"""
Frosty AI — REST API Backend Server for Mobile App & Web Clients
Features:
1. App Authenticity Handshake (HMAC-SHA256 Request Signature + Replay Protection)
2. Zero-Token WOS Domain Recognizer (Rejects non-WOS queries to protect AI tokens)
3. IP Rate Limiting & Anti-Abuse Shield
4. ChromaDB Hybrid RAG + Multi-Provider AI (Gemini 3.6 Flash, Groq, Ollama, Local)
"""

import os
import re
import time
import hmac
import hashlib
import json
import logging
import mimetypes
import asyncio
import dataclasses
from typing import Tuple, Dict, List, Any, Optional
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import requests

from ai_engine import AIEngine
from knowledge_base import KnowledgeBase
from wos_gateway_protocol import probe_all_gateways, probe_gateway_endpoint, DEFAULT_GATEWAYS

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("FrostyAI.APIServer")

PORT = int(os.getenv("PORT", "8000"))
FROSTY_APP_SECRET = os.getenv("FROSTY_APP_SECRET", "frosty-wos-grandmaster-v2-secure-handshake").strip()
APP_CLIENT_ID = "frosty-wos-official-client"
ENFORCE_APP_HANDSHAKE = os.getenv("ENFORCE_APP_HANDSHAKE", "true").lower() in ["true", "1", "yes"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ai_engine = AIEngine()
knowledge_base = KnowledgeBase()

# --- In-Memory Caching for External Intelligence ---
_intel_cache: Dict[str, Tuple[float, Any]] = {}
CACHE_TTL_SECONDS = 1800  # 30 minutes
WOS_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
WOS_BASE_URL = "https://whiteoutstats.com"


def get_cached_intel(cache_key: str) -> Optional[Any]:
    if cache_key in _intel_cache:
        ts, data = _intel_cache[cache_key]
        if time.time() - ts < CACHE_TTL_SECONDS:
            return data
    return None


def set_cached_intel(cache_key: str, data: Any):
    _intel_cache[cache_key] = (time.time(), data)


def fetch_whiteoutstats(endpoint_path: str, timeout: float = 8.0) -> Tuple[bool, Any, int]:
    """
    Safely fetches intelligence from WhiteoutStats with in-memory caching and browser headers.
    Returns (success, json_data_or_error_dict, status_code).
    """
    cache_key = f"wos_intel:{endpoint_path}"
    cached = get_cached_intel(cache_key)
    if cached is not None:
        return True, cached, 200

    url = f"{WOS_BASE_URL}{endpoint_path}"
    headers = {
        "User-Agent": WOS_USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://whiteoutstats.com/",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            set_cached_intel(cache_key, data)
            return True, data, 200
        else:
            return False, {"error": f"Upstream returned HTTP {resp.status_code}", "status": resp.status_code}, resp.status_code
    except requests.Timeout:
        return False, {"error": "Upstream intelligence timeout (>8s)", "status": 504}, 504
    except Exception as e:
        logger.error(f"Error fetching from WhiteoutStats ({url}): {e}")
        return False, {"error": str(e), "status": 502}, 502


def serve_static_file(handler, filepath: str, content_type: Optional[str] = None):
    """Safely serves static assets avoiding directory traversal."""
    real_path = os.path.abspath(filepath)
    if not real_path.startswith(BASE_DIR):
        handler._set_cors_headers(403)
        handler.wfile.write(json.dumps({"error": "Forbidden"}).encode("utf-8"))
        return

    if not os.path.isfile(real_path):
        handler._set_cors_headers(404)
        handler.wfile.write(json.dumps({"error": "File not found"}).encode("utf-8"))
        return

    if not content_type:
        content_type, _ = mimetypes.guess_type(real_path)
        content_type = content_type or "application/octet-stream"

    try:
        with open(real_path, "rb") as f:
            content = f.read()
        handler.send_response(200)
        handler.send_header("Content-Type", content_type)
        handler.send_header("Content-Length", str(len(content)))
        handler.send_header("Access-Control-Allow-Origin", "*")
        handler.end_headers()
        handler.wfile.write(content)
    except Exception as e:
        logger.error(f"Error serving file {real_path}: {e}")
        handler._set_cors_headers(500)
        handler.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

# --- Rate Limiter & Active Users Storage ---
SERVER_START_TIME = time.time()
ip_request_history: Dict[str, List[float]] = defaultdict(list)
active_devices: Dict[str, float] = {}  # {client_hash: last_seen_epoch}
total_requests_served = 0
total_guardrail_filtered = 0
RATE_LIMIT_WINDOW = 60.0  # seconds
RATE_LIMIT_MAX_REQ = 25   # requests per window


# --- Whiteout Survival Entity & Domain Dictionary (Zero-Token Guardrail) ---
WOS_KEYWORDS = {
    # Game Names & Core Concepts
    "whiteout", "wos", "frosty", "chief", "furnace", "fire crystal", "fc", "fc1", "fc2", "fc3", "fc4", "fc5", "fc6", "fc7", "fc8",
    "state", "server", "sunfire", "castle", "fortress", "stronghold", "turret", "barricade", "infirmary", "monument",
    
    # Resources & Progression
    "gem", "gems", "diamond", "diamonds", "speedup", "speedups", "stamina", "meat", "wood", "coal", "iron", "steel",
    "power", "grow", "growth", "beginner", "guide", "tips", "tricks", "level", "star", "stars", "reset", "vip", "pack", "packs",
    "alliance", "tech", "technology", "research", "construction", "training", "healing",
    
    # Troop Types & Formations
    "infantry", "lancer", "marksman", "sharpshooter", "troops", "troop", "formation", "ratio", "ratios", "50/20/30", "10/10/80", "60/20/20", "40/10/50", "4-1-1",
    "garrison", "rally", "joiner", "joiners", "reinforce", "reinforcement", "reinforcements", "march", "capacity", "lethality", "health", "defense", "attack", "stat", "stats",
    
    # Heroes (Generations 0 to 16+)
    "seigel", "aisling", "ursar", "hank", "viveca", "estrella", "elif", "dominic", "cara",
    "gisela", "flora", "vulcanus", "hervor", "karol", "ligeia", "eleonora", "lloyd", "rufus",
    "gregory", "freya", "blanchette", "magnus", "fred", "xura", "gatot", "sonya", "hendrik",
    "bradley", "gordon", "edith", "wayne", "wu ming", "renee", "hector", "norah", "gwen",
    "ahmose", "reina", "lynn", "logan", "greg", "mia", "flint", "philly", "alonso",
    "jeronimo", "natalia", "molly", "zinman", "jessie", "sergey", "patrick", "bahiti", "gina",
    "jasser", "seo-yoon", "seoyoon", "walis", "smith", "eugene", "charlie", "cloris",
    "hero", "heroes", "mythic", "epic", "rare", "legendary",
    
    # Events & Modes
    "bear", "trap", "bear trap", "crazy joe", "joe", "foundry", "foundry battle", "frostfire", "mine", "frostfire mine",
    "canyon", "canyon clash", "svs", "state vs state", "state of power", "kill event", "ke", "prep stage", "preparation",
    "mercenary", "prestige", "beast", "beasts", "polar terror", "intel", "exploration", "arena", "hero journey", "light the fire",
    
    # Progression & Economy
    "chief gear", "charms", "hero gear", "exclusive gear", "gear", "widgets", "widget", "shards", "shard", "mythic shards", "generic shards",
    "lucky wheel", "wheel", "hall of heroes", "dawn academy", "expert", "experts", "agnes", "cyrille", "baldur", "romulus", "valeria",
    "island", "tree of life", "state transfer", "transfer", "generation", "gen", "gen 1", "gen 2", "gen 3", "gen 4",
    "gen 5", "gen 6", "gen 7", "gen 8", "gen 9", "gen 10", "gen 11", "gen 12", "gen 13", "gen 14", "gen 15", "gen 16",
    
    # Strategy & Combat Verbs
    "lineup", "lineups", "squad", "team", "upgrade", "counter", "tier list", "best hero", "best team", "best march", "f2p", "p2w", "spending", "spend"
}


def verify_app_signature(headers: Dict[str, str], body_text: str, query: str = "") -> Tuple[bool, str]:
    """
    Validates HMAC-SHA256 signature generated by legitimate Frosty mobile app.
    Prevents unauthorized scrapers, hackers, and modded clients.
    """
    if not ENFORCE_APP_HANDSHAKE:
        return True, "Handshake bypass (dev mode)"

    client_id = headers.get("X-Frosty-App-Id", "").strip()
    timestamp_str = headers.get("X-Frosty-Timestamp", "").strip()
    client_sig = headers.get("X-Frosty-Signature", "").strip()

    if not client_id or not timestamp_str or not client_sig:
        return False, "Missing security headers (X-Frosty-App-Id, X-Frosty-Timestamp, X-Frosty-Signature)"

    if client_id != APP_CLIENT_ID:
        return False, f"Invalid client ID: {client_id}"

    try:
        req_timestamp = int(timestamp_str)
    except ValueError:
        return False, "Invalid timestamp format"

    # Replay Protection: Timestamp must be within 300 seconds (5 minutes) of server time
    current_timestamp = int(time.time())
    if abs(current_timestamp - req_timestamp) > 300:
        return False, "Request expired or clock drift exceeded 300s (Replay Protection)"

    # Compute expected signatures (supports body-level or query-level signing)
    secret_bytes = FROSTY_APP_SECRET.encode("utf-8")
    sig_full_body = hmac.new(secret_bytes, f"{req_timestamp}:{body_text}".encode("utf-8"), hashlib.sha256).hexdigest()
    sig_query_only = hmac.new(secret_bytes, f"{req_timestamp}:{query}".encode("utf-8"), hashlib.sha256).hexdigest()

    if hmac.compare_digest(sig_full_body.lower(), client_sig.lower()) or hmac.compare_digest(sig_query_only.lower(), client_sig.lower()):
        return True, "Signature valid"

    return False, "Invalid HMAC security signature (Unauthorized client)"


def is_wos_relevant(query: str) -> Tuple[bool, str]:
    """
    Zero-Token Semantic Guardrail:
    Determines if user query is legitimately related to Whiteout Survival tactics/gameplay.
    Rejects generic questions (coding, essays, general chit-chat) to save 100% of LLM API tokens.
    """
    q = query.lower()
    
    # 1. Direct Keyword Match
    words = set(re.findall(r'[a-z0-9\/\-\+\:]+', q))
    for kw in WOS_KEYWORDS:
        if " " in kw:
            if kw in q:
                return True, f"Matched keyword phrase '{kw}'"
        else:
            if kw in words or kw in q:
                return True, f"Matched keyword '{kw}'"

    # 2. Numbered Generation / State Pattern Matches (e.g. "gen 15", "state 266", "fc 3")
    if re.search(r'\b(gen|generation)\s*\d+\b', q):
        return True, "Matched Generation query"
    if re.search(r'\b(state|server)\s*\d+\b', q):
        return True, "Matched State query"
    if re.search(r'\b\d{1,2}\/\d{1,2}\/\d{1,2}\b', q):
        return True, "Matched Formation Ratio query"

    # 3. Strategy Intent + Combat Context (e.g. "best attack lineup against lancer")
    combat_terms = {"hero", "heroes", "troop", "troops", "squad", "march", "tank", "healer", "dps", "pvp", "pve", "event", "buff", "stat"}
    strategy_terms = {"best", "how to", "who to", "should i", "upgrade", "lineup", "formation", "guide", "tips", "build", "vs"}
    if len(words.intersection(combat_terms)) >= 1 and len(words.intersection(strategy_terms)) >= 1:
        return True, "Matched Combat/Strategy intent"

    return False, "Query does not contain recognized Whiteout Survival game entities, mechanics, or tactical context"


def check_rate_limit(client_ip: str) -> bool:
    """Sliding-window IP rate limiter."""
    now = time.time()
    history = ip_request_history[client_ip]
    # Prune old timestamps
    ip_request_history[client_ip] = [ts for ts in history if now - ts < RATE_LIMIT_WINDOW]
    
    if len(ip_request_history[client_ip]) >= RATE_LIMIT_MAX_REQ:
        return False
    
    ip_request_history[client_ip].append(now)
    return True


class FrostyAPIHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Frosty-App-Id, X-Frosty-Timestamp, X-Frosty-Signature")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_cors_headers(200)

    def do_HEAD(self):
        self._set_cors_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if not path:
            path = "/"

        # 1. Static Website Files
        if path == "/":
            index_path = os.path.join(BASE_DIR, "index.html")
            serve_static_file(self, index_path, "text/html; charset=utf-8")
            return

        # Check for direct static assets (e.g. /style.css, /app.js, /heroes_data.json, /assets/...)
        rel_path = parsed.path.lstrip("/")
        potential_static = os.path.join(BASE_DIR, rel_path)
        if os.path.isfile(potential_static) and os.path.abspath(potential_static).startswith(BASE_DIR):
            serve_static_file(self, potential_static)
            return

        # 2. REST API: Health Check
        if path == "/api/health":
            self._set_cors_headers(200)
            chunk_count = knowledge_base.collection.count() if knowledge_base.collection else 0
            response = {
                "status": "online",
                "service": "Frosty Tactical AI Server",
                "active_model": ai_engine.get_active_model_name(),
                "guardrail": "Zero-Token WOS Relevance Classifier & HMAC Handshake Active",
                "knowledge_chunks": chunk_count
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))
            return

        # 3. REST API: Active Users & Usage Telemetry
        if path in ["/api/stats", "/stats"]:
            self._set_cors_headers(200)
            now = time.time()
            active_1h = sum(1 for t in active_devices.values() if (now - t) <= 3600)
            active_24h = sum(1 for t in active_devices.values() if (now - t) <= 86400)
            active_7d = sum(1 for t in active_devices.values() if (now - t) <= 604800)
            uptime_seconds = int(now - SERVER_START_TIME)

            response = {
                "status": "online",
                "service": "Frosty Tactical AI Server",
                "uptime_hours": round(uptime_seconds / 3600, 2),
                "uptime_human": f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m",
                "active_mobile_users": {
                    "last_1_hour": active_1h,
                    "last_24_hours": active_24h,
                    "last_7_days": active_7d
                },
                "total_tactical_queries_served": total_requests_served,
                "zero_token_guardrail_blocked": total_guardrail_filtered,
                "active_model": ai_engine.get_active_model_name(),
                "knowledge_chunks": knowledge_base.collection.count() if knowledge_base.collection else 0
            }
            self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))
            return

        # 4. REST API: WOS Kingdom Intelligence (Real-time telemetry, Top Whales, Health Grade)
        if path.startswith("/api/wos/kingdom/"):
            kid_raw = path.split("/api/wos/kingdom/")[1].strip()
            if not kid_raw.isdigit():
                self._set_cors_headers(400)
                self.wfile.write(json.dumps({"error": "Invalid kingdom ID (must be integer)"}).encode("utf-8"))
                return

            ok, data, status = fetch_whiteoutstats(f"/api/kingdoms/{kid_raw}")
            self._set_cors_headers(status)
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # 5. REST API: WOS Head-to-Head Compare Matrix
        if path == "/api/wos/compare":
            qs = parse_qs(parsed.query)
            state_a = qs.get("a", ["266"])[0].strip()
            state_b = qs.get("b", ["265"])[0].strip()
            depth = qs.get("n", ["100"])[0].strip()

            if not state_a.isdigit() or not state_b.isdigit():
                self._set_cors_headers(400)
                self.wfile.write(json.dumps({"error": "States 'a' and 'b' must be integers"}).encode("utf-8"))
                return

            ok, data, status = fetch_whiteoutstats(f"/api/compare?a={state_a}&b={state_b}&n={depth}")
            self._set_cors_headers(status)
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # 6. REST API: WOS Kingdom State Transfer Registry & Group Brackets
        if path.startswith("/api/wos/transfers/"):
            kid_raw = path.split("/api/wos/transfers/")[1].strip()
            if not kid_raw.isdigit():
                self._set_cors_headers(400)
                self.wfile.write(json.dumps({"error": "Invalid kingdom ID (must be integer)"}).encode("utf-8"))
                return

            ok, data, status = fetch_whiteoutstats(f"/api/kingdoms/{kid_raw}/transfers")
            self._set_cors_headers(status)
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # 7. REST API: Century Games & iLiveData Direct Socket Gateway Health Probes
        if path == "/api/wos/gateways":
            try:
                results = asyncio.run(probe_all_gateways(timeout=2.5))
                self._set_cors_headers(200)
                payload = {
                    "ok": True,
                    "timestamp": time.time(),
                    "total_gateways": len(results),
                    "online_gateways": sum(1 for r in results if r.online),
                    "gateways": [dataclasses.asdict(r) for r in results]
                }
                self.wfile.write(json.dumps(payload).encode("utf-8"))
            except Exception as e:
                logger.error(f"Error probing gateways: {e}")
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # Fallback 404
        self._set_cors_headers(404)
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def do_POST(self):
        global total_requests_served, total_guardrail_filtered
        parsed = urlparse(self.path)
        client_ip = self.client_address[0]

        if parsed.path == "/api/chat":
            # Track active client
            client_hash = hashlib.sha256(client_ip.encode("utf-8")).hexdigest()[:12]
            active_devices[client_hash] = time.time()

            # 1. Rate Limiting Check
            if not check_rate_limit(client_ip):
                logger.warning(f"⛔ Rate limit exceeded for IP {client_ip}")
                self._set_cors_headers(429)
                self.wfile.write(json.dumps({
                    "error": "Rate limit exceeded (Max 25 requests/min). Please wait before sending more tactical requests."
                }).encode("utf-8"))
                return

            try:
                content_length = int(self.headers.get("Content-Length", 0))
                if content_length > 8192:  # 8KB max payload
                    self._set_cors_headers(413)
                    self.wfile.write(json.dumps({"error": "Payload too large (Max 8KB)"}).encode("utf-8"))
                    return

                raw_body = self.rfile.read(content_length).decode("utf-8")
                
                data = {}
                try:
                    data = json.loads(raw_body)
                except Exception:
                    pass

                query = data.get("query", "").strip() or data.get("prompt", "").strip() or data.get("message", "").strip()

                # 2. App Handshake Signature Verification (Prevents unauthorized bots / modded apps)
                is_valid_app, handshake_msg = verify_app_signature(self.headers, raw_body, query)
                if not is_valid_app:
                    logger.warning(f"🔒 Unauthorized App Request from {client_ip}: {handshake_msg}")
                    self._set_cors_headers(403)
                    self.wfile.write(json.dumps({
                        "error": "Forbidden: Unauthorized App Client",
                        "details": handshake_msg,
                        "action": "Please use the official Frosty WOS Mobile App to communicate with this server."
                    }).encode("utf-8"))
                    return

                if not query:
                    self._set_cors_headers(400)
                    self.wfile.write(json.dumps({"error": "Query cannot be empty"}).encode("utf-8"))
                    return

                # 3. Zero-Token WOS Relevance Recognizer (Saves 100% LLM tokens on non-WOS queries)
                is_wos, reason = is_wos_relevant(query)
                if not is_wos:
                    total_guardrail_filtered += 1
                    logger.info(f"🛡️ Non-WOS query filtered from {client_ip}: '{query[:60]}...' ({reason})")
                    self._set_cors_headers(400)
                    self.wfile.write(json.dumps({
                        "error": "Non-WOS Query Filtered",
                        "message": "❄️ **Frosty Tactical Directive:** I am exclusively calibrated for **Whiteout Survival** military intelligence, hero builds, troop ratios (50/20/30), Bear Trap buffs, and SvS strategy.\n\n*Please ask a question relating to Whiteout Survival to consult the Tactical Oracle!*",
                        "reason": reason
                    }).encode("utf-8"))
                    return

                total_requests_served += 1

                history = data.get("history", [])

                # 4. ChromaDB Semantic Context Retrieval
                context = knowledge_base.search_context(query, max_chunks=5)
                system_prompt = knowledge_base.build_system_prompt(query, context)

                # 5. Multi-Provider AI Inference (Gemini 3.6 Flash / Groq / Ollama / Local)
                answer, model_used, elapsed = ai_engine.generate_response(
                    system_prompt=system_prompt,
                    user_message=query,
                    history=history,
                    temperature=0.6
                )

                self._set_cors_headers(200)
                response_payload = {
                    "text": answer,
                    "model": model_used,
                    "latency": elapsed,
                    "sources_used": len(context),
                    "wos_verified": True
                }
                self.wfile.write(json.dumps(response_payload).encode("utf-8"))

            except Exception as e:
                logger.error(f"Error handling /api/chat from {client_ip}: {e}", exc_info=True)
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self._set_cors_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {args[0]} {args[1]}")


def run_server():
    server = HTTPServer(("0.0.0.0", PORT), FrostyAPIHandler)
    logger.info(f"❄️ Frosty Protected REST API Server running on port {PORT} (http://0.0.0.0:{PORT})")
    logger.info(f"🛡️ App Handshake Enforcement: {ENFORCE_APP_HANDSHAKE}")
    logger.info("🛡️ Zero-Token WOS Domain Recognizer: ACTIVE")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping server...")
        server.server_close()


if __name__ == "__main__":
    run_server()
