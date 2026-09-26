"""
❄️ Whiteout Survival Gift Code Center API Client
Reverse-engineered from Century Games' official redemption portal:
https://wos-giftcode.centurygame.com/
"""

import hashlib
import time
import urllib.parse
import logging
from typing import Dict, Any, Optional
import asyncio
import requests

logger = logging.getLogger("WosGiftcodeApi")

API_ENDPOINT = "https://wos-giftcode-api.centurygame.com/api/gift_code"
SECRET_SALT = "tB87#kPtkxqOS2"

COMMON_HEADERS = {
    "Origin": "https://wos-giftcode.centurygame.com",
    "Referer": "https://wos-giftcode.centurygame.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded",
}

# Error code to human-readable message mapping
ERROR_CODE_MESSAGES = {
    20000: "✅ Success! In-game rewards have been sent to your mailbox.",
    40007: "⚠️ Already Claimed! This gift code was already claimed for your character.",
    40008: "⌛ Expired! This gift code has expired and can no longer be redeemed.",
    40005: "❌ Invalid Code! Gift code does not exist. Check case-sensitivity.",
    40020: "❌ Character Info Incorrect! Player ID and State number do not match or character was not found.",
    40009: "⛔ Requirements Not Met! Your character level/age does not meet the requirements for this code.",
    40100: "🤖 Captcha Triggered! Century Games security check required.",
    40102: "🤖 Captcha Verification Failed.",
    40002: "⏱️ Rate Limited! Frequency too high. Please try again later.",
    40004: "⏱️ Rate Limited! Cooldown active on Century Games server.",
    40014: "⚠️ Same Type Exchange! A code of this campaign type was already used.",
    429: "⏱️ Too Many Requests (429)! Century Games rate limit reached.",
}


def sign_payload(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constructs the MD5 signed dictionary required by Century Games Gift Code API.
    1. Sort keys alphabetically.
    2. URL-encode parameters as k1=v1&k2=v2...
    3. Append SECRET_SALT ('tB87#kPtkxqOS2').
    4. Calculate MD5 hex digest.
    """
    sorted_keys = sorted(params.keys())
    query_parts = []
    for k in sorted_keys:
        v = params[k]
        query_parts.append(f"{k}={urllib.parse.quote(str(v), safe='')}")
    query_string = "&".join(query_parts)

    raw_signature_str = query_string + SECRET_SALT
    sign = hashlib.md5(raw_signature_str.encode("utf-8")).hexdigest()

    result = dict(params)
    result["sign"] = sign
    return result


def redeem_gift_code_sync(player_id: str, state: int, code: str, timeout: int = 15) -> Dict[str, Any]:
    """
    Synchronous HTTP request to redeem a Whiteout Survival gift code.
    Returns a standardized dictionary:
    {
        "success": bool,
        "err_code": int,
        "message": str,
        "raw": dict
    }
    """
    clean_fid = str(player_id).strip()
    clean_kid = str(state).strip()
    clean_cdk = str(code).strip()

    payload = {
        "fid": clean_fid,
        "kid": clean_kid,
        "cdk": clean_cdk,
        "time": int(time.time()),
    }
    signed_payload = sign_payload(payload)

    try:
        resp = requests.post(
            API_ENDPOINT,
            headers=COMMON_HEADERS,
            data=signed_payload,
            timeout=timeout
        )
        if resp.status_code == 429:
            return {
                "success": False,
                "err_code": 429,
                "message": "⏱️ Too Many Requests (429)! Century Games rate limit reached.",
                "raw": {}
            }
        if resp.status_code != 200:
            return {
                "success": False,
                "err_code": resp.status_code,
                "message": f"HTTP error {resp.status_code} from Century Games portal.",
                "raw": {}
            }

        data = resp.json()
        err_code = data.get("err_code", 0)
        raw_msg = str(data.get("msg", "")).strip()

        # Success is either err_code == 20000 or (code == 0 and err_code == 0 and raw_msg == SUCCESS)
        is_success = (err_code == 20000) or (data.get("code") == 0 and err_code == 0 and raw_msg.upper() == "SUCCESS")

        if err_code in ERROR_CODE_MESSAGES:
            msg = ERROR_CODE_MESSAGES[err_code]
        elif "SAME TYPE EXCHANGE" in raw_msg.upper():
            msg = "⚠️ Same Type Exchange! A gift code of this campaign type was already used."
        elif raw_msg and raw_msg != str(err_code):
            msg = raw_msg
        elif err_code == 40004:
            msg = "⏱️ Rate Limited! Cooldown active on Century Games server."
        else:
            msg = f"Century Games response: {err_code or raw_msg or 'Unknown'}"

        return {
            "success": is_success,
            "err_code": err_code,
            "message": msg,
            "raw": data
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "err_code": -1,
            "message": "Connection timed out reaching Century Games portal.",
            "raw": {}
        }
    except Exception as e:
        logger.error(f"Error redeeming gift code: {e}")
        return {
            "success": False,
            "err_code": -2,
            "message": f"Network or parsing error: {str(e)}",
            "raw": {}
        }


async def redeem_gift_code(player_id: str, state: int, code: str, timeout: int = 15) -> Dict[str, Any]:
    """
    Async wrapper for redeem_gift_code_sync. Runs in thread pool to prevent blocking asyncio loop.
    """
    return await asyncio.to_thread(redeem_gift_code_sync, player_id, state, code, timeout)
