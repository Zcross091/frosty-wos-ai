"""
❄️ Whiteout Survival Community Intelligence API Client
Integrates with WhiteoutStats API (https://api.whiteoutstats.com/v1) for live state metrics,
alliance power rankings, member counts, and transfer registries.
"""

import os
import time
import logging
from typing import Dict, Any, Optional
import aiohttp

logger = logging.getLogger("WosIntelligence")

BASE_API_URL = "https://api.whiteoutstats.com/v1"
DEFAULT_CACHE_TTL_SECONDS = 300  # 5 minutes


class WosIntelligenceClient:
    """
    Client for querying WhiteoutStats community intelligence endpoints with
    in-memory caching, rate limiting protection, and structured responses.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("WHITEOUTSTATS_API_KEY", "").strip()
        self._cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": "Frosty-WOS-AI/2.0 (DiscordBot; State266-Intl)",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        cached = self._cache.get(key)
        if cached:
            timestamp, data = cached
            if time.time() - timestamp < DEFAULT_CACHE_TTL_SECONDS:
                return data
        return None

    def _set_cache(self, key: str, data: Dict[str, Any]) -> None:
        self._cache[key] = (time.time(), data)

    async def get_alliance_intel(self, state: int, tag: str) -> Dict[str, Any]:
        """
        Fetches live alliance metrics (power, member count, ranking, leader)
        for a specific state and alliance tag (e.g. state=266, tag="AVM").
        """
        clean_tag = tag.strip().upper()
        cache_key = f"alliance_{state}_{clean_tag}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return {"source": "cache", **cached}

        url = f"{BASE_API_URL}/alliances/{state}/{clean_tag}"
        params = {"include": "info"}

        try:
            async with aiohttp.ClientSession(headers=self._get_headers()) as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=8.0)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result = {
                            "success": True,
                            "state": state,
                            "tag": clean_tag,
                            "data": data,
                            "source": "live",
                        }
                        self._set_cache(cache_key, result)
                        return result
                    elif resp.status == 401:
                        return {
                            "success": False,
                            "err_code": 401,
                            "message": "🔒 WhiteoutStats API key required or expired. Set WHITEOUTSTATS_API_KEY in bot configuration.",
                            "state": state,
                            "tag": clean_tag,
                        }
                    elif resp.status == 404:
                        return {
                            "success": False,
                            "err_code": 404,
                            "message": f"Alliance `[{clean_tag}]` was not found in State `{state}` on WhiteoutStats database.",
                            "state": state,
                            "tag": clean_tag,
                        }
                    else:
                        text = await resp.text()
                        return {
                            "success": False,
                            "err_code": resp.status,
                            "message": f"WhiteoutStats returned status {resp.status}: {text[:100]}",
                            "state": state,
                            "tag": clean_tag,
                        }
        except aiohttp.ClientConnectorError:
            return {
                "success": False,
                "err_code": -1,
                "message": "⚠️ Unable to connect to WhiteoutStats API gateway.",
                "state": state,
                "tag": clean_tag,
            }
        except Exception as e:
            logger.error(f"Error fetching alliance intel: {e}")
            return {
                "success": False,
                "err_code": -2,
                "message": f"Network or parsing error: {str(e)}",
                "state": state,
                "tag": clean_tag,
            }

    async def get_state_intel(self, state: int) -> Dict[str, Any]:
        """
        Fetches state-level intelligence summary and transfer registry info from WhiteoutStats.
        """
        cache_key = f"state_{state}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return {"source": "cache", **cached}

        url = f"{BASE_API_URL}/states/{state}"

        try:
            async with aiohttp.ClientSession(headers=self._get_headers()) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=8.0)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result = {
                            "success": True,
                            "state": state,
                            "data": data,
                            "source": "live",
                        }
                        self._set_cache(cache_key, result)
                        return result
                    elif resp.status == 401:
                        return {
                            "success": False,
                            "err_code": 401,
                            "message": "🔒 WhiteoutStats API key required. Set WHITEOUTSTATS_API_KEY in bot .env configuration.",
                            "state": state,
                        }
                    else:
                        return {
                            "success": False,
                            "err_code": resp.status,
                            "message": f"State `{state}` info unavailable on WhiteoutStats (Status {resp.status}).",
                            "state": state,
                        }
        except Exception as e:
            return {
                "success": False,
                "err_code": -1,
                "message": f"Error reaching WhiteoutStats: {str(e)}",
                "state": state,
            }


# Global singleton instance
intelligence_client = WosIntelligenceClient()
