# ❄️ Frosty: Whiteout Survival Expert AI

Frosty is a high-performance Discord bot powered by **Gemini 3 Flash** and **ChromaDB**, designed to provide instant, expert-level strategic advice for Whiteout Survival players. 

<p align="center">
  <a href="https://discord.com/oauth2/authorize?client_id=1501632240466006108&permissions=347200&integration_type=0&scope=bot+applications.commands">
    <img src="https://img.shields.io/badge/Invite%20Frosty-Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" />
  </a>
</p>

---

## 🚀 Features

*   **Deep Strategy Knowledge:** Powered by a vector database containing over 3,300 pages of game mechanics, hero guides, and event strategies.
*   **Real-Time AI Response:** Utilizes the latest Gemini 3 Flash model for rapid, context-aware answers.
*   **Persistent Cloud Hosting:** Managed via PM2 on Oracle Cloud for 24/7 uptime.
*   **Discord Integration:** Built with `discord.py` for seamless slash command and prefix support.

## 🛠️ Commands

| Command | Description |
| :--- | :--- |
| `!wos [question]` | Ask Frosty anything about Whiteout Survival strategy, hero lineups, or events. |
| `!status` | Check the bot's current RAM usage and database health. |

## 📦 Tech Stack

- **Language:** Python 3.10+
- **AI Model:** Gemini 3 Flash (via `google-genai`)
- **Database:** ChromaDB (Vector Storage)
- **Process Manager:** PM2
- **Infrastructure:** Oracle Cloud Infrastructure (OCI)

## 🔧 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Zcross091/frosty-wos-ai.git](https://github.com/Zcross091/frosty-wos-ai.git)
   cd frosty-wos-ai
