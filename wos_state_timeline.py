"""
❄️ Whiteout Survival State Timeline & Hero Generation Engine
Provides calibrated server age estimation, live WhiteoutStats API integration,
active hero generation tracking, and future generation unlock roadmaps (Gen 1 to Gen 17).
"""

import os
import re
import json
import logging
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger("FrostyAI.StateTimeline")

# Memory cache for live WhiteoutStats kingdom telemetry (TTL: 24 hours)
_KINGDOM_CACHE: Dict[int, Dict[str, Any]] = {}
_KINGDOM_CACHE_EXPIRY: Dict[int, float] = {}
CACHE_TTL_SECONDS = 86400  # 24 hours

# Piecewise calibrated Whiteout Survival Historical Launch Anchor Points (State Number, Launch Date UTC)
STATE_LAUNCH_ANCHORS = [
    (1, datetime(2023, 2, 14, 0, 0, 0)),
    (60, datetime(2023, 3, 19, 13, 15, 2)),
    (80, datetime(2023, 4, 2, 8, 30, 1)),
    (91, datetime(2023, 4, 11, 0, 30, 1)),
    (120, datetime(2023, 5, 5, 4, 30, 2)),
    (140, datetime(2023, 5, 22, 1, 0, 1)),
    (195, datetime(2023, 6, 25, 15, 45, 1)),
    (210, datetime(2023, 7, 2, 5, 45, 2)),
    (225, datetime(2023, 7, 7, 15, 0, 2)),
    (240, datetime(2023, 7, 13, 1, 5, 2)),
    (266, datetime(2023, 7, 21, 10, 35, 3)),
    (300, datetime(2023, 8, 2, 13, 35, 3)),
    (350, datetime(2023, 8, 20, 7, 35, 3)),
    (380, datetime(2023, 8, 28, 10, 25, 3)),
    (390, datetime(2023, 8, 31, 15, 0, 2)),
    (480, datetime(2023, 10, 10, 15, 15, 3)),
    (500, datetime(2023, 10, 19, 14, 35, 3)),
    (542, datetime(2023, 11, 3, 10, 25, 2)),
    (600, datetime(2023, 11, 22, 17, 45, 2)),
    (700, datetime(2023, 12, 25, 14, 15, 1)),
    (800, datetime(2024, 1, 21, 3, 15, 1)),
    (900, datetime(2024, 2, 21, 11, 55, 2)),
    (1000, datetime(2024, 3, 25, 5, 5, 2)),
    (1200, datetime(2024, 5, 17, 16, 0, 2)),
    (1400, datetime(2024, 7, 2, 5, 40, 3)),
    (1600, datetime(2024, 8, 15, 18, 45, 4)),
    (1800, datetime(2024, 9, 25, 19, 15, 2)),
    (2000, datetime(2024, 11, 1, 16, 15, 2)),
    (2200, datetime(2024, 12, 12, 17, 15, 2)),
    (2500, datetime(2025, 2, 2, 9, 30, 2)),
    (2800, datetime(2025, 4, 19, 2, 15, 3)),
    (3000, datetime(2025, 6, 10, 12, 0, 2)),
    (3200, datetime(2025, 7, 26, 7, 15, 2)),
    (3500, datetime(2025, 9, 26, 17, 0, 2)),
    (3800, datetime(2025, 12, 8, 13, 45, 2)),
    (4000, datetime(2026, 1, 18, 0, 2, 2)),
    (4100, datetime(2026, 2, 10, 20, 45, 3)),
    (4200, datetime(2026, 3, 12, 13, 0, 5)),
    (4300, datetime(2026, 4, 17, 13, 45, 17)),
    (4400, datetime(2026, 5, 23, 15, 0, 11)),
    (4500, datetime(2026, 6, 27, 10, 58, 8)),
    (4600, datetime(2026, 8, 7, 20, 15, 9)),
    (4670, datetime(2026, 9, 4, 10, 45, 9)),
]

