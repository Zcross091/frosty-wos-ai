"""
❄️ Whiteout Survival Registered Players Storage Manager (Multi-Account Support)
Handles storage, querying, and multi-account limits for Discord users
registered for automated Whiteout Survival gift code claiming.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import threading

logger = logging.getLogger("RegisteredPlayers")

DB_PATH = os.path.join(os.path.dirname(__file__), "registered_players.json")
_FILE_LOCK = threading.Lock()

MAX_ACCOUNTS_PER_USER = 5


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


def _normalize_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrates single-account legacy schema to multi-account schema transparently:
    { "accounts": [ { "player_id": "...", "state": 542, "label": "Main", ... } ], "auto_claim": True, "notify_dm": True }
    """
    if "accounts" not in user_data:
        # Legacy record detected
        if "player_id" in user_data and "state" in user_data:
            user_data["accounts"] = [{
                "player_id": str(user_data["player_id"]).strip(),
                "state": int(user_data["state"]),
                "label": "Main",
                "registered_at": user_data.get("registered_at", datetime.utcnow().isoformat() + "Z"),
                "claimed_codes": user_data.get("claimed_codes", []),
                "last_claim_at": user_data.get("last_claim_at"),
                "last_status": user_data.get("last_status", "Registered")
            }]
        else:
            user_data["accounts"] = []

    user_data.setdefault("auto_claim", True)
    user_data.setdefault("notify_dm", True)
    return user_data


def get_player_accounts(discord_user_id: int) -> List[Dict[str, Any]]:
    """Returns all registered accounts for a Discord user."""
    data = load_registered_players()
    uid = str(discord_user_id)
    user_data = data.get("users", {}).get(uid)
    if not user_data:
        return []
    _normalize_user(user_data)
    return user_data.get("accounts", [])


def get_player(discord_user_id: int) -> Optional[Dict[str, Any]]:
    """Backwards-compatible getter: returns the primary/first account for a user."""
    accounts = get_player_accounts(discord_user_id)
    if accounts:
        primary = dict(accounts[0])
        primary["total_accounts"] = len(accounts)
        return primary
    return None


def get_player_owner(player_id: str) -> Optional[str]:
    """Returns the Discord user ID (str) who owns this player_id, or None if not registered."""
    clean_pid = str(player_id).strip()
    data = load_registered_players()
    for uid, udata in data.get("users", {}).items():
        _normalize_user(udata)
        for acc in udata.get("accounts", []):
            if acc.get("player_id") == clean_pid:
                return uid
    return None


