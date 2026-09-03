"""
Frosty Knowledge Base & Hybrid RAG Retrieval Engine
Handles semantic search, entity recognition, metadata filtering, and fallback game knowledge.
"""

import os
import re
import logging
from typing import List, Dict, Set, Optional, Tuple

logger = logging.getLogger("FrostyAI.KnowledgeBase")

# Core Whiteout Survival Game Knowledge (Always available)
CORE_WOS_KNOWLEDGE = """
=== CORE WHITEOUT SURVIVAL MECHANICS & DOCTRINE ===
1. HERO LINEUPS & FORMATIONS:
   - Lineup Structure: A standard squad/march has 3 Hero slots: 1 Leader (Captain) + 2 Deputies.
   - Troop Roles:
     * Infantry: The frontline shield. Absorbs damage. If infantry falls, Lancers and Marksmen die rapidly.
     * Lancers: Flankers & mid-range DPS. Strong vs Marksmen.
     * Marksmen (Sharpshooters): High backline DPS / damage dealers. High fragility.
   - Standard Troop Ratios:
     * Standard PvP / Balanced: 50% Infantry / 20% Lancer / 30% Marksman (50/20/30).
     * Heavy Defense / Castle Defense: 60% Infantry / 20% Lancer / 20% Marksman (60/20/20).
     * High Burst Attack: 40% Infantry / 10% Lancer / 50% Marksman (40/10/50 or '4-1-1').
     * Bear Trap / Pure PvE Damage: 10% Infantry / 10% Lancer / 80% Marksman (10/10/80).

2. RALLY MECHANICS & JOINER SKILLS (CRITICAL):
   - Only the TOP 4 rally joiners' first expedition skill (Top-Right Skill) buff the entire rally!
   - Best Rally Joiner Heroes:
     * Jessie: "Inspire" (+25% Damage Dealt for the entire rally at skill Lv. 5). Top Tier joiner.
     * Jeronimo: "Legion's Might" (+15% Attack / Damage).
     * Patrick: "First Aid" (+15% HP for rally defenders/attackers). Essential for defense.
     * Sergey: "Iron Defense" (-20% Damage Taken). Top Tier defense joiner.
     * Seo-yoon: "Rallying Song" (+20% Attack buff). Excellent for Bear Trap & PvE.
     * Gina: March speed and stamina reduction (great for beasts/rally travel).
   - Joiners should send Jessie, Jeronimo, Patrick, or Seo-yoon as their 1st hero when joining rallies!

3. BEAR TRAP STRATEGY:
   - Trap Duration: 30 minutes. Run as many rallies as possible.
   - Ratios: 10/10/80 or 0/20/80 (heavy Marksmen).
   - Leaders: Use highest DPS heroes (e.g., Flint/Alonso/Mia/Lynn/Wayne/Bradley/Magnus depending on Gen).
   - Joiners: Every joiner MUST send Jessie or Seo-yoon as primary hero to stack the 25% and 20% damage buffs!

4. CRAZY JOE DEFENSE:
   - Joe attacks alliance cities in 20 waves over ~40 minutes.
   - Headquarters waves: Wave 10 and Wave 20 are massive attacks on the Alliance HQ!
   - Troop Rule: NEVER send Marksmen to reinforce allies or HQ. Keep Marksmen at home in your own city barricade! Send only Infantry & Lancers to reinforce allies and HQ.
   - Empty city tactic: Send your troops out to reinforce online alliance members so your city gives points while being defended.

5. DAWN ACADEMY EXPERTS:
   - Unlocked at Furnace Lv 25 + Fire Crystal 1 (~Day 150+).
   - Strategic Pausing: Never level experts blindly. Pause at key breakpoints (Level 10, 20, 30) where talent boosts spike.
   - F2P Priority: Agnes (Construction/Research) -> Cyrille (Healing/Training) -> Baldur (Event economy).
   - P2W / Combat Priority: Romulus, Valeria, Fabian for massive combat stats.
"""