# Master Registry of Whiteout Survival Generations (Gen 1 to Gen 17)
# Source verified via game updates, Heroes.md, and community data
HERO_GENERATIONS: Dict[int, Dict[str, Any]] = {
    1: {
        "gen": 1,
        "unlock_day": 0,
        "infantry": {"name": "Jeronimo", "source": "VIP / Hall of Chiefs", "role": "Rally DPS & Tank"},
        "infantry_alt": {"name": "Natalia", "source": "First Purchase / Packs", "role": "Beast & Stun Tank"},
        "lancer": {"name": "Molly", "source": "Day 2 Sign-in / Intel / HoH", "role": "Early Rally Joiner & Flanker"},
        "marksman": {"name": "Zinman", "source": "Lucky Wheel", "role": "Construction & Resource Economy"},
        "wheel_hero": "Zinman (Marksman)",
        "hoh_hero": "Jeronimo (Infantry)",
        "summary": "Natalia, Jeronimo, Molly, Zinman. Foundation heroes unlocked on server launch."
    },
    2: {
        "gen": 2,
        "unlock_day": 40,
        "infantry": {"name": "Flint", "source": "Lucky Wheel", "role": "Top F2P Tank & Frontline Shield"},
        "lancer": {"name": "Philly", "source": "Packs / Mystery Shop", "role": "Healer & Sustain"},
        "marksman": {"name": "Alonso", "source": "Hall of Heroes / KoI", "role": "High Single-target Burst"},
        "wheel_hero": "Flint (Infantry)",
        "hoh_hero": "Alonso (Marksman)",
        "summary": "Flint, Alonso, Philly. Flint is the essential F2P tank from the Lucky Wheel."
    },
    3: {
        "gen": 3,
        "unlock_day": 120,
        "infantry": {"name": "Logan", "source": "Hall of Heroes", "role": "Arena & Garrison Tank"},
        "lancer": {"name": "Greg", "source": "Packs / Mystery Shop", "role": "Flanker & Sustained DPS"},
        "marksman": {"name": "Mia", "source": "Lucky Wheel", "role": "Apex Bear Trap & Exploration Carry"},
        "wheel_hero": "Mia (Marksman)",
        "hoh_hero": "Logan (Infantry)",
        "summary": "Mia, Logan, Greg. Mia is the #1 Lucky Wheel priority for Bear Trap damage."
    },
    4: {
        "gen": 4,
        "unlock_day": 195,
        "infantry": {"name": "Ahmose", "source": "Hall of Heroes", "role": "Invincible Barrier Tank"},
        "lancer": {"name": "Reina", "source": "Packs / Mystery Shop", "role": "High Velocity Burst Lancer"},
        "marksman": {"name": "Lynn", "source": "Lucky Wheel", "role": "Armor-Piercing Marksman"},
        "wheel_hero": "Lynn (Marksman)",
        "hoh_hero": "Ahmose (Infantry)",
        "summary": "Lynn, Ahmose, Reina. Lynn dominates wheel spins; Ahmose is an elite PvP wall."
    },
    5: {
        "gen": 5,
        "unlock_day": 270,
        "infantry": {"name": "Hector", "source": "Lucky Wheel", "role": "Fortress & Sunfire Rally Lead"},
        "lancer": {"name": "Norah", "source": "Hall of Heroes", "role": "Backline Flanker & Stun"},
        "marksman": {"name": "Gwen", "source": "Packs / Mystery Shop", "role": "Precision Sniper"},
        "wheel_hero": "Hector (Infantry)",
        "hoh_hero": "Norah (Lancer)",
        "summary": "Hector, Norah, Gwen. Hector is the premier fortress garrison lead on Lucky Wheel."
    },
    6: {
        "gen": 6,
        "unlock_day": 360,
        "infantry": {"name": "Wayne", "source": "Hall of Heroes", "role": "Garrison Defender & Counter"},
        "lancer": {"name": "Wu Ming", "source": "Packs / Mystery Shop", "role": "Debuff Lancer"},
        "marksman": {"name": "Renee", "source": "Lucky Wheel", "role": "Heavy Area Marksman"},
        "wheel_hero": "Renee (Marksman)",
        "hoh_hero": "Wayne (Infantry)",
        "summary": "Renee, Wayne, Wu Ming. Renee brings massive AoE damage from the Lucky Wheel."
    },
    7: {
        "gen": 7,
        "unlock_day": 440,
        "infantry": {"name": "Bradley", "source": "Lucky Wheel", "role": "Fortress Stun & Resilience Lead"},
        "lancer": {"name": "Gordon", "source": "Packs / Mystery Shop", "role": "High Impact Lancer"},
        "marksman": {"name": "Edith", "source": "Hall of Heroes", "role": "Marksman Assassin"},
        "wheel_hero": "Bradley (Infantry)",
        "hoh_hero": "Edith (Marksman)",
        "summary": "Bradley, Edith, Gordon. Bradley on Lucky Wheel is mandatory for competitive SvS."
    },
    8: {
        "gen": 8,
        "unlock_day": 520,
        "infantry": {"name": "Gatot", "source": "Hall of Heroes", "role": "Reflect Damage Frontline"},
        "lancer": {"name": "Hendrik", "source": "Lucky Wheel", "role": "Stun Lancer & Momentum Lead"},
        "marksman": {"name": "Sonya", "source": "Packs / Mystery Shop", "role": "Suppressive Fire Marksman"},
        "wheel_hero": "Hendrik (Lancer)",
        "hoh_hero": "Gatot (Infantry)",
        "summary": "Hendrik, Gatot, Sonya. Hendrik brings rare Lucky Wheel Lancer value."
    },
    9: {
        "gen": 9,
        "unlock_day": 600,
        "infantry": {"name": "Xura", "source": "Packs / Mystery Shop", "role": "Evasion & Defense Tank"},
        "lancer": {"name": "Fred", "source": "Hall of Heroes", "role": "Penetrating Lancer Charge"},
        "marksman": {"name": "Magnus", "source": "Lucky Wheel", "role": "Brutal Critical Artillery"},
        "wheel_hero": "Magnus (Marksman)",
        "hoh_hero": "Fred (Lancer)",
        "summary": "Magnus, Fred, Xura. Magnus on Lucky Wheel delivers devastating backline crits."
    },
    10: {
        "gen": 10,
        "unlock_day": 700,
        "infantry": {"name": "Gregory", "source": "Hall of Heroes", "role": "Heavy Fortress Tank"},
        "lancer": {"name": "Freya", "source": "Packs / Mystery Shop", "role": "Frost Lancer Flanker"},
        "marksman": {"name": "Blanchette", "source": "Lucky Wheel", "role": "PvE & Bear Trap Sniper"},
        "wheel_hero": "Blanchette (Marksman)",
        "hoh_hero": "Gregory (Infantry)",
        "summary": "Blanchette, Gregory, Freya. Blanchette is top-tier for high-tier Bear Trap rallies."
    },
    11: {
        "gen": 11,
        "unlock_day": 800,
        "infantry": {"name": "Rufus", "source": "Hall of Heroes", "role": "Armor Shredding Frontline"},
        "lancer": {"name": "Lloyd", "source": "Packs / Mystery Shop", "role": "Tactical Mobility Lancer"},
        "marksman": {"name": "Eleonora", "source": "Lucky Wheel", "role": "Rapid-Fire Marksman"},
        "wheel_hero": "Eleonora (Marksman)",
        "hoh_hero": "Rufus (Infantry)",
        "summary": "Eleonora, Rufus, Lloyd. Rufus shreds enemy armor while Eleonora dishes burst."
    },
    12: {
        "gen": 12,
        "unlock_day": 870,
        "infantry": {"name": "Hervor", "source": "Hall of Heroes", "role": "Rally Anchor Tank"},
        "lancer": {"name": "Karol", "source": "Packs / Mystery Shop", "role": "Anti-Backline Lancer"},
        "marksman": {"name": "Ligeia", "source": "Lucky Wheel", "role": "Apex Bear Trap DPS"},
        "wheel_hero": "Ligeia (Marksman)",
        "hoh_hero": "Hervor (Infantry)",
        "summary": "Ligeia, Hervor, Karol. Ligeia sets new records in Bear Trap multipliers."
    },
    13: {
        "gen": 13,
        "unlock_day": 951,
        "infantry": {"name": "Gisela", "source": "Lucky Wheel", "role": "Frontline Kinetic Barrier"},
        "lancer": {"name": "Flora", "source": "Packs / Mystery Shop", "role": "Sustained Skirmish Lancer"},
        "marksman": {"name": "Vulcanus", "source": "Hall of Heroes", "role": "Explosive Siege Fire"},
        "wheel_hero": "Gisela (Infantry)",
        "hoh_hero": "Vulcanus (Marksman)",
        "summary": "Gisela, Vulcanus, Flora. Gisela provides supreme frontline survivability."
    },
    14: {
        "gen": 14,
        "unlock_day": 1030,
        "infantry": {"name": "Elif", "source": "Hall of Heroes", "role": "Fortified Bastion Tank"},
        "lancer": {"name": "Dominic", "source": "Packs / Mystery Shop", "role": "Precision Strike Lancer"},
        "marksman": {"name": "Cara", "source": "Lucky Wheel", "role": "Area Suppression Artillery"},
        "wheel_hero": "Cara (Marksman)",
        "hoh_hero": "Elif (Infantry)",
        "summary": "Cara, Elif, Dominic. Cara on Lucky Wheel lays down punishing suppression fire."
    },
    15: {
        "gen": 15,
        "unlock_day": 1115,
        "infantry": {"name": "Hank", "source": "Hall of Heroes", "role": "Apex Damage Mitigation Tank"},
        "lancer": {"name": "Estrella", "source": "Packs / Mystery Shop", "role": "High Lethality Flanker"},
        "marksman": {"name": "Viveca", "source": "Lucky Wheel", "role": "Multi-Target Burst Cannon"},
        "wheel_hero": "Viveca (Marksman)",
        "hoh_hero": "Hank (Infantry)",
        "summary": "Hank, Viveca, Estrella. Hank is an unyielding wall; Viveca delivers devastating wheel DPS."
    },
    16: {
        "gen": 16,
        "unlock_day": 1220,
        "infantry": {"name": "Seigel", "source": "Lucky Wheel", "role": "Reflect Armor & Vanguard Shield"},
        "lancer": {"name": "Ursar", "source": "Hall of Heroes", "role": "Heavy Charge & Stun Lancer"},
        "marksman": {"name": "Aisling", "source": "Packs / Mystery Shop", "role": "Long-Range Siege Sniper"},
        "wheel_hero": "Seigel (Infantry)",
        "hoh_hero": "Ursar (Lancer)",
        "summary": "Seigel, Ursar, Aisling. Seigel on Lucky Wheel counters heavy burst with reflect damage."
    },
    17: {
        "gen": 17,
        "unlock_day": 1280,
        "infantry": {"name": "Aiden", "source": "Lucky Wheel", "role": "Rage Battery & Kinetic Bastion"},
        "lancer": {"name": "Bertha", "source": "Packs / Mystery Shop", "role": "Support Healer & Sustain DPS"},
        "marksman": {"name": "Eleanor", "source": "Hall of Heroes", "role": "45% Armor Shred Artillery"},
        "wheel_hero": "Aiden (Infantry)",
        "hoh_hero": "Eleanor (Marksman)",
        "summary": "Aiden, Bertha, Eleanor. Aiden accelerates squad rage while Eleanor annihilates armor."
    }
}


