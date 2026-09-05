# ❄️ Frosty: Whiteout Survival Tactical AI & Grandmaster Advisor

<p align="center">
  <img src="https://img.shields.io/badge/Frosty_AI-v2.5_Active-00D2FF?style=for-the-badge&logo=discord&logoColor=white" alt="Frosty AI Version" />
  <img src="https://img.shields.io/badge/Android-Flutter_App-3DDC84?style=for-the-badge&logo=android&logoColor=white" alt="Android App" />
  <img src="https://img.shields.io/badge/Made_By-StateCraft-00F0FF?style=for-the-badge" alt="Made by StateCraft" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Google_Gemini-3.6_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Google Gemini" />
  <img src="https://img.shields.io/badge/Groq-Active_LLMs-F55036?style=for-the-badge&logo=groq&logoColor=white" alt="Groq" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License" />
</p>

<p align="center">
  <b>The ultimate Discord & Android AI tactical companion for Whiteout Survival Chiefs, Alliances, and Grandmasters.</b><br />
  Combines conversational LLM intelligence (Google Gemini 3.6 Flash & Groq) with a dedicated ChromaDB Hybrid RAG engine containing verified archives for <b>Generations 0 through 16+</b>, State Age calculators, event walkthroughs, Dawn Academy experts, and formation calculators.
</p>

<p align="center">
  <a href="https://discord.com/oauth2/authorize?client_id=1501632240466006108&permissions=347200&integration_type=0&scope=bot+applications.commands">
    <img src="https://img.shields.io/badge/❄️_INVITE_FROSTY_TO_DISCORD-5865F2?style=for-the-badge&logo=discord&logoColor=white" height="42" alt="Invite Frosty to Discord" />
  </a>
  <a href="https://github.com/Zcross091/frosty-wos-ai/releases">
    <img src="https://img.shields.io/badge/📱_DOWNLOAD_ANDROID_APK-3DDC84?style=for-the-badge&logo=android&logoColor=white" height="42" alt="Download Android App" />
  </a>
</p>

---

## 📱 Frosty Mobile (Native Android Flutter App)

