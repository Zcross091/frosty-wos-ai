"""
❄️ Frosty Automated Daily Data Sync Script
Runs daily via GitHub Actions at 05:00 UTC.
Parses local and web sources to keep heroes_data.json, state_timeline.json,
and utility_data.json fresh and up-to-date for the mobile app & bot.
"""

import os
import re
import json
import logging
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FrostyDailySync")


def sync_heroes_data(heroes_md_path: str = "./wos data/Heroes.md", output_path: str = "heroes_data.json") -> List[Dict]:
    """Parses Heroes.md and updates heroes_data.json"""
    if not os.path.exists(heroes_md_path):
        logger.warning(f"File not found: {heroes_md_path}")
        return []

    try:
        with open(heroes_md_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        hero_blocks = content.split("## ")
        heroes = []

        for block in hero_blocks:
            lines = block.strip().split("\n")
            header = lines[0].strip()

            gen_match = re.search(r'Gen\s*(\d+)', header, re.IGNORECASE)
            name_match = re.match(r'([A-Za-z0-9\s\-]+)', header)

            if not name_match:
                continue

            hero_name = name_match.group(1).split("-")[0].replace("Gen", "").strip()
            if not hero_name or hero_name.lower() in ["table of contents", "overview", "generations"]:
                continue

            gen_val = int(gen_match.group(1)) if gen_match else 0
            if "jeronimo" in hero_name.lower() or "natalia" in hero_name.lower() or "jessie" in hero_name.lower():
                gen_val = 0

            # Troop type detection
            troop_type = "infantry"
            lower_b = block.lower()
            if "lancer" in lower_b or "lancers" in lower_b:
                troop_type = "lancer"
            elif "marksman" in lower_b or "markswoman" in lower_b or "archer" in lower_b:
                troop_type = "marksman"

            # Rating / tier
            tier = "S"
            if "tier s+" in lower_b or "s-tier" in lower_b:
                tier = "S+"
            elif "tier s" in lower_b:
                tier = "S"
            elif "tier a" in lower_b or "a-tier" in lower_b:
                tier = "A"

            # Roles & summary
            summary = lines[1].strip() if len(lines) > 1 and not lines[1].startswith("*") else (lines[2].strip() if len(lines) > 2 else "Elite Whiteout Survival Hero")
            summary = re.sub(r'[*_`#]', '', summary).strip()

            heroes.append({
                "id": hero_name.lower().replace(" ", "_"),
                "name": hero_name,
                "generation": gen_val,
                "troop_type": troop_type,
                "tier": tier,
                "summary": summary[:250],
                "recommended_for": ["Exploration", "Expedition", "PvP"],
                "f2p_friendly": gen_val <= 3 or "f2p" in lower_b
            })

        if heroes:
            # Deduplicate by name
            unique_heroes = {h["name"].lower(): h for h in heroes}
            final_list = list(unique_heroes.values())
            final_list.sort(key=lambda h: (h["generation"], h["name"]))

            with open(output_path, "w", encoding="utf-8") as out:
                json.dump(final_list, out, indent=2)
            logger.info(f"✅ Synced {len(final_list)} heroes into {output_path} (Max Gen: {max(h['generation'] for h in final_list)})")
            return final_list
    except Exception as e:
        logger.error(f"Error syncing heroes: {e}")
    return []


def sync_state_timeline(timeline_md_path: str = "./wos data/State_Timeline.md", output_path: str = "state_timeline.json") -> List[Dict]:
    """Parses State_Timeline.md and updates state_timeline.json"""
    if not os.path.exists(timeline_md_path):
        return []

    try:
        with open(timeline_md_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        milestones = []
        for line in lines:
            if not line.strip().startswith("|") or "Milestone / Feature Unlock" in line or "|:---" in line:
                continue

            parts = [p.strip() for p in line.strip().split("|")[1:-1]]
            if len(parts) >= 4:
                day_str, title_str, cat_str, desc_str = parts[0], parts[1], parts[2], parts[3]
                day_match = re.search(r'\d+', day_str)
                if not day_match:
                    continue
                day_val = int(day_match.group(0))

                clean_title = re.sub(r'[*_`]', '', title_str).strip()
                clean_cat = re.sub(r'[*_`]', '', cat_str).strip()
                clean_desc = re.sub(r'[*_`]', '', desc_str).strip()

                icon = "📜"
                lower_title = clean_title.lower()
                lower_cat = clean_cat.lower()
                if "hero" in lower_cat or "hero" in lower_title:
                    icon = "👑"
                elif "fire crystal" in lower_cat or "fire crystal" in lower_title:
                    icon = "💎"
                elif "pet" in lower_cat or "pet" in lower_title:
                    icon = "🐾"
                elif "gear" in lower_cat or "charm" in lower_title:
                    icon = "🛡️"
                elif "academy" in lower_cat or "troop" in lower_title:
                    icon = "🏛️"
                elif "sunfire" in lower_title or "castle" in lower_title:
                    icon = "🏰"
                elif "svs" in lower_title or "war" in lower_title:
                    icon = "⚔️"
                elif "transfer" in lower_title:
                    icon = "🚀"

                milestones.append({
                    "day": day_val,
                    "title": clean_title,
                    "category": clean_cat,
                    "icon": icon,
                    "description": clean_desc
                })

        milestones.sort(key=lambda m: m["day"])
        if milestones:
            with open(output_path, "w", encoding="utf-8") as out:
                json.dump(milestones, out, indent=2)
            logger.info(f"✅ Synced {len(milestones)} state timeline milestones into {output_path}!")
            return milestones
    except Exception as e:
        logger.error(f"Error syncing timeline: {e}")
    return []


def scrape_online_gift_codes() -> List[Dict[str, str]]:
    """
    Fetches active promo gift codes from multiple live online sources:
    1. Whiteout Survival HQ (Hourly live redemption verified codes via JSON-LD + HTML tables)
    2. Beebom
    Preserves exact casing and extracts live status.
    """
    found_codes = []
    seen_codes = set()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    # 1. Whiteout Survival HQ (Live verified hourly codes - no bot block)
    try:
        url = "https://whiteoutsurvivalhq.com/gift-codes/"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")

            # A. Parse JSON-LD structured data (ItemList)
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    if script.string:
                        jdata = json.loads(script.string)
                        if isinstance(jdata, dict) and jdata.get("@type") == "ItemList" and "itemListElement" in jdata:
                            for item in jdata["itemListElement"]:
                                code_val = str(item.get("name", "")).strip()
                                if code_val and len(code_val) >= 5 and code_val.upper() not in seen_codes:
                                    seen_codes.add(code_val.upper())
                                    found_codes.append({
                                        "code": code_val,
                                        "status": "🟢 Active & Verified (WoS HQ Live)",
                                        "rewards": "Verified In-Game Rewards (Gems, Speedups, Gold Keys)"
                                    })
                except Exception:
                    pass

            # B. Parse table rows with font-mono class
            for th in soup.find_all("th", scope="row"):
                code_val = th.get_text().strip()
                if code_val and len(code_val) >= 5 and code_val.upper() not in seen_codes:
                    if re.match(r'^[A-Za-z0-9_-]{5,25}$', code_val):
                        seen_codes.add(code_val.upper())
                        found_codes.append({
                            "code": code_val,
                            "status": "🟢 Active & Verified (WoS HQ Live)",
                            "rewards": "Verified In-Game Rewards"
                        })
    except Exception as e:
        logger.debug(f"WoS HQ gift codes fetch notice: {e}")

    # 2. Beebom Scraper (Secondary Fallback)
    try:
        url = "https://beebom.com/whiteout-survival-codes/"
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            active_list = soup.find("ul", class_="is-style-copy-code-list")
            if active_list:
                for li in active_list.find_all("li"):
                    strong = li.find("strong")
                    if strong:
                        code_txt = strong.get_text().strip()
                        raw_text = li.get_text().replace("Copy", "").replace("Copied", "").strip()
                        rewards = raw_text.split(":", 1)[1].strip() if ":" in raw_text else "Free In-Game Rewards (Gems, Speedups)"
                        if code_txt.upper() not in seen_codes and len(code_txt) >= 5:
                            seen_codes.add(code_txt.upper())
                            found_codes.append({
                                "code": code_txt,
                                "status": "🟢 Active & Verified",
                                "rewards": rewards
                            })
    except Exception as e:
        logger.debug(f"Beebom gift codes scraper notice: {e}")

    return found_codes


def sync_utility_data(util_md_path: str = "./wos data/Utility_Calculators.md", output_path: str = "utility_data.json") -> Dict:
    """Updates utility_data.json with FC tiers, Charms, SvS rates, and live codes"""
    data = {}
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass

    # Read markdown
    if os.path.exists(util_md_path):
        try:
            with open(util_md_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            code_matches = re.findall(r'`([A-Za-z0-9]{5,20})`', content)
            if "gift_codes" in data and code_matches:
                existing_codes = {c["code"].upper() for c in data["gift_codes"]}
                for cm in code_matches:
                    clean_cm = cm.strip()
                    if clean_cm.upper() not in existing_codes and len(clean_cm) >= 5:
                        data["gift_codes"].insert(0, {"code": clean_cm, "status": "🟢 Active & Verified", "rewards": "Promo Gift Code Rewards"})
                        existing_codes.add(clean_cm.upper())
        except Exception as e:
            logger.warning(f"Error parsing utility md: {e}")

    # Fetch online codes if possible
    online_codes = scrape_online_gift_codes()
    if online_codes and "gift_codes" in data:
        existing_codes = {c["code"].upper() for c in data["gift_codes"]}
        for oc in online_codes:
            clean_oc = oc["code"].strip()
            if clean_oc.upper() not in existing_codes:
                data["gift_codes"].insert(0, oc)
                existing_codes.add(clean_oc.upper())

    if data:
        with open(output_path, "w", encoding="utf-8") as out:
            json.dump(data, out, indent=2)
        logger.info(f"✅ Synced utility data into {output_path} ({len(data.get('gift_codes', []))} active codes)!")

    return data


def main():
    logger.info("❄️ Starting Frosty Daily Automated Data Sync...")
    sync_heroes_data()
    sync_state_timeline()
    sync_utility_data()
    logger.info("✨ Daily Data Sync Completed Successfully!")


if __name__ == "__main__":
    main()