def register_player(
    discord_user_id: int, 
    player_id: str, 
    state: int, 
    label: Optional[str] = None, 
    notify_dm: bool = True
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Registers a new account or updates an existing one for a Discord user.
    Enforces a maximum of MAX_ACCOUNTS_PER_USER (5).
    Returns (success: bool, message: str, account_data: dict).
    """
    data = load_registered_players()
    uid = str(discord_user_id)
    clean_pid = str(player_id).strip()
    clean_state = int(state)

    # Check if this player_id is already registered by another Discord user
    owner_uid = get_player_owner(clean_pid)
    if owner_uid and owner_uid != uid:
        logger.info(f"Blocked registration of {clean_pid} by user {uid}: already owned by {owner_uid}")
        return False, "⚠️ This Player ID is already registered by another Discord user. If this is your account, ask them to unregister it.", {}

    user_data = data.setdefault("users", {}).setdefault(uid, {})
    _normalize_user(user_data)
    user_data["notify_dm"] = notify_dm
    accounts = user_data["accounts"]

    # Check if this player_id is already registered by this user (update)
    for acc in accounts:
        if acc["player_id"] == clean_pid:
            acc["state"] = clean_state
            if label:
                acc["label"] = label.strip()
            acc["updated_at"] = datetime.utcnow().isoformat() + "Z"
            save_registered_players(data)
            logger.info(f"Updated account {clean_pid} (State {clean_state}) for user {uid}")
            return True, f"Updated existing account `{clean_pid}` ({acc['label']}) in State `{clean_state}`.", acc

    # Check maximum accounts limit
    if len(accounts) >= MAX_ACCOUNTS_PER_USER:
        return False, f"⚠️ You have reached the maximum limit of **{MAX_ACCOUNTS_PER_USER} registered accounts**. Use `/codes action:Unregister from Auto-Claim` to free up a slot.", {}

    # Assign default label if none provided
    if not label or not label.strip():
        if len(accounts) == 0:
            clean_label = "Main"
        else:
            clean_label = f"Farm {len(accounts)}"
    else:
        clean_label = label.strip()

    new_acc = {
        "player_id": clean_pid,
        "state": clean_state,
        "label": clean_label,
        "registered_at": datetime.utcnow().isoformat() + "Z",
        "claimed_codes": [],
        "last_claim_at": None,
        "last_status": "Registered",
    }
    accounts.append(new_acc)
    user_data["accounts"] = accounts
    save_registered_players(data)

    logger.info(f"Registered account {clean_pid} [{clean_label}] (State {clean_state}) for user {uid} (Slot {len(accounts)}/{MAX_ACCOUNTS_PER_USER})")
    return True, f"Successfully registered **{clean_label}** (`{clean_pid}`, State `{clean_state}`)! (Account {len(accounts)}/{MAX_ACCOUNTS_PER_USER})", new_acc


def unregister_player(discord_user_id: int, player_id: Optional[str] = None) -> Tuple[bool, str]:
    """
    Removes a specific account or all accounts for a user.
    If player_id is None, deletes all registered accounts for that user.
    """
    data = load_registered_players()
    uid = str(discord_user_id)
    if uid not in data.get("users", {}):
        return False, "⚠️ You do not have any registered accounts."

    user_data = data["users"][uid]
    _normalize_user(user_data)
    accounts = user_data.get("accounts", [])

    if not player_id:
        # Unregister all accounts
        del data["users"][uid]
        save_registered_players(data)
        logger.info(f"Unregistered all accounts for user {uid}")
        return True, "🗑️ All registered accounts have been successfully removed from auto-claim."

    clean_pid = str(player_id).strip()
    remaining = [acc for acc in accounts if acc["player_id"] != clean_pid]
    if len(remaining) == len(accounts):
        return False, f"⚠️ Account with Player ID `{clean_pid}` was not found in your registered accounts."

    if remaining:
        user_data["accounts"] = remaining
    else:
        del data["users"][uid]

    save_registered_players(data)
    logger.info(f"Removed account {clean_pid} for user {uid}")
    return True, f"🗑️ Removed account `{clean_pid}`. You now have **{len(remaining)}/{MAX_ACCOUNTS_PER_USER}** accounts registered."


def toggle_auto_claim(discord_user_id: int, enabled: Optional[bool] = None) -> Optional[bool]:
    """Enables or disables auto-claiming globally for a user."""
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
    """Enables or disables DM notifications for a user."""
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


def record_claim_for_account(
    discord_user_id: int, 
    player_id: str, 
    code: str, 
    success: bool, 
    status_msg: str
) -> None:
    """Records a redemption result for a specific account."""
    data = load_registered_players()
    uid = str(discord_user_id)
    user = data.get("users", {}).get(uid)
    if not user:
        return

    _normalize_user(user)
    clean_pid = str(player_id).strip()
    clean_code = code.strip().upper()

    for acc in user.get("accounts", []):
        if acc["player_id"] == clean_pid:
            claimed = acc.get("claimed_codes", [])
            if clean_code not in [c.upper() for c in claimed]:
                claimed.append(code.strip())
                acc["claimed_codes"] = claimed
            acc["last_claim_at"] = datetime.utcnow().isoformat() + "Z"
            acc["last_status"] = f"{'Success' if success else 'Failed'}: {status_msg}"
            save_registered_players(data)
            break


def get_all_active_accounts() -> List[Dict[str, Any]]:
    """
    Returns a flat list of all active accounts across all registered users
    for the background redemption queue.
    """
    data = load_registered_players()
    active_accounts = []

    for uid, udata in data.get("users", {}).items():
        _normalize_user(udata)
        if not udata.get("auto_claim", True):
            continue

        notify_dm = udata.get("notify_dm", True)
        for acc in udata.get("accounts", []):
            if acc.get("player_id") and acc.get("state"):
                item = dict(acc)
                item["discord_uid"] = uid
                item["notify_dm"] = notify_dm
                active_accounts.append(item)

    return active_accounts


def get_active_auto_claim_players() -> Dict[str, Dict[str, Any]]:
    """Legacy compatibility helper."""
    all_acc = get_all_active_accounts()
    grouped = {}
    for acc in all_acc:
        grouped[f"{acc['discord_uid']}_{acc['player_id']}"] = acc
    return grouped
