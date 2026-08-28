"""
Frosty AI — REST API Backend Server for Mobile App & Web Clients
Provides HTTP JSON endpoints:
- POST /api/chat: ChromaDB RAG + Multi-Provider AI (Gemini 3.6 Flash, Groq, Ollama, Local)
- GET /api/health: Health check and server status
"""

import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from dotenv import load_dotenv

from ai_engine import AIEngine
from knowledge_base import KnowledgeBase

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("FrostyAI.APIServer")

PORT = int(os.getenv("PORT", "8000"))
ai_engine = AIEngine()
knowledge_base = KnowledgeBase()

class FrostyAPIHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_cors_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ["/api/health", "/"]:
            self._set_cors_headers(200)
            chunk_count = knowledge_base.collection.count() if knowledge_base.collection else 0
            response = {
                "status": "online",
                "service": "Frosty Tactical AI Server",
                "active_model": ai_engine.get_active_model_name(),
                "knowledge_chunks": chunk_count
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self._set_cors_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/chat":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(body)
                
                query = data.get("query", "").strip() or data.get("prompt", "").strip() or data.get("message", "").strip()
                if not query:
                    self._set_cors_headers(400)
                    self.wfile.write(json.dumps({"error": "Query cannot be empty"}).encode("utf-8"))
                    return

                history = data.get("history", [])
                
                # 1. ChromaDB Semantic Context Retrieval
                context = knowledge_base.search_context(query, max_chunks=5)
                system_prompt = knowledge_base.build_system_prompt(query, context)
                
                # 2. Multi-Provider AI Inference
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
                    "sources_used": len(context)
                }
                self.wfile.write(json.dumps(response_payload).encode("utf-8"))
                
            except Exception as e:
                logger.error(f"Error handling /api/chat: {e}", exc_info=True)
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self._set_cors_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def log_message(self, format, *args):
        # Clean formatted logging
        logger.info(f"{self.address_string()} - {args[0]} {args[1]}")

def run_server():
    server = HTTPServer(("0.0.0.0", PORT), FrostyAPIHandler)
    logger.info(f"❄️ Frosty REST API Server listening on port {PORT} (http://0.0.0.0:{PORT})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping server...")
        server.server_close()

if __name__ == "__main__":
    run_server()