Located in [`device/mobile/`](file:///c:/Users/afaqa/OneDrive/Documents/Development/Frosty%20Bot%20wos/device/mobile), the Frosty Android app brings all tactical intelligence directly to your mobile device:

* 💬 **Live Tactical AI Chat:** Ask complex questions with real-time "cooking" typing animations. Supports **Gemini 3.6 Flash**, **Groq**, **Local Ollama**, and **Offline Tactical Core**.
* ⏱️ **Offline State Age & Generation Calculator:** Enter your State Number (1 - 1500+) or launch date to calculate exact server age, active hero generation, countdown to the next generation, and tactical shard-saving advice.
* 📖 **Offline Hero Codex (Gen 0 - 16+):** Complete offline dossier for heroes (Seigel, Aisling, Ursar, Bradley, Edith, Flint, Alonso, etc.) with stats, exclusive gear, and F2P/P2W star roadmaps.
* 📊 **Interactive Troop Formation Calculator:** Preset switches (`50/20/30 PvP`, `10/10/80 Bear Trap`, `60/20/20 Garrison`) with march capacity sliders and exact troop counts.
* 🌟 **Community & Settings Hub:** Direct links to **Post Issues**, **Fork Repository**, **Star on GitHub**, **Contribute**, and Discord bot invite.


---

## 🌐 Live Interactive 3D Showcase & Documentation

Experience the live 3D web dashboard, interactive command simulator, and tactical lineup calculator hosted on GitHub Pages:

👉 **[Launch 3D Interactive Website](https://zcross091.github.io/frosty-wos-ai/)**

---

## ⚡ Key Capabilities

* 🧠 **Multi-Provider AI Fallback Matrix:** Defaults to ultra-fast **Google Gemini 3.6 Flash** and automatically fails over to **Groq (`openai/gpt-oss-120b`, `llama-3.3-70b-versatile`, `qwen3.8-27b`)**, **Local Ollama**, or the **Offline Zero-Key Tactical Synthesizer**.
* 📚 **Deep Whiteout Survival Knowledge Base:** Indexed across 5,500+ lines of verified game data covering every generation (**Gen 0 to Gen 16+** like Seigel, Aisling, and Ursar), skill synergies, exclusive gear, and F2P/P2W advice.
* 🐻 **Bear Trap & Rally Joiner Mastery:** Implements Whiteout Survival's core math—automatically advises the **Top 4 Rally Joiner skill buffs** (Jessie +25% damage, Seo-yoon +20% attack) and high-DPS `10/10/80` or `0/20/80` troop compositions.
* ⚔️ **Tactical Formation Engine:** Formulates optimal 3-hero squad positioning (1 Leader / Captain + 2 Deputies) with precision troop ratios (`50/20/30`, `60/20/20`, `40/10/50` / `4-1-1`).
* ⚡ **Zero-Lag Async Worker Threads:** All AI generation executes in dedicated non-blocking asynchronous threads (`asyncio.to_thread`), ensuring Discord gateway heartbeats never freeze.
* 🎨 **Interactive Discord UI:** Clean icy cyan embeds (`#00D2FF`) featuring action buttons (`⚡ Regenerate`, `🛡️ Lineup Tips`, `❌ Dismiss`) and autocomplete for all heroes and events.
* 🧵 **Thread Conversation Memory:** Retains multi-turn conversation context in Discord channels and DMs for deep coaching sessions.

---

## 🛠️ Commands Directory

Frosty fully supports both modern **Slash Commands (`/`)** with instant autocomplete and classic **Prefix Commands (`!`)**:

| Slash Command | Prefix Command | Description |
| :--- | :--- | :--- |
| `/wos [question]` | `!wos [question]` | Ask any complex Whiteout Survival question, hero comparison, meta lineup, or battle strategy. |
| `/state [number/days]` | `!state [number/days]` | Real-time Server Age calculator, active Generation, recently unlocked features & milestone countdowns. |
| `/fc [building] [from] [to]` | `!fc [building] [from] [to]` | Fire Crystal (FC 1 - FC 12+ & Refined FC) material, build time, and SvS Construction points calculator. |
| `/charms [from] [to]` | `!charms [from] [to]` | Chief Charms (Lv 1 - 12) Guides & Designs cost, combat surge %, and SvS Charm points. |
| `/svs [activity] [amount]` | `!svs [activity] [amount]` | SvS Prep Phase Points optimizer with optimal day recommendations (Day 1 to 5). |
| `/timer [set/list/delete]` | `!timer [set/list/delete]` | Manage up to 5 UTC alliance countdowns (Foundry, Canyon Clash, SvS, Bear Trap, Fortress) with automated `@here` alerts. |
| `/transfer [power]` | `!transfer [power]` | State Transfer Pass calculator based on Chief Power (1 to 80+ passes) & eligibility rules. |
| `/codes` | `!codes` | Active Whiteout Survival gift codes with direct 1-tap Century Games redemption portal link. |
| `/hero [name]` | `!hero [name]` | Complete hero dossier (Generation, Troop Type, Skills, Exclusive Gear, F2P vs P2W verdict). |
| `/lineup [mode] [gen]` | `!lineup [mode]` | Recommended 3-hero lineups and troop ratios for PvP, Bear Trap, Castle Defense, and Foundry. |
| `/bear` | `!bear` | Master Bear Trap cheat sheet: `10/10/80` troop ratio, rally joiner Jessie/Seo-yoon buffs, and leader setups. |
| `/bearsim [capacity] [tier]` | `!bearsim [capacity]` | Interactive Bear Trap DPS Simulator with exact troop breakdown and Jessie joiner boost calculations. |
| `/event [name]` | `!event [name]` | Walkthroughs and tips for Crazy Joe, Foundry Battle, Frostfire Mine, Sunfire Castle, and SvS. |
| `/expert [name]` | `!expert [name]` | Dawn Academy expert profiles, sigil optimization, and Strategic Pausing breakpoints. |
| `/status` | `!status` | Real-time bot diagnostics: active AI engine, RAM consumption, websocket latency, and indexed knowledge chunks. |
| `/reindex` | `!reindex` | *(Admin Only)* Triggers semantic re-indexing of local guides into ChromaDB. |
| `/help` | `!help` | Displays the interactive command menu. |

---

## 🏛️ System Architecture

```
                                  ┌────────────────────────┐
                                  │   Discord User / Chat  │
                                  └───────────┬────────────┘
                                              │ (/wos, !hero, !lineup)
                                              ▼
                                  ┌────────────────────────┐
                                  │   discord.py Gateway   │
                                  │  (Async Worker Thread) │
                                  └───────────┬────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
         ┌─────────────────────────┐                     ┌─────────────────────────┐
         │ ChromaDB Hybrid RAG     │                     │ Multi-Provider AI Engine│
         ├─────────────────────────┤                     ├─────────────────────────┤
         │ • Heroes.md (Gen 0-17+) │ === Context Boost ==>│ 1. Google Gemini 3.6    │
         │ • Events.md (Crazy Joe) │                     │ 2. Groq LLMs            │
         │ • State_Timeline.md     │                     │ 3. Local Ollama         │
         │ • Utility_Calculators.md│                     │ 4. Zero-Key Synthesizer │
         └─────────────────────────┘                     └────────────┬────────────┘
                                                                      │
                                                                      ▼
                                                         ┌─────────────────────────┐
                                                         │ Discord Rich Cyan Embed │
                                                         │ (Interactive UI Buttons)│
                                                         └─────────────────────────┘
```

---

## ⚙️ Quick Start & Self-Hosting Guide

### Prerequisites
- Python 3.10+
- Free Discord Bot Token from [Discord Developer Portal](https://discord.com/developers/applications)
- Free Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/) or Groq Key from [Groq Console](https://console.groq.com/)

### 1. Clone the Repository
```bash
git clone https://github.com/Zcross091/frosty-wos-ai.git
cd frosty-wos-ai
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment (`.env`)
Create your `.env` configuration file:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# Discord Token
DISCORD_TOKEN=your_discord_bot_token_here

# Primary AI Provider: "gemini", "groq", "ollama", or "local"
AI_PROVIDER=gemini

# Google Gemini (Recommended - 100% Free)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash

# Groq (Fast Cloud Fallback)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Local Knowledge Base & Bot Settings
CHROMA_PATH=./frosty_brain
COMMAND_PREFIX=!
ADMIN_USER_IDS=
```

### 4. Ingest Tactical Knowledge Base
Index the local strategy guides into ChromaDB:
```bash
# Ingest clean local markdown guides (Heroes Gen 0-17, State Timeline, Utilities)
python ingest.py --local-only --clean
```

### 5. Launch the Bot
```bash
python bot.py
```

---

## ☁️ 24/7 Production Deployment (Oracle Cloud / PM2)

To run Frosty permanently in the background with automatic restart on crashes or reboots:

```bash
# Install PM2 globally (Node.js required)
npm install -g pm2

# Start with PM2 Ecosystem
pm2 start ecosystem.config.js

# Or start directly:
pm2 start bot.py --name frosty-wos-ai --interpreter python3

# Save PM2 process list across VM reboots
pm2 save
pm2 startup
```

---

## 🛡️ Hero Generation Coverage Matrix

Frosty contains verified statistical dossiers, exploration skills, expedition buffs, and exclusive gear ratings for all generations:

| Generation | Era | Highlight Heroes | Key Meta Roles |
| :---: | :---: | :---: | :---: |
| **Gen 0 / Rare & Epic** | Early Game | Jessie, Sergey, Bahiti, Patrick, Gina, Smith | Essential Rally Joiners (+25% Dmg) & Gathering |
| **Gen 1** | Early Server | Jeronimo, Natalia, Zinman, Molly | Early Rally Lead & Arena Burst |
| **Gen 2** | ~Day 40 | Flint, Alonso, Philly | Lucky Wheel Tank, AOE Stun, Healer |
| **Gen 3** | ~Day 120 | Mia, Logan, Greg | High Burst Marksman & SvS Garrison |
| **Gen 4** | ~Day 180 | Lynn, Hector, Ahmose | Rally Lead Stuns & Lancer Pierce |
| **Gen 5 – 6** | Mid Game | Gwen, Norah, Wayne, Renee, Hendrik | Defensive Wall & Sniper DPS |
| **Gen 7** | ~Day 400 | Bradley, Edith, Gordon | Top PvP Frontline & Piercing Marksman |
| **Gen 8 – 11** | Mid-Late Game | Sonya, Reina, Magnus, Blanche, Xylona, Rufus | Lethality Shred & Multi-Target Debuffs |
| **Gen 12 – 15** | Late Game | Anson, Eleanor, Lloyd, Freyja, Kai, Alistair | High Scale Defense & Speed Metas |
| **Gen 16** | ~1160 Days | **Seigel** (Infantry), **Ursar** (Lancer), **Aisling** (Marksman) | Reflect Shield, Toxic Support & Endgame Burst |
| **Gen 17+** | 1240+ Days | **Aiden** (Infantry), **Eleanor** (Marksman), **Rufus** (Lancer) | Ultimate Piercing Lethality & Solar Aegis |

---

## 👥 Contributors

Thank you to everyone who has contributed code, bug reports, tactical data, and feature ideas to the Frosty WOS AI project!

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
<p align="center">
  <a href="https://github.com/Zcross091/frosty-wos-ai/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=Zcross091/frosty-wos-ai" alt="Frosty Contributors" />
  </a>
</p>
<!-- ALL-CONTRIBUTORS-BADGE:END -->

<p align="center">
  <sub>Made by <a href="https://github.com/Zcross091"><b>Zcross091</b></a> and the Whiteout Survival tactical community.</sub>
</p>

---

## 🤝 Contributing & Community

Contributions, issues, and tactical strategy submissions are warmly welcome!
- **Submit an Issue:** Report bugs or suggest new game features via [GitHub Issues](https://github.com/Zcross091/frosty-wos-ai/issues).
- **Pull Requests:** Feel free to submit PRs for new hero guides, event data, or performance optimizations.
- **View Full Contributor Network:** Explore all [contributors on GitHub](https://github.com/Zcross091/frosty-wos-ai/graphs/contributors).

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

<p align="center">
  <b>Built with ❄️ for Whiteout Survival Chiefs worldwide.</b>
</p>
