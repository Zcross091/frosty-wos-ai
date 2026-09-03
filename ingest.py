"""
Frosty Ingestion Engine
Performs semantic, structure-aware markdown parsing and web wiki ingestion for ChromaDB.
"""

import os
import re
import time
import argparse
import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple, Optional
import requests
from bs4 import BeautifulSoup
import chromadb
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FrostyAI.Ingest")

DB_PATH = os.getenv("CHROMA_PATH", "./frosty_brain")
COLLECTION_NAME = "wos_knowledge"


def get_chroma_collection(db_path: str = DB_PATH):
    client = chromadb.PersistentClient(path=db_path)
    return client.get_or_create_collection(name=COLLECTION_NAME)


def recursive_chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> List[str]:
    """
    Splits text into chunks respecting paragraph and line breaks with overlap.
    """
    text = text.strip()
    if len(text) <= max_chars:
        return [text] if text else []

    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(current_chunk) + len(p) + 2 <= max_chars:
            current_chunk = f"{current_chunk}\n\n{p}" if current_chunk else p
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # If paragraph itself is huge, split by lines or sentences
            if len(p) > max_chars:
                lines = p.split("\n")
                sub_chunk = ""
                for line in lines:
                    if len(sub_chunk) + len(line) + 1 <= max_chars:
                        sub_chunk = f"{sub_chunk}\n{line}" if sub_chunk else line
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk.strip())
                        sub_chunk = line
                if sub_chunk:
                    current_chunk = sub_chunk
                else:
                    current_chunk = ""
            else:
                current_chunk = p

    if current_chunk:
        chunks.append(current_chunk.strip())

    # Add sliding overlap if needed
    final_chunks = []
    for i, c in enumerate(chunks):
        if i > 0 and overlap > 0 and len(chunks[i-1]) > overlap:
            tail = chunks[i-1][-overlap:]
            final_chunks.append(f"...{tail}\n{c}")
        else:
            final_chunks.append(c)

    return final_chunks


def parse_heroes_markdown(content: str) -> List[Dict]:
    """
    Parses Heroes.md by section and hero headers.
    """
    chunks = []
    # Split by major generation headers or hero headers
    lines = content.splitlines()
    current_gen = "Gen 0"
    current_hero = ""
    current_troop = ""
    current_block = []

    for line in lines:
        # Detect generation header (e.g. ### Gen 1, ### Rare, # Gen 8)
        gen_match = re.search(r'#{1,4}\s*(Rare|Epic|Gen\s*\d+)', line, re.IGNORECASE)
        if gen_match:
            current_gen = gen_match.group(1).title()

        # Detect hero header (e.g. 🔨 Smith – Rare Heroes, 🪓 Eugene, Jeronimo, etc.)
        hero_match = re.search(r'([A-Za-z0-9\s]+)\s*–\s*(Rare|Epic|Gen\s*\d+)?\s*(Infantry|Lancer|Marksman)?', line)
        if hero_match and (line.startswith("#") or any(icon in line for icon in ["🔨", "🪓", "🏹", "⚔️", "🛡️", "👑"])):
            # Save previous block if it has substance
            if current_block and len("\n".join(current_block).strip()) > 80:
                block_text = "\n".join(current_block).strip()
                sub_chunks = recursive_chunk_text(block_text, max_chars=1400)
                for sc in sub_chunks:
                    chunks.append({
                        "text": sc,
                        "metadata": {
                            "category": "hero_guide",
                            "hero_name": current_hero if current_hero else "General",
                            "generation": current_gen,
                            "troop_type": current_troop,
                            "source": "Heroes.md"
                        }
                    })
                current_block = []

            # Extract hero name
            name_candidate = line.split("–")[0].strip()
            # Clean icons
            clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name_candidate).strip()
            if clean_name:
                current_hero = clean_name.split()[0].title() if clean_name.split() else clean_name.title()
            
            if "infantry" in line.lower():
                current_troop = "Infantry"
            elif "lancer" in line.lower():
                current_troop = "Lancer"
            elif "marksman" in line.lower() or "sharpshooter" in line.lower():
                current_troop = "Marksman"

        current_block.append(line)

    if current_block:
        block_text = "\n".join(current_block).strip()
        sub_chunks = recursive_chunk_text(block_text, max_chars=1400)
        for sc in sub_chunks:
            chunks.append({
                "text": sc,
                "metadata": {
                    "category": "hero_guide",
                    "hero_name": current_hero if current_hero else "General",
                    "generation": current_gen,
                    "troop_type": current_troop,
                    "source": "Heroes.md"
                }
            })

    return chunks


