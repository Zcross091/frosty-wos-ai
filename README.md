# ❄️ Frosty: Whiteout Survival Tactical AI & Grandmaster Advisor

Frosty is an advanced Discord AI bot powered by **Google Gemini** (with **Groq** & **OpenAI** multi-provider fallback) and **ChromaDB Hybrid RAG**, designed to provide instant, tactical, and expert-level guidance for Whiteout Survival Chiefs.

<p align="center">
  <a href="https://discord.com/oauth2/authorize?client_id=1501632240466006108&permissions=347200&integration_type=0&scope=bot+applications.commands">
    <img src="https://img.shields.io/badge/Invite%20Frosty-Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" />
  </a>
</p>

---

## 🚀 Key Features

* 🧠 **Multi-Provider AI Engine:** Powered by **Google Gemini** (`gemini-2.0-flash` / `gemini-1.5-flash`), with automated failover to **Groq** (`llama-3.3-70b-versatile`) and **OpenAI** (`gpt-4o-mini`).
* 📚 **Semantic Hybrid RAG:** Ingests and cross-references over 5,500+ lines of hero guides (Gen 0 through Gen 16+), wave-by-wave event tactics (Crazy Joe, Bear Trap, Foundry Battle, Frostfire Mine, Sunfire Castle), and Dawn Academy expert roadmaps.
* ⚡ **Discord Slash Commands & Autocomplete:** Full support for modern `/` Discord slash commands with instant auto-completion for heroes, events, and Dawn Academy experts.
* 🛡️ **Tactical Formation Engine:** Instant calculations for 3-hero marches (Leader + 2 Deputies) and troop ratios (`50/20/30`, `40/10/50` / `4-1-1`, `10/10/80` Bear Trap).
* 🔄 **Interactive Discord UI:** Clean icy cyan embeds (`#00D2FF`) with interactive buttons (`⚡ Regenerate`, `🛡️ Lineup Tips`, `❌ Dismiss`).
* 🧵 **Multi-Turn Thread Memory:** Remembers recent conversation context in Discord threads and DMs for deep coaching sessions.
* ☁️ **Production Cloud Ready:** Optimized with PM2 ecosystem config for 24/7 uptime on Oracle Cloud Infrastructure (OCI).

---

## 🛠️ Commands & Capabilities

Frosty supports both **Slash Commands (`/`)** and **Prefix Commands (`!`)**:

| Slash Command | Prefix Command | Description |
| :--- | :--- | :--- |
| `/wos [question]` | `!wos [question]` | Ask any question on Whiteout Survival strategy, hero comparisons, or mechanics. |
| `/hero [name]` | `!hero [name]` | Complete hero breakdown (Generation, Troop Type, Skills, Best Gear, F2P/P2W verdict) with autocomplete. |
| `/lineup [mode] [gen]` | `!lineup [mode]` | Recommended 3-hero lineups and troop ratios for Exploration, Bear Trap, Castle Defense, PvP, and Foundry. |
| `/bear` | `!bear` | Master Bear Trap cheat sheet (10/10/80 ratio, Jessie/Seo-yoon joiner damage buffs, lead setups). |
| `/event [name]` | `!event [name]` | In-depth walkthroughs for Crazy Joe, Foundry Battle, Frostfire Mine, Sunfire Castle, and SvS. |
| `/expert [name]` | `!expert [name]` | Dawn Academy expert guide, sigil cost efficiency, and Strategic Pausing breakpoints. |
| `/status` | `!status` | Real-time diagnostics: active AI engine, RAM usage, ping, and indexed knowledge chunks. |
| `/reindex` | `!reindex` | *(Admin Only)* Triggers database re-indexing with the latest local guides. |
| `/help` | `!help` | Displays interactive tactical command directory. |

---

## ⚙️ Environment Setup (`.env`)

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
# Discord Token
DISCORD_TOKEN=your_discord_bot_token_here

# AI Provider ("gemini", "groq", or "openai")
AI_PROVIDER=gemini

# Google Gemini (Recommended)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Groq (Alternative / Fallback)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Admin User IDs (comma-separated Discord IDs for /reindex)
ADMIN_USER_IDS=123456789012345678
```

---

## ☁️ Deployment on Oracle Cloud (PM2)

### 1. Update Code on Oracle Cloud
```bash
git pull origin main
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Ingest / Index Game Knowledge
```bash
# Ingest local markdown strategy guides (Fast)
python ingest.py --local-only

# Or run full ingestion with web wikis
python ingest.py
```

### 4. Start / Restart via PM2
```bash
# Start with PM2 ecosystem
pm2 start ecosystem.config.js

# Or if already running:
pm2 restart frosty-wos-ai

# Save PM2 process list to persist on VM reboot
pm2 save
```

---

## 📦 Tech Stack

- **Language:** Python 3.10+
- **Discord Framework:** `discord.py` (v2.3+) with App Commands
- **AI Models:** Google Gemini 2.0 Flash (`google-genai` / `google-generativeai`), Groq LLaMA 3.3 70B (`groq`), OpenAI GPT-4o-mini (`openai`)
- **Vector Database:** ChromaDB
- **Process Manager:** PM2 on Oracle Cloud Infrastructure (OCI)
