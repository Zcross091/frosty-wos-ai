import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
import chromadb
import os
import time

# 1. Connect to Frosty's persistent database folder
chroma_client = chromadb.PersistentClient(path="./frosty_brain")
collection = chroma_client.get_or_create_collection(name="wos_knowledge")

def chunk_text(text, chunk_size=2000):
    """Splits text content into character blocks under 2000 characters."""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def get_all_urls(source):
    """Finds all links inside a local sitemap file or live URL."""
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
                urls.extend(get_all_urls(s.text))
        
        locations = root.findall('.//ns:url/ns:loc', namespace)
        for loc in locations:
            urls.append(loc.text)
    except Exception as e:
        print(f"⚠️ Error parsing sitemap layout ({source}): {e}")
    return list(set(urls))

def get_indexed_urls(site_label):
    """Queries ChromaDB to see which URLs have already been indexed for a site."""
    try:
        # Fetch existing metadata entries matching this site source label
        results = collection.get(where={"site": site_label}, include=["metadatas"])
        if results and results["metadatas"]:
            return set(meta["source"] for meta in results["metadatas"] if "source" in meta)
    except Exception:
        pass
    return set()

def run_web_ingestion(source, site_label):
    """Scrapes, cleans, chunks, and inputs web content with checkpoint skipping."""
    all_links = get_all_urls(source)
    target_keywords = ['/hero', '/event', '/building', '/expert', '/pet', '/gear', '/guide']
    target_urls = [u for u in all_links if any(k in u.lower() for k in target_keywords)]
    total_targets = len(target_urls)
    
    print(f"🚀 Analyzing {total_targets} pages for {site_label}...")
    
    # Check existing data to skip previously completed work
    indexed_urls = get_indexed_urls(site_label)
    print(f"ℹ️ Found {len(indexed_urls)} URLs already present in database.")
    
    for i, url in enumerate(target_urls):
        if url in indexed_urls:
            # Checkpoint Skip Logic
            if (i + 1) % 50 == 0 or i + 1 == total_targets:
                print(f"⏩ [{site_label}] Fast-forwarding: Checked {i+1}/{total_targets} links...")
            continue
            
        try:
            # Active tracking print statement so SSH connections never idle out!
            print(f"📑 [{site_label}] Learning page {i+1}/{total_targets}: {url}")
            
            res = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            
            for junk in soup.select('nav, footer, script, style, aside, .sidebar, .ad-container, header, .menu'):
                junk.decompose()
            
            clean_text = soup.get_text(separator=' ', strip=True)
            page_chunks = chunk_text(clean_text, chunk_size=2000)
            
            for chunk_idx, chunk in enumerate(page_chunks):
                collection.add(
                    documents=[chunk],
                    ids=[f"{site_label}_{i}_chunk_{chunk_idx}"],
                    metadatas=[{"source": url, "site": site_label}]
                )
            time.sleep(0.3)
        except Exception as e:
            print(f"❌ Failed to scrape {url}: {e}")

def ingest_local_markdown_folder(folder_path):
    """Processes local sub-folder strategy notes with fallback protections."""
    if not os.path.exists(folder_path):
        print(f"❌ Subfolder {folder_path} does not exist.")
        return
    for filename in os.listdir(folder_path):
        if filename.endswith(".md") or filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                text_chunks = chunk_text(content, chunk_size=2000)
                for chunk_idx, chunk in enumerate(text_chunks):
                    collection.add(
                        documents=[chunk],
                        ids=[f"local_{filename}_chunk_{chunk_idx}"],
                        metadatas=[{"source": filename, "site": "local_data"}]
                    )
            print(f"✅ Processed Local Folder Document: {filename}")

# --- Master Execution Plan ---
if __name__ == "__main__":
    # Part 1: Handle your markdown documentation folder first
    print("--- Ingesting Local Markdown Strategy Folders ---")
    ingest_local_markdown_folder('./wos data')

    # Part 2: Handle your original root directory sitemap file
    print("\n--- Processing Root Directory Sitemaps ---")
    if os.path.exists('sitemap.xml'):
        run_web_ingestion('sitemap.xml', 'wos_guide')
    else:
        print("ℹ️ No local sitemap.xml detected in root folder.")

    # Part 3: Handle the remote live sitemap
    print("\n--- Processing Live Web Wiki Sitemaps ---")
    run_web_ingestion('https://www.whiteoutsurvival.wiki/sitemap.xml', 'wos_wiki')

    print(f"\n✨ COMPLETE: Frosty's brain currently contains {collection.count()} active indexed chunks!")