# Recognized Heroes across all Generations
KNOWN_HEROES = [
    # Rare
    "smith", "eugene", "charlie", "cloris",
    # Epic
    "jessie", "bahiti", "sergey", "gina", "patrick", "walis", "jasser", "ling",
    # Gen 1
    "jeronimo", "natalia", "zinman", "molly",
    # Gen 2
    "flint", "alonso", "philly",
    # Gen 3
    "mia", "logan", "greg",
    # Gen 4
    "lynn", "hector", "ahmose",
    # Gen 5
    "gwen", "norah", "wayne",
    # Gen 6
    "renee", "hendrik", "hendrick",
    # Gen 7
    "bradley", "edith", "gordon",
    # Gen 8
    "sonya", "reina", "gatot",
    # Gen 9
    "magnus", "blanche", "luke",
    # Gen 10
    "xylona", "fred", "gregory",
    # Gen 11
    "rufus", "nicole", "bern",
    # Gen 12
    "anson", "eleanor", "lloyd",
    # Gen 13
    "freyja", "eric", "morgan",
    # Gen 14
    "kai", "varg", "evelyn",
    # Gen 15
    "alistair", "astrid", "cedric", "hank", "viveca", "estrella",
    # Gen 16
    "seigel", "aisling", "ursar", "gerald", "maeve", "rowen",
    # Gen 17
    "aiden", "bertha", "eleanor"
]

KNOWN_EVENTS = [
    "crazy joe", "bear trap", "foundry battle", "foundry", "frostfire mine", "frostfire",
    "sunfire castle", "sunfire", "castle battle", "state transfer", "transfer",
    "state of power", "svs", "fortress", "stronghold", "canyon clash", "alliance championship",
    "mercenary prestige", "gina's revenge", "fishing"
]

KNOWN_EXPERTS = [
    "agnes", "cyrille", "holger", "romulus", "baldur", "fabian", "valeria", "ronne", "kathy"
]


