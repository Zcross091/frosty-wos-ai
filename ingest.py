import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
import chromadb
import os
import time

# 1. Setup ChromaDB (The persistent library for your bot)
chroma_client = chromadb.PersistentClient(path="./frosty_brain")
collection = chroma_client.get_or_create_collection(name="wos_knowledge")

def get_all_urls(source):
    """Recursively finds all guide URLs from a local file or a live URL."""
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

        # Case 1: Sitemap Index (Points to other XML files)
        sitemaps = root.findall('.//ns:sitemap/ns:loc', namespace)
        if sitemaps:
            for s in sitemaps:
                print(f"📂 Diving into sub-sitemap: {s.text}")
                urls.extend(get_all_urls(s.text))
        
        # Case 2: Standard Sitemap (Points to actual web pages)
        locations = root.findall('.//ns:url/ns:loc', namespace)
        for loc in locations:
            urls.append(loc.text)

    except Exception as e:
        print(f"⚠️ Error parsing {source}: {e}")
    
    return list(set(urls)) # Remove duplicates

def run_ingestion(source, site_label):
    all_links = get_all_urls(source)
    
    # Filter for quality: We want guides, heroes, buildings, and events
    target_keywords = ['/hero', '/event', '/building', '/expert', '/pet', '/gear', '/guide']
    target_urls = [u for u in all_links if any(k in u.lower() for k in target_keywords)]
    
    print(f"🚀 Found {len(target_urls)} relevant pages for {site_label}. Starting scrape...")
    
    for i, url in enumerate(target_urls):
        try:
            res = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # ✅ FIXED NOISE REMOVAL (Copilot's optimized fix)
            # This removes tags (nav, footer) AND classes (.sidebar) correctly
            noise_selectors = ['nav', 'footer', 'script', 'style', 'aside', '.sidebar', '.ad-container', 'header', '.menu']
            for selector in noise_selectors:
                for junk in soup.select(selector):
                    junk.decompose()
            
            # Get only the main content text
            clean_text = soup.get_text(separator=' ', strip=True)
            
            # Store in the "Brain"
            collection.add(
                documents=[clean_text],
                ids=[f"{site_label}_{i}"],
                metadatas=[{"source": url, "site": site_label}]
            )
            
            if i % 10 == 0:
                print(f"✅ Progress: {i}/{len(target_urls)} pages learned.")
            
            time.sleep(0.3)
        except Exception as e:
            print(f"❌ Failed to scrape {url}: {e}")

def ingest_local_files(folder_path):
    """Option A: Ingest your personal strategies from wos_data folder."""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"📂 Created {folder_path} folder. Drop your .txt files there!")
        return

    for filename in os.listdir(folder_path):
        if filename.endswith(".txt") or filename.endswith(".md"):
            with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as f:
                collection.add(
                    documents=[f.read()],
                    ids=[f"personal_{filename}"],
                    metadatas=[{"source": filename, "type": "personal_strategy"}]
                )
                print(f"📒 Ingested personal strategy: {filename}")

# --- EXECUTION ---
if __name__ == "__main__":
    # 1. Scrape wos-guide.com (using your local sitemap.xml)
    if os.path.exists('sitemap.xml'):
        run_ingestion('sitemap.xml', 'wos_guide')

    # 2. Scrape whiteoutsurvival.wiki (using the live index URL)
    run_ingestion('https://www.whiteoutsurvival.wiki/sitemap.xml', 'wos_wiki')

    # 3. Ingest your custom strategies (Option A)
    ingest_local_files('wos_data')

    print("\n✨ SYSTEM: Frosty's brain is fully synced and ready for Discord!")