def parse_events_markdown(content: str) -> List[Dict]:
    """
    Parses Event Information.md into structured event cards.
    """
    chunks = []
    lines = content.splitlines()
    current_event = "General Event"
    current_block = []

    for line in lines:
        # Detect event start header like `# \# Crazy Joe`, `# \# Frost Fire Mine`, etc.
        event_match = re.search(r'#{1,3}\s*\\?#?\s*([A-Za-z0-9\s]+)', line)
        if event_match and any(keyword in line.lower() for keyword in ["joe", "mine", "foundry", "bear", "castle", "transfer", "svs", "fortress", "event"]):
            if current_block and len("\n".join(current_block).strip()) > 80:
                block_text = "\n".join(current_block).strip()
                sub_chunks = recursive_chunk_text(block_text, max_chars=1400)
                for sc in sub_chunks:
                    chunks.append({
                        "text": sc,
                        "metadata": {
                            "category": "event_guide",
                            "event_name": current_event,
                            "source": "Event Information.md"
                        }
                    })
                current_block = []

            ev_title = event_match.group(1).strip()
            clean_ev = re.sub(r'[^a-zA-Z0-9\s]', '', ev_title).strip()
            if clean_ev:
                current_event = clean_ev.title()

        current_block.append(line)

    if current_block:
        block_text = "\n".join(current_block).strip()
        sub_chunks = recursive_chunk_text(block_text, max_chars=1400)
        for sc in sub_chunks:
            chunks.append({
                "text": sc,
                "metadata": {
                    "category": "event_guide",
                    "event_name": current_event,
                    "source": "Event Information.md"
                }
            })

    return chunks


def parse_experts_markdown(content: str) -> List[Dict]:
    """
    Parses Experts.md into Dawn Academy expert records.
    """
    chunks = []
    lines = content.splitlines()
    current_expert = "General Expert"
    current_block = []

    for line in lines:
        expert_match = re.search(r'#{1,4}\s*([A-Za-z0-9\s]+)\s*–\s*Gen\s*(\d+)?\s*Expert', line, re.IGNORECASE)
        if expert_match or any(icon in line for icon in ["👩‍💼", "🐻", "🏟️", "⚔️", "🤝", "🔥", "🏆", "🚚", "⛏️"]):
            if current_block and len("\n".join(current_block).strip()) > 80:
                block_text = "\n".join(current_block).strip()
                sub_chunks = recursive_chunk_text(block_text, max_chars=1400)
                for sc in sub_chunks:
                    chunks.append({
                        "text": sc,
                        "metadata": {
                            "category": "expert_guide",
                            "expert_name": current_expert,
                            "source": "Experts.md"
                        }
                    })
                current_block = []

            clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', line.split("–")[0]).strip()
            if clean_name:
                current_expert = clean_name.split()[0].title() if clean_name.split() else clean_name.title()

        current_block.append(line)

    if current_block:
        block_text = "\n".join(current_block).strip()
        sub_chunks = recursive_chunk_text(block_text, max_chars=1400)
        for sc in sub_chunks:
            chunks.append({
                "text": sc,
                "metadata": {
                    "category": "expert_guide",
                    "expert_name": current_expert,
                    "source": "Experts.md"
                }
            })

    return chunks