def estimate_state_launch_date(state_number: int) -> datetime:
    """Estimates the historical launch date of a Whiteout Survival State using calibrated piecewise interpolation."""
    if state_number <= STATE_LAUNCH_ANCHORS[0][0]:
        return STATE_LAUNCH_ANCHORS[0][1]

    for i in range(len(STATE_LAUNCH_ANCHORS) - 1):
        s1, d1 = STATE_LAUNCH_ANCHORS[i]
        s2, d2 = STATE_LAUNCH_ANCHORS[i + 1]
        if s1 <= state_number <= s2:
            ratio = (state_number - s1) / (s2 - s1)
            delta = (d2 - d1).total_seconds()
            return d1 + timedelta(seconds=ratio * delta)

    # Beyond latest anchor (extrapolate using modern cadence of ~0.40 days / ~9.6 hours per state)
    last_s, last_d = STATE_LAUNCH_ANCHORS[-1]
    prev_s, prev_d = STATE_LAUNCH_ANCHORS[-2]
    sec_per_state = (last_d - prev_d).total_seconds() / (last_s - prev_s)
    return last_d + timedelta(seconds=(state_number - last_s) * sec_per_state)


def fetch_live_state_age(state_number: int) -> Tuple[int, datetime, str]:
    """
    Attempts to fetch ground-truth launch date and server age from WhiteoutStats API.
    Falls back seamlessly to calibrated piecewise estimation if unavailable.
    Returns: (age_days, launch_datetime, source_name)
    """
    now_dt = datetime.now()
    now_ts = now_dt.timestamp()

    # Check memory cache
    if state_number in _KINGDOM_CACHE and now_ts < _KINGDOM_CACHE_EXPIRY.get(state_number, 0):
        data = _KINGDOM_CACHE[state_number]
        return data["age_days"], data["launch_datetime"], data["source"]

    # Try live query from WhiteoutStats public API
    try:
        url = f"https://whiteoutstats.com/api/kingdoms/{state_number}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "FrostyBot/2.0 (Whiteout Survival Tactical Assistant)",
                "Accept": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                open_time = body.get("open_time")
                opened_on = body.get("opened_on")
                if open_time:
                    launch_dt = datetime.utcfromtimestamp(open_time)
                    age_days = max(0, (now_dt - launch_dt).days)
                    result = {
                        "age_days": age_days,
                        "launch_datetime": launch_dt,
                        "source": "WhiteoutStats Live API"
                    }
                    _KINGDOM_CACHE[state_number] = result
                    _KINGDOM_CACHE_EXPIRY[state_number] = now_ts + CACHE_TTL_SECONDS
                    return age_days, launch_dt, "WhiteoutStats Live API"
    except Exception as e:
        logger.debug(f"Live state telemetry fallback for S#{state_number}: {e}")

    # Fallback to calibrated anchor interpolation
    launch_dt = estimate_state_launch_date(state_number)
    age_days = max(0, min(3000, (now_dt - launch_dt).days))
    return age_days, launch_dt, "Calibrated Interpolation Engine"