class KnowledgeBase:
    def __init__(self, db_path: str = "./frosty_brain"):
        self.db_path = db_path
        self.chroma_client = None
        self.collection = None
        self.known_heroes = set(KNOWN_HEROES)
        self.max_generation = 17
        self._init_db()
        self.reload_dynamic_entities()

    def _init_db(self):
        try:
            import chromadb
            self.chroma_client = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.chroma_client.get_or_create_collection(name="wos_knowledge")
            logger.info(f"Connected to ChromaDB at {self.db_path} (Chunks: {self.collection.count()})")
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}. Running with core fallback knowledge.")
            self.collection = None

    def reload_dynamic_entities(self):
        """Dynamically scans heroes_data.json to keep heroes and max generation live without restarts."""
        self.known_heroes = set(KNOWN_HEROES)
        json_path = "heroes_data.json"
        if os.path.exists(json_path):
            try:
                import json
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        g = item.get("gen", 0)
                        if isinstance(g, int) and g > self.max_generation:
                            self.max_generation = g
                        for key in ["infantry", "lancer", "marksman"]:
                            h_name = item.get(key, "").strip().lower()
                            if h_name:
                                clean_h = re.sub(r'[^a-z0-9]', '', h_name.split()[0])
                                if clean_h:
                                    self.known_heroes.add(clean_h)
            except Exception as e:
                logger.debug(f"Notice loading dynamic heroes: {e}")

    def get_count(self) -> int:
        if self.collection:
            try:
                return self.collection.count()
            except Exception:
                return 0
        return 0

    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extracts heroes, events, generations, and expert names from the query."""
        q = query.lower()
        entities = {
            "heroes": [],
            "events": [],
            "experts": [],
            "generations": []
        }

        # Hero matching
        for hero in self.known_heroes:
            # Word boundary check
            if re.search(r'\b' + re.escape(hero) + r'\b', q):
                entities["heroes"].append(hero.title())

        # Event matching
        for ev in KNOWN_EVENTS:
            if ev in q:
                entities["events"].append(ev.title())

        # Expert matching
        for exp in KNOWN_EXPERTS:
            if re.search(r'\b' + re.escape(exp) + r'\b', q):
                entities["experts"].append(exp.title())

        # Generation matching (e.g., gen 1, gen 2, gen14, generation 5, gen 17, gen 18)
        gen_matches = re.findall(r'\b(?:gen|generation)\s*(\d{1,2})\b', q)
        if gen_matches:
            for g in gen_matches:
                entities["generations"].append(f"Gen {g}")

        return entities

    def get_hero_profile(self, hero_name: str) -> Optional[str]:
        """Directly extracts full, clean markdown profile for a hero from Heroes.md."""
        file_path = "./wos data/Heroes.md"
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            
            hero_lower = hero_name.lower()
            found = False
            extracted = []
            
            for line in lines:
                stripped = line.strip()
                # Check for hero header (e.g. Flint, Edith, Alonso, Jeronimo, Smith)
                if not found:
                    if re.search(r'\b' + re.escape(hero_lower) + r'\b', stripped.lower()) and ("–" in stripped or "—" in stripped or stripped.startswith("#")):
                        # Exclude team pairing lines (e.g. "Teams: Flint + Alonso")
                        if "teams:" not in stripped.lower() and "roadmap:" not in stripped.lower() and "build order:" not in stripped.lower():
                            found = True
                            extracted.append(line)
                else:
                    # If we reach another hero header, stop
                    if ("–" in stripped or "—" in stripped or stripped.startswith("### Gen ") or stripped.startswith("# Gen ")) and not re.search(r'\b' + re.escape(hero_lower) + r'\b', stripped.lower()):
                        if "teams:" not in stripped.lower() and len(extracted) > 10:
                            break
                    extracted.append(line)
            
            if extracted:
                return "".join(extracted).strip()
        except Exception as e:
            logger.debug(f"Error reading hero profile: {e}")
        return None

    def get_event_profile(self, event_name: str) -> Optional[str]:
        """Directly extracts full, clean markdown guide for an event from Event Information.md."""
        file_path = "./wos data/Event Information.md"
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            
            ev_lower = event_name.lower()
            found = False
            extracted = []
            
            for line in lines:
                stripped = line.strip()
                if not found:
                    if ev_lower in stripped.lower() and ("#" in stripped or "–" in stripped or "—" in stripped):
                        found = True
                        extracted.append(line)
                else:
                    if (stripped.startswith("# #") or stripped.startswith("## ")) and ev_lower not in stripped.lower():
                        if len(extracted) > 10:
                            break
                    extracted.append(line)
            
            if extracted:
                return "".join(extracted).strip()
        except Exception as e:
            logger.debug(f"Error reading event profile: {e}")
        return None


    def get_generation_profile(self, gen_name: str) -> Optional[str]:
        """Extracts full markdown details for a specific Generation (e.g. Gen 16, Gen 2)."""
        file_path = "./wos data/Heroes.md"
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            
            gen_num = re.search(r'\d+', gen_name)
            if not gen_num:
                return None
            gen_target = f"gen {gen_num.group(0)}"
            
            found = False
            extracted = []
            
            for line in lines:
                stripped = line.strip().lower()
                if not found:
                    if (stripped.startswith("### gen ") or stripped.startswith("# gen ") or stripped.startswith("## gen ")) and gen_target in stripped:
                        found = True
                        extracted.append(line)
                else:
                    if (stripped.startswith("### gen ") or stripped.startswith("# gen ") or stripped.startswith("### rare") or stripped.startswith("### epic")) and gen_target not in stripped:
                        if len(extracted) > 10:
                            break
                    extracted.append(line)
            
            if extracted:
                return "".join(extracted).strip()
        except Exception as e:
            logger.debug(f"Error reading generation profile: {e}")
        return None

    def search_context(self, query: str, max_chunks: int = 5) -> str:
        """
        Hybrid retrieval combining semantic vector search, metadata boosts,
        direct hero and generation markdown extractors, and core fallback rules.
        """
        entities = self.extract_entities(query)
        collected_documents = []
        seen_ids = set()

        # 1. Direct Hero profile if hero mentioned
        for hero in entities.get("heroes", []):
            profile = self.get_hero_profile(hero)
            if profile:
                collected_documents.append(f"=== OFFICIAL HERO DOSSIER: {hero} ===\n{profile[:3000]}")

        # 2. Direct Generation profile if generation mentioned
        for gen in entities.get("generations", []):
            gen_prof = self.get_generation_profile(gen)
            if gen_prof:
                collected_documents.append(f"=== OFFICIAL GENERATION DOSSIER: {gen} ===\n{gen_prof[:3500]}")

        # 3. Direct Event guide if event mentioned
        for ev in entities.get("events", []):
            profile = self.get_event_profile(ev)
            if profile:
                collected_documents.append(f"=== OFFICIAL EVENT GUIDE: {ev} ===\n{profile[:3000]}")

        # 4. Semantic Vector Query from ChromaDB


        if self.collection and self.collection.count() > 0:
            try:
                vector_results = self.collection.query(
                    query_texts=[query],
                    n_results=min(max_chunks * 2, max(self.collection.count(), 1))
                )
                if vector_results and vector_results['documents'] and vector_results['documents'][0]:
                    docs = vector_results['documents'][0]
                    ids = vector_results['ids'][0] if 'ids' in vector_results else []
                    for doc_id, doc in zip(ids, docs):
                        if doc_id not in seen_ids:
                            # Filter out raw garbage web chunks if present
                            if "â" not in doc and len(doc.strip()) > 40:
                                collected_documents.append(doc)
                                seen_ids.add(doc_id)

            except Exception as e:
                logger.error(f"Vector search failed: {e}")

        # Limit to top chunks
        top_chunks = collected_documents[:max_chunks]
        rag_context = "\n\n---\n\n".join(top_chunks) if top_chunks else "No specific indexed chunk found."

        # Assemble full context
        full_context = f"{CORE_WOS_KNOWLEDGE}\n\n=== RETRIEVED WOS ARCHIVES & DATA ===\n{rag_context}"
        return full_context

    def build_system_prompt(self, query: str, context: str) -> str:
        """
        Constructs the Grandmaster Whiteout Survival AI persona prompt.
        """
        system_prompt = f"""You are **Frosty**, the premier Whiteout Survival Tactical Oracle and Grandmaster Military Advisor.