def ingest_local_markdown_folder(folder_path: str = "./wos data", collection = None) -> int:
    """Processes local markdown strategy guides with semantic metadata tagging."""
    if collection is None:
        collection = get_chroma_collection()

    if not os.path.exists(folder_path):
        logger.warning(f"Local folder {folder_path} does not exist.")
        return 0

    total_added = 0
    logger.info(f"📂 Ingesting local markdown files from {folder_path}...")

    for filename in sorted(os.listdir(folder_path)):
        if not (filename.endswith(".md") or filename.endswith(".txt")):
            continue

        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        parsed_chunks = []
        if "hero" in filename.lower():
            parsed_chunks = parse_heroes_markdown(content)
        elif "event" in filename.lower():
            parsed_chunks = parse_events_markdown(content)
        elif "expert" in filename.lower():
            parsed_chunks = parse_experts_markdown(content)
        else:
            # General markdown
            text_blocks = recursive_chunk_text(content, max_chars=1200)
            for tb in text_blocks:
                parsed_chunks.append({
                    "text": tb,
                    "metadata": {"category": "general_guide", "source": filename}
                })

        # Add to ChromaDB in batches
        docs = []
        ids = []
        metadatas = []
        clean_file_prefix = re.sub(r'[^a-zA-Z0-9]', '_', filename)

        for idx, item in enumerate(parsed_chunks):
            doc_id = f"local_{clean_file_prefix}_{idx}"
            docs.append(item["text"])
            ids.append(doc_id)
            metadatas.append(item["metadata"])

            if len(docs) >= 50:
                collection.upsert(documents=docs, ids=ids, metadatas=metadatas)
                total_added += len(docs)
                docs, ids, metadatas = [], [], []

        if docs:
            collection.upsert(documents=docs, ids=ids, metadatas=metadatas)
            total_added += len(docs)

        logger.info(f"✅ Ingested {len(parsed_chunks)} semantic chunks from: {filename}")

    return total_added


NON_ENGLISH_PREFIXES = [
    '/tw/', '/zh/', '/cn/', '/ja/', '/jp/', '/ko/', '/kr/', '/fr/', '/es/',
    '/pt/', '/de/', '/ru/', '/ar/', '/it/', '/th/', '/vi/', '/id/', '/tr/',
    '/pl/', '/nl/', '/ro/', '/el/', '/hu/', '/cs/', '/uk/', '/fa/'
]


def is_clean_english_url(url: str) -> bool:
    """Checks if a URL is an English-only document and not a foreign translation mirror."""
    u = url.lower()
    if any(lang in u for lang in NON_ENGLISH_PREFIXES):
        return False
    try:
        url.encode('ascii')
    except UnicodeEncodeError:
        return False
    return True