def calculate_state_telemetry(input_val: int, is_state_number: bool = True) -> Dict[str, Any]:
    """
    Calculates State Age, Active Hero Generation, Current Unlocked Heroes,
    Upcoming Hero Generations with Countdown, and Upcoming Milestones.
    """
    now_dt = datetime.now()

    if is_state_number:
        state_number = max(1, input_val)
        age, launch_date, source = fetch_live_state_age(state_number)
    else:
        state_number = None
        age = max(0, min(3000, input_val))
        launch_date = now_dt - timedelta(days=age)
        source = "Direct Day Input"

    # Determine Active Hero Generation
    cur_gen = 1
    for g in sorted(HERO_GENERATIONS.keys(), reverse=True):
        if age >= HERO_GENERATIONS[g]["unlock_day"]:
            cur_gen = g
            break

    current_gen_data = HERO_GENERATIONS[cur_gen]
    unlocked_gens = [g for g in sorted(HERO_GENERATIONS.keys()) if g <= cur_gen]

    # Future Generations Roadmap
    upcoming_gens = []
    for g in sorted(HERO_GENERATIONS.keys()):
        if g > cur_gen:
            unlock_day = HERO_GENERATIONS[g]["unlock_day"]
            days_left = max(1, unlock_day - age)
            months_left = max(1, round(days_left / 30.4))
            upcoming_gens.append({
                "gen": g,
                "unlock_day": unlock_day,
                "days_left": days_left,
                "months_left": months_left,
                "data": HERO_GENERATIONS[g]
            })

    next_gen_info = upcoming_gens[0] if upcoming_gens else None

    # Load Milestones from state_timeline.json
    milestones = []
    timeline_path = "state_timeline.json"
    if os.path.exists(timeline_path):
        try:
            with open(timeline_path, "r", encoding="utf-8") as f:
                tdata = json.load(f)
                for item in tdata:
                    milestones.append((item.get("day", 0), item.get("title", ""), item.get("category", "Event")))
        except Exception:
            pass

    if not milestones:
        # Fallback milestones matching timeline doctrine
        for g, gdata in HERO_GENERATIONS.items():
            milestones.append((gdata["unlock_day"], f"Generation {g} Heroes ({gdata['infantry']['name']}, {gdata['lancer']['name']}, {gdata['marksman']['name']})", "Heroes"))

    unlocked_milestones = [m for m in milestones if age >= m[0]]
    upcoming_milestones = [m for m in milestones if age < m[0]]
    next_m = upcoming_milestones[0] if upcoming_milestones else None

    return {
        "state_number": state_number,
        "is_state_number": is_state_number,
        "age": age,
        "launch_date": launch_date.strftime("%B %d, %Y"),
        "telemetry_source": source,
        "current_gen": cur_gen,
        "current_gen_data": current_gen_data,
        "unlocked_gens": unlocked_gens,
        "next_gen": next_gen_info["gen"] if next_gen_info else None,
        "next_gen_info": next_gen_info,
        "days_to_next_gen": next_gen_info["days_left"] if next_gen_info else None,
        "upcoming_gens": upcoming_gens,
        "unlocked_count": len(unlocked_milestones),
        "total_count": len(milestones),
        "recent_unlocked": [m[1] for m in unlocked_milestones[-3:]],
        "next_milestone": next_m,
        "days_to_next_milestone": (next_m[0] - age) if next_m else None
    }