You possess deep, comprehensive mastery of Whiteout Survival mechanics, heroes (Gen 0 through Gen {self.max_generation}+), troop ratios, rally joiner dynamics, Bear Trap setups, Crazy Joe defense, Dawn Academy Experts, and PvP/PvE strategies.

### YOUR DIRECTIVES:
1. **Live Generation Reality**: All generations present in your archives up to Gen {self.max_generation}+ are fully released and active on older states. Provide direct, tactical evaluations and lineup setups for all indexed generations.
2. **Provide Expert, High-Value Advice**: Deliver concrete, tactical, and immediately actionable answers.
3. **Use Accurate Game Data**: Utilize the provided data context for exact stats, multipliers, generation numbers, and skill mechanics. Never invent fake stats.
4. **Format for Discord Readability**:
   - Use clean Markdown with bold headers (`### 🛡️ ...`), bullet points, and high-visibility emojis.
   - When discussing heroes, state their Generation, Troop Type (Infantry/Lancer/Marksman), Key Skills, and F2P vs P2W verdict.
   - When discussing formations/lineups, explain the troop ratios (e.g. 50/20/30 or 4-1-1) and hero positioning (1 Leader + 2 Deputies).
   - Conclude with a clear, punchy **💡 Grandmaster Tip** or **❄️ Tactical Verdict**.
5. **Context Synthesis**: Synthesize retrieved archives with core Whiteout Survival knowledge to provide a complete, flawless answer.

### REFERENCE DATA CONTEXT:
{context}
"""
        return system_prompt