def get_all_urls_from_sitemap(source: str) -> List[str]:
    """Finds all clean English URLs inside a local sitemap file or live URL."""
    urls = []
    try:
        if os.path.exists(source):
            with open(source, 'rb') as f:
                content = f.read()
        else:
            res = requests.get(source, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            content = res.content

        root = ET.fromstring(content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        sitemaps = root.findall('.//ns:sitemap/ns:loc', namespace)
        if sitemaps:
            for s in sitemaps:
                if is_clean_english_url(s.text):
                    urls.extend(get_all_urls_from_sitemap(s.text))

        locations = root.findall('.//ns:url/ns:loc', namespace)
        for loc in locations:
            if is_clean_english_url(loc.text):
                urls.append(loc.text)
    except Exception as e:
        logger.warning(f"Sitemap parsing notice ({source}): {e}")
    return list(set(urls))


def run_web_ingestion(source: str, site_label: str, collection = None) -> int:
    """Scrapes and chunks English web content with checkpointing."""
    if collection is None:
        collection = get_chroma_collection()

    all_links = get_all_urls_from_sitemap(source)
    target_keywords = ['/hero', '/event', '/building', '/expert', '/pet', '/gear', '/guide', '/lineup']
    
    # Filter target keywords AND ensure clean English URLs
    target_urls = [u for u in all_links if any(k in u.lower() for k in target_keywords) and is_clean_english_url(u)]
    total_targets = len(target_urls)

    if not target_urls:
        logger.info(f"No matching English target URLs found in {source}")
        return 0

    logger.info(f"🌐 Scraping {total_targets} verified English pages for {site_label}...")
    added = 0

    for i, url in enumerate(target_urls):
        try:
            if (i + 1) % 10 == 0 or i == 0 or (i + 1) == total_targets:
                logger.info(f"📑 [{site_label}] Progress: ({i+1}/{total_targets}) - {url}")

            res = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')

            for junk in soup.select('nav, footer, script, style, aside, .sidebar, .ad-container, header, .menu'):
                junk.decompose()

            clean_text = soup.get_text(separator=' ', strip=True)
            page_chunks = recursive_chunk_text(clean_text, max_chars=1200)

            for chunk_idx, chunk in enumerate(page_chunks):
                collection.upsert(
                    documents=[chunk],
                    ids=[f"{site_label}_{i}_chunk_{chunk_idx}"],
                    metadatas=[{"source": url, "site": site_label, "category": "web_guide"}]
                )
                added += 1

            time.sleep(0.15)
        except Exception as e:
            logger.debug(f"Skipped page {url}: {e}")

    logger.info(f"✅ English web ingestion complete for {site_label}: {added} chunks.")
    return added


import json


def auto_sync_heroes_data_json(heroes_md_path: str = "./wos data/Heroes.md", output_path: str = "heroes_data.json") -> List[Dict]:
    """
    Parses Heroes.md and generates an up-to-date heroes_data.json file automatically.
    This guarantees the mobile app, Hero Codex, and web frontend stay 100% in sync
    with every future generation and ingestion.
    """
    if not os.path.exists(heroes_md_path):
        logger.warning(f"Heroes markdown not found at {heroes_md_path}")
        return []

    try:
        with open(heroes_md_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Unlock day base references
        unlock_days = {
            1: 0, 2: 40, 3: 120, 4: 180, 5: 250, 6: 320, 7: 400,
            8: 480, 9: 550, 10: 620, 11: 690, 12: 760, 13: 830,
            14: 900, 15: 960, 16: 1160, 17: 1240
        }

        # Find all generation sections
        gen_sections = re.findall(r'(#{2,4}\s*Gen\s*(\d+).*?)(?=(?:#{2,4}\s*Gen\s*\d+|\Z))', content, re.DOTALL | re.IGNORECASE)
        
        extracted_gens = {}
        for full_sec, gen_num_str in gen_sections:
            gen_num = int(gen_num_str)
            if gen_num in extracted_gens:
                continue

            # Extract Infantry, Lancer, Marksman
            inf_match = re.search(r'•\s*\*\*([A-Za-z0-9\s]+)\*\*.*?Infantry', full_sec, re.IGNORECASE) or \
                        re.search(r'([A-Za-z0-9\s]+)\s*–\s*.*?(?:Infantry)', full_sec, re.IGNORECASE) or \
                        re.search(r'🛡️\s*([A-Za-z0-9\s]+)', full_sec)
            
            lan_match = re.search(r'•\s*\*\*([A-Za-z0-9\s]+)\*\*.*?Lancer', full_sec, re.IGNORECASE) or \
                        re.search(r'([A-Za-z0-9\s]+)\s*–\s*.*?(?:Lancer)', full_sec, re.IGNORECASE) or \
                        re.search(r'🐎\s*([A-Za-z0-9\s]+)', full_sec)

            mar_match = re.search(r'•\s*\*\*([A-Za-z0-9\s]+)\*\*.*?(?:Marksman|Sharpshooter)', full_sec, re.IGNORECASE) or \
                        re.search(r'([A-Za-z0-9\s]+)\s*–\s*.*?(?:Marksman|Sharpshooter)', full_sec, re.IGNORECASE) or \
                        re.search(r'🏹\s*([A-Za-z0-9\s]+)', full_sec)

            inf_name = inf_match.group(1).strip() if inf_match else ""
            lan_name = lan_match.group(1).strip() if lan_match else ""
            mar_name = mar_match.group(1).strip() if mar_match else ""

            # Clean hero names
            inf_name = re.sub(r'[^a-zA-Z\s]', '', inf_name).split()[0].title() if inf_name else ""
            lan_name = re.sub(r'[^a-zA-Z\s]', '', lan_name).split()[0].title() if lan_name else ""
            mar_name = re.sub(r'[^a-zA-Z\s]', '', mar_name).split()[0].title() if mar_name else ""

            # Compute unlock day
            if gen_num in unlock_days:
                day = unlock_days[gen_num]
            else:
                day = 1240 + (gen_num - 17) * 80

            # Advice extraction
            adv_match = re.search(r'(?:F2P vs P2W|Shard Advice|Recommended build order).*?:?\s*([^\n\r]+)', full_sec, re.IGNORECASE)
            advice = adv_match.group(1).strip() if adv_match else f"Generation {gen_num} core lineup: {inf_name} (Infantry), {lan_name} (Lancer), {mar_name} (Marksman)."

            extracted_gens[gen_num] = {
                "gen": gen_num,
                "label": f"Gen {gen_num}",
                "unlockDay": day,
                "infantry": inf_name or f"Hero-Inf-{gen_num}",
                "lancer": lan_name or f"Hero-Lan-{gen_num}",
                "marksman": mar_name or f"Hero-Mar-{gen_num}",
                "wheelHero": f"{inf_name} (Infantry)" if inf_name else f"Gen {gen_num} Wheel",
                "advice": advice
            }

        # Sort descending by generation number (Gen 17 -> Gen 1)
        sorted_gens = [extracted_gens[g] for g in sorted(extracted_gens.keys(), reverse=True)]

        if sorted_gens:
            with open(output_path, "w", encoding="utf-8") as out:
                json.dump(sorted_gens, out, indent=2)
            logger.info(f"💾 Automatically synced {len(sorted_gens)} generations into {output_path}!")
            return sorted_gens
    except Exception as e:
        logger.warning(f"Error auto-syncing heroes_data.json: {e}")
    return []


def run_full_reindex(local_only: bool = False, clean: bool = False) -> int:
    """Entry point for both CLI and Discord /reindex command."""
    client = chromadb.PersistentClient(path=DB_PATH)
    
    if clean:
        try:
            client.delete_collection(name=COLLECTION_NAME)
            logger.info("🗑️ Reset existing ChromaDB collection for a clean re-index.")
        except Exception:
            pass
            
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    logger.info(f"🚀 Starting ingestion into ChromaDB (Path: {DB_PATH})...")

    # Step 1: Auto-generate fresh heroes_data.json for mobile app and web codex
    auto_sync_heroes_data_json()

    # Step 2: Ingest local structured guides
    local_count = ingest_local_markdown_folder("./wos data", collection=collection)

    # Step 3: Ingest root sitemap if exists
    web_count = 0
    if not local_only:
        if os.path.exists("sitemap.xml"):
            web_count += run_web_ingestion("sitemap.xml", "wos_guide", collection=collection)
        
        # Live sitemap
        try:
            web_count += run_web_ingestion("https://www.whiteoutsurvival.wiki/sitemap.xml", "wos_wiki", collection=collection)
        except Exception as e:
            logger.warning(f"Live wiki ingestion skipped: {e}")

    total_chunks = collection.count()
    logger.info(f"✨ Ingestion complete! Total chunks in database: {total_chunks}")
    return total_chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Frosty AI Knowledge Ingestion")
    parser.add_argument("--local-only", action="store_true", help="Ingest only local wos data folder without web crawling")
    parser.add_argument("--clean", action="store_true", help="Wipe database before ingesting for a completely clean index")
    args = parser.parse_args()

    run_full_reindex(local_only=args.local_only, clean=args.clean)