def format_state_ai_context(state_number: int) -> str:
    """
    Generates a structured, fact-checked markdown dossier of state age and hero progression
    for direct injection into the AI prompt / RAG search context.
    """
    t = calculate_state_telemetry(state_number, is_state_number=True)
    c_data = t["current_gen_data"]

    lines = [
        f"=== OFFICIAL STATE #{state_number} TELEMETRY & HERO DOSSIER ===",
        f"• Server Age: Day ~{t['age']} (Founded: {t['launch_date']} UTC via {t['telemetry_source']})",
        f"• Active Hero Generation: Generation {t['current_gen']} (Unlocked on Day {c_data['unlock_day']})",
        f"• Current Active Generation {t['current_gen']} Heroes:",
        f"  - 🛡️ Infantry: {c_data['infantry']['name']} ({c_data['infantry']['source']}) — {c_data['infantry']['role']}",
        f"  - 🐎 Lancer: {c_data['lancer']['name']} ({c_data['lancer']['source']}) — {c_data['lancer']['role']}",
        f"  - 🏹 Marksman: {c_data['marksman']['name']} ({c_data['marksman']['source']}) — {c_data['marksman']['role']}",
        f"• All Previously Unlocked Generations: Generations 1 through {t['current_gen']} are 100% available in State #{state_number}."
    ]

    if t["upcoming_gens"]:
        lines.append("• Future Hero Generation Roadmap:")
        for up in t["upcoming_gens"][:3]:
            g_num = up["gen"]
            g_dat = up["data"]
            lines.append(
                f"  - Generation {g_num} (Day {up['unlock_day']}, unlocks in ~{up['days_left']} days / ~{up['months_left']} mo): "
                f"🛡️ {g_dat['infantry']['name']} (Infantry), 🐎 {g_dat['lancer']['name']} (Lancer), 🏹 {g_dat['marksman']['name']} (Marksman)"
            )
    else:
        lines.append("• Future Roadmap: All current Whiteout Survival generations (up to Gen 17) are unlocked!")

    return "\n".join(lines)
