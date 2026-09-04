"""
❄️ Whiteout Survival Registered Players Storage Manager
Handles storage and querying for Discord users registered for automated gift code claiming.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import threading

logger = logging.getLogger("RegisteredPlayers")

DB_PATH = os.path.join(os.path.dirname(__file__), "registered_players.json")
_FILE_LOCK = threading.Lock()


def load_registered_players() -> Dict[str, Any]:
    """Loads all registered players from registered_players.json safely."""
    with _FILE_LOCK:
        if os.path.exists(DB_PATH):
            try:
                with open(DB_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "users" in data:
                        return data
            except Exception as e:
                logger.error(f"Error reading {DB_PATH}: {e}")
        return {"users": {}}


def save_registered_players(data: Dict[str, Any]) -> bool:
    """Saves the data structure into registered_players.json safely."""
    with _FILE_LOCK:
        try:
            with open(DB_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving {DB_PATH}: {e}")
            return False


def get_player(discord_user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a player's registration details by their Discord User ID."""
    data = load_registered_players()
    return data.get("users", {}).get(str(discord_user_id))


def register_player(discord_user_id: int, player_id: str, state: int, notify_dm: bool = True) -> Dict[str, Any]:
    """
    Registers or updates a player's Whiteout Survival details.
    """
    data = load_registered_players()
    uid = str(discord_user_id)
    clean_pid = str(player_id).strip()
    clean_state = int(state)

    existing = data.get("users", {}).get(uid, {})
    claimed_codes = existing.get("claimed_codes", [])

    record = {
        "player_id": clean_pid,
        "state": clean_state,
        "auto_claim": True,
        "notify_dm": notify_dm,
        "registered_at": existing.get("registered_at", datetime.utcnow().isoformat() + "Z"),
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "claimed_codes": claimed_codes,
        "last_claim_at": existing.get("last_claim_at"),
        "last_status": existing.get("last_status", "Registered"),
    }

    data.setdefault("users", {})[uid] = record
    save_registered_players(data)
    logger.info(f"Registered user {uid} with Player ID {clean_pid} (State {clean_state})")
    return record


def unregister_player(discord_user_id: int) -> bool:
    """Deletes a player's registration completely."""
    data = load_registered_players()
    uid = str(discord_user_id)
    if uid in data.get("users", {}):
        del data["users"][uid]
        save_registered_players(data)
        logger.info(f"Unregistered user {uid}")
        return True
    return False


def toggle_auto_claim(discord_user_id: int, enabled: Optional[bool] = None) -> Optional[bool]:
    """Enables or disables auto-claiming for a player."""
    data = load_registered_players()
    uid = str(discord_user_id)
    user = data.get("users", {}).get(uid)
    if not user:
        return None

    if enabled is None:
        user["auto_claim"] = not user.get("auto_claim", True)
    else:
        user["auto_claim"] = bool(enabled)

    user["updated_at"] = datetime.utcnow().isoformat() + "Z"
    save_registered_players(data)
    return user["auto_claim"]


def toggle_dm_notification(discord_user_id: int, enabled: Optional[bool] = None) -> Optional[bool]:
    """Enables or disables DM notifications for a player."""
    data = load_registered_players()
    uid = str(discord_user_id)
    user = data.get("users", {}).get(uid)
    if not user:
        return None

    if enabled is None:
        user["notify_dm"] = not user.get("notify_dm", True)
    else:
        user["notify_dm"] = bool(enabled)

    user["updated_at"] = datetime.utcnow().isoformat() + "Z"
    save_registered_players(data)
    return user["notify_dm"]


def record_claim(discord_user_id: int, code: str, success: bool, status_msg: str) -> None:
    """Records a claim attempt result for a player."""
    data = load_registered_players()
    uid = str(discord_user_id)
    user = data.get("users", {}).get(uid)
    if not user:
        return

    claimed = user.get("claimed_codes", [])
    clean_code = code.strip().upper()
    if clean_code not in [c.upper() for c in claimed]:
        claimed.append(code.strip())
        user["claimed_codes"] = claimed

    user["last_claim_at"] = datetime.utcnow().isoformat() + "Z"
    user["last_status"] = f"{'Success' if success else 'Failed'}: {status_msg}"
    save_registered_players(data)


def get_active_auto_claim_players() -> Dict[str, Dict[str, Any]]:
    """Returns all users who have auto_claim enabled."""
    data = load_registered_players()
    return {
        uid: u for uid, u in data.get("users", {}).items()
        if u.get("auto_claim", True) and u.get("player_id") and u.get("state")
    }
