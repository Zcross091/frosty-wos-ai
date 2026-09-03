"""
❄️ Frosty AI - Next-Level Whiteout Survival Discord Bot
Features Slash Commands, Autocomplete, Hybrid RAG, Multi-Provider AI (Gemini/Groq/OpenAI),
Interactive UI Buttons, Rich Embeds, and Multi-Turn Conversation Memory.
"""

import os
import re
import json
import time
import asyncio
import logging
import psutil
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Tuple, Any

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

from ai_engine import AIEngine
from knowledge_base import KnowledgeBase, KNOWN_HEROES, KNOWN_EVENTS, KNOWN_EXPERTS
from ingest import run_full_reindex

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("FrostyAI")

# Load environment
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!").strip() or "!"
ADMIN_USER_IDS = [int(uid.strip()) for uid in os.getenv("ADMIN_USER_IDS", "").split(",") if uid.strip().isdigit()]

# Color Palette
FROSTY_COLOR = discord.Color.from_rgb(0, 210, 255)      # #00D2FF Frosty Cyan
SUCCESS_COLOR = discord.Color.from_rgb(46, 204, 113)    # Emerald Green
WARN_COLOR = discord.Color.from_rgb(241, 196, 15)       # Amber Gold
ERROR_COLOR = discord.Color.from_rgb(231, 76, 60)       # Ruby Red

# Active Alliance Timers Cache {guild_id or channel_id: list of timer dicts} (Max 5 per context)
ACTIVE_TIMERS: Dict[int, List[Dict[str, Any]]] = {}
_timer_counter = 1

# Active Whiteout Survival Promo Codes (Easy to update and poll)
ACTIVE_GIFT_CODES = [
    {"code": "WOS2026", "rewards": "1000 Gems, 5x 1h Speedups, 10x Gold Keys, 500k Meat/Wood"},
    {"code": "STATEOFPOWER", "rewards": "500 Gems, 10x Advanced Wild Marks, 20x Chief Charm Guides"},
    {"code": "DC300K", "rewards": "1500 Gems, 20x Mythic Shards, 10x 1h Speedups"},
    {"code": "FROSTYTACTICS", "rewards": "Exclusive Frosty Avatar Frame, 300 Gems, 5x Stamina Potions"},
    {"code": "BEARHUNT2026", "rewards": "800 Gems, 100x Stamina, 10x March Speedups"},
]

# Initialize Core Services
ai_engine = AIEngine()
knowledge_base = KnowledgeBase()

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)

# Multi-Turn Conversation Memory {channel_id: [{"role": "...", "content": "..."}]}
conversation_memory: Dict[int, List[Dict[str, str]]] = {}
CONV_TIMEOUT = 900  # 15 minutes


def get_conversation_history(channel_id: int) -> List[Dict[str, str]]:
    return conversation_memory.get(channel_id, [])


def append_conversation(channel_id: int, user_msg: str, bot_msg: str):
    if channel_id not in conversation_memory:
        conversation_memory[channel_id] = []
    history = conversation_memory[channel_id]
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": bot_msg})
    # Keep only last 6 turns (3 exchanges)
    conversation_memory[channel_id] = history[-6:]


# --- Interactive UI Components ---
class FrostyActionView(discord.ui.View):
    def __init__(self, original_user: discord.User, question: str, original_answer: str):
        super().__init__(timeout=180)
        self.original_user = original_user
        self.question = question
        self.original_answer = original_answer

        # 4th Button: Direct Link to Download Latest Mobile App
        self.add_item(discord.ui.Button(
            label="📱 Get Mobile App",
            style=discord.ButtonStyle.link,
            url="https://github.com/Zcross091/frosty-wos-ai/releases/latest",
            emoji="📥"
        ))

    @discord.ui.button(label="🔄 Regenerate", style=discord.ButtonStyle.secondary, emoji="⚡")
    async def regenerate_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.original_user.id:
            await interaction.response.send_message("❌ Only the chief who asked this question can regenerate it.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)
        context = knowledge_base.search_context(self.question, max_chunks=5)
        system_prompt = knowledge_base.build_system_prompt(self.question, context)
        answer, model_used, elapsed = await asyncio.to_thread(
            ai_engine.generate_response, system_prompt, self.question, None, 0.8
        )

        embed = discord.Embed(
            title="❄️ Frosty Tactical Advisory (Regenerated)",
            description=answer[:4000],
            color=FROSTY_COLOR
        )
        embed.set_footer(text=f"Engine: {model_used} • Latency: {elapsed:.2f}s • Chief: {self.original_user.display_name}")
        await interaction.followup.send(embed=embed, view=FrostyActionView(self.original_user, self.question, answer))

    @discord.ui.button(label="⚔️ Best Lineup Tips", style=discord.ButtonStyle.primary, emoji="🛡️")
    async def lineup_tips_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True, ephemeral=True)
        lineup_query = f"What is the best hero lineup and troop ratio for: {self.question}"
        context = knowledge_base.search_context(lineup_query, max_chunks=4)
        system_prompt = knowledge_base.build_system_prompt(lineup_query, context)
        answer, model_used, elapsed = await asyncio.to_thread(
            ai_engine.generate_response, system_prompt, lineup_query, None, 0.6
        )

        embed = discord.Embed(
            title="⚔️ Tactical Formation & Lineup Advisory",
            description=answer[:4000],
            color=FROSTY_COLOR
        )
        embed.set_footer(text=f"Engine: {model_used} • Frosty Doctrine")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="🗑️ Dismiss", style=discord.ButtonStyle.danger, emoji="❌")
    async def dismiss_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.original_user.id or (interaction.user.guild_permissions.manage_messages if interaction.guild else False):
            await interaction.message.delete()
        else:
            await interaction.response.send_message("❌ You cannot dismiss this message.", ephemeral=True)


# --- Autocomplete Helpers ---
async def hero_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    current_lower = current.lower()
    matches = [h.title() for h in KNOWN_HEROES if current_lower in h.lower()]
    return [app_commands.Choice(name=m, value=m) for m in matches[:25]]


async def event_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    current_lower = current.lower()
    matches = [e.title() for e in KNOWN_EVENTS if current_lower in e.lower()]
    return [app_commands.Choice(name=m, value=m) for m in matches[:25]]


async def expert_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    current_lower = current.lower()
    matches = [exp.title() for exp in KNOWN_EXPERTS if current_lower in exp.lower()]
    return [app_commands.Choice(name=m, value=m) for m in matches[:25]]


# --- Timer Loop (Alliance Countdowns) ---
@tasks.loop(seconds=15)
async def check_timers():
    try:
        await bot.wait_until_ready()
        now_utc = datetime.now(timezone.utc)
        for key, timers in list(ACTIVE_TIMERS.items()):
            expired = [t for t in timers if t["target_time"] <= now_utc]
            for t in expired:
                try:
                    channel = bot.get_channel(t["channel_id"])
                    if channel:
                        embed = discord.Embed(
                            title=f"🚨 ALLIANCE EVENT ALERT: {t['event'].upper()}",
                            description=f"🔔 Attention Chiefs! **{t['event']}** is starting **NOW**!\n\n• **Event:** `{t['event']}`\n• **Set By:** <@{t['user_id']}>\n• **Time (UTC):** `{t['target_time'].strftime('%Y-%m-%d %H:%M UTC')}`",
                            color=WARN_COLOR
                        )
                        if "bear" in t["event"].lower():
                            embed.add_field(name="🐻 Bear Trap Strategy", value="• Set **Jessie / Jader / Seo-yoon** as 1st joiner heroes (+25% Damage)!\n• Use **10/10/80** troop ratio (heavy Marksman) for max damage.", inline=False)
                        elif "foundry" in t["event"].lower():
                            embed.add_field(name="🗺️ Foundry Battle Strategy", value="• Capture Boiler Room & Arsenal first!\n• Intercept enemy transport trucks on bottom lane.", inline=False)
                        elif "canyon" in t["event"].lower():
                            embed.add_field(name="🏜️ Canyon Clash Strategy", value="• Control central canyon nodes and secure resource transports!", inline=False)
                        elif "svs" in t["event"].lower():
                            embed.add_field(name="⚔️ SVS Battle Phase Strategy", value="• Defend Sunfire Castle and attack enemy turrets!\n• Activate War Buffs and Shield unjoined cities.", inline=False)
                        elif "fortress" in t["event"].lower():
                            embed.add_field(name="🏰 Fortress Battle Strategy", value="• Coordinate rally leaders with highest lethality!\n• Rotate garrison reinforcement troops.", inline=False)

                        await channel.send(content=f"🔔 <@{t['user_id']}> **@here**", embed=embed)
                except Exception as ex:
                    logger.error(f"Error executing timer alert: {ex}")
                timers.remove(t)
    except Exception as e:
        logger.debug(f"Timer loop notice: {e}")


# --- Activity Loop ---
@tasks.loop(minutes=3)
async def rotate_presence():
    try:
        await bot.wait_until_ready()
        if bot.is_closed():
            return
        import random
        activities = [
            discord.Game(name="Whiteout Survival | /wos"),
            discord.Activity(type=discord.ActivityType.watching, name=f"{knowledge_base.get_count()} Tactical Archives"),
            discord.Game(name="Bear Trap & SvS Strategies | /bear"),
            discord.Activity(type=discord.ActivityType.listening, name="Hero Formations & Guides | /help")
        ]
        await bot.change_presence(activity=random.choice(activities))
    except Exception as e:
        logger.debug(f"Presence update ignored: {e}")


@rotate_presence.before_loop
async def before_rotate():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    logger.info(f"❄️ Frosty AI is online as {bot.user} (ID: {bot.user.id})")
    logger.info(f"Active Engine: {ai_engine.get_active_model_name()}")
    logger.info(f"ChromaDB Chunks Indexed: {knowledge_base.get_count()}")

    try:
        synced = await bot.tree.sync()
        logger.info(f"✨ Successfully synced {len(synced)} slash commands globally.")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")

    if not rotate_presence.is_running():
        rotate_presence.start()
    if not check_timers.is_running():
        check_timers.start()


# --- Core Response Generator ---
async def generate_frosty_response(
    channel_id: int,
    user: discord.User,
    question: str
) -> Tuple[discord.Embed, Optional[discord.ui.View]]:
    history = get_conversation_history(channel_id)
    context = knowledge_base.search_context(question, max_chunks=5)
    system_prompt = knowledge_base.build_system_prompt(question, context)

    answer, model_used, elapsed = await asyncio.to_thread(
        ai_engine.generate_response,
        system_prompt,
        question,
        history,
        0.6
    )


    append_conversation(channel_id, question, answer)

    embed = discord.Embed(
        title="❄️ Frosty Tactical Advisory",
        description=answer[:4000],
        color=FROSTY_COLOR
    )
    embed.set_footer(
        text=f"Engine: {model_used} • Latency: {elapsed:.2f}s • Asked by {user.display_name}"
    )

    view = FrostyActionView(original_user=user, question=question, original_answer=answer)
    return embed, view


# ==========================================
# 🚀 SLASH COMMANDS (/wos, /hero, /lineup, etc.)
# ==========================================

@bot.tree.command(name="wos", description="Ask Frosty anything about Whiteout Survival heroes, events, or strategy!")
@app_commands.describe(question="What strategy, hero, formation, or event would you like advice on?")
async def slash_wos(interaction: discord.Interaction, question: str):
    await interaction.response.defer(thinking=True)
    embed, view = await generate_frosty_response(interaction.channel_id, interaction.user, question)
    await interaction.followup.send(embed=embed, view=view)


@bot.tree.command(name="hero", description="Get a comprehensive tactical breakdown and build guide for any hero.")
@app_commands.describe(hero_name="Name of the hero (e.g. Jeronimo, Flint, Alonso, Mia, Wayne, Kai)")
@app_commands.autocomplete(hero_name=hero_autocomplete)
async def slash_hero(interaction: discord.Interaction, hero_name: str):
    await interaction.response.defer(thinking=True)
    query = f"Provide a complete tactical guide and evaluation for Hero: {hero_name}. Include Generation, Troop Type, Skills breakdown, Best Gear, Exploration vs Expedition rating, and F2P vs P2W verdict."
    embed, view = await generate_frosty_response(interaction.channel_id, interaction.user, query)
    await interaction.followup.send(embed=embed, view=view)


@bot.tree.command(name="lineup", description="Get the best hero lineups and troop formations for any mode and generation.")
@app_commands.describe(
    mode="Game mode",
    generation="Generation number (e.g. Gen 1, Gen 2, Gen 4, Gen 14)"
)
@app_commands.choices(mode=[
    app_commands.Choice(name="Exploration / Arena / Campaign", value="Exploration"),
    app_commands.Choice(name="Bear Trap (Max PvE Damage)", value="Bear Trap"),
    app_commands.Choice(name="Sunfire Castle / Stronghold Defense", value="Castle Defense"),
    app_commands.Choice(name="PvP Rally Attack", value="PvP Rally"),
    app_commands.Choice(name="Foundry Battle / Field PvP", value="Foundry Battle"),
    app_commands.Choice(name="Crazy Joe Defense", value="Crazy Joe")
])
async def slash_lineup(interaction: discord.Interaction, mode: app_commands.Choice[str], generation: Optional[str] = "Current"):
    await interaction.response.defer(thinking=True)
    query = f"What is the optimal hero lineup, hero positions (Leader + 2 Deputies), and troop ratio (e.g. 50/20/30 or 4-1-1) for {mode.name} in {generation}?"
    embed, view = await generate_frosty_response(interaction.channel_id, interaction.user, query)
    await interaction.followup.send(embed=embed, view=view)


@bot.tree.command(name="event", description="Detailed step-by-step master guide for Whiteout Survival events.")
@app_commands.describe(event_name="Select or type the event name")
@app_commands.autocomplete(event_name=event_autocomplete)
async def slash_event(interaction: discord.Interaction, event_name: str):
    await interaction.response.defer(thinking=True)
    query = f"Provide an in-depth master guide and checklist for the event: {event_name}. Include preparation tips, troop rules, wave schedules (if applicable), and scoring strategies."
    embed, view = await generate_frosty_response(interaction.channel_id, interaction.user, query)
    await interaction.followup.send(embed=embed, view=view)


@bot.tree.command(name="expert", description="Dawn Academy expert progression, sigil costs, and breakpoint strategies.")
@app_commands.describe(expert_name="Select or type the expert name")
@app_commands.autocomplete(expert_name=expert_autocomplete)
async def slash_expert(interaction: discord.Interaction, expert_name: str):
    await interaction.response.defer(thinking=True)
    query = f"Provide a complete breakdown for Dawn Academy Expert: {expert_name}. Include unlock requirements, skill priorities, sigil cost efficiency, and Strategic Pausing breakpoints."
    embed, view = await generate_frosty_response(interaction.channel_id, interaction.user, query)
    await interaction.followup.send(embed=embed, view=view)


@bot.tree.command(name="bear", description="Quick master reference for Bear Trap rally setups, joiner buffs, and ratios.")
async def slash_bear(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    query = "Give a concise master guide for Bear Trap: 1. Troop ratio (10/10/80), 2. Rally leader heroes, 3. Critical Rally Joiner heroes (Jessie/Seo-yoon damage buffs), and 4. March optimization tips."
    embed, view = await generate_frosty_response(interaction.channel_id, interaction.user, query)
    await interaction.followup.send(embed=embed, view=view)


@bot.tree.command(name="status", description="Display live Discord servers, total users reached, active AI model, and RAM.")
async def slash_status(interaction: discord.Interaction):
    process = psutil.Process(os.getpid())
    ram = process.memory_info().rss / 1024 / 1024
    uptime_sec = time.time() - process.create_time()
    hours, remainder = divmod(int(uptime_sec), 3600)
    minutes, seconds = divmod(remainder, 60)
    total_guilds = len(bot.guilds)
    total_members = sum(g.member_count for g in bot.guilds if g.member_count)

    embed = discord.Embed(title="📊 Frosty AI — Live Analytics & Health", color=FROSTY_COLOR)
    embed.add_field(name="🌐 Discord Servers", value=f"**{total_guilds}** Active Guilds", inline=True)
    embed.add_field(name="👥 Total Chiefs Reached", value=f"**{total_members:,}** Members", inline=True)
    embed.add_field(name="⚡ Tactical Engine", value=f"`{ai_engine.get_active_model_name()}`", inline=True)
    embed.add_field(name="📚 Database Chunks", value=f"`{knowledge_base.get_count()} chunks`", inline=True)
    embed.add_field(name="💾 Bot Memory", value=f"`{ram:.1f} MB`", inline=True)
    embed.add_field(name="⏱️ Uptime", value=f"`{hours}h {minutes}m {seconds}s`", inline=True)
    embed.add_field(name="📡 Gateway Ping", value=f"`{bot.latency * 1000:.1f} ms`", inline=True)
    embed.set_footer(text="Mobile & Web API: Check http://<server-ip>:8000/api/stats for active app users")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="reindex", description="[Admin Only] Re-ingest local markdown guides and update the vector database.")
@app_commands.describe(local_only="If True, only index local 'wos data' files without web scraping (faster)")
async def slash_reindex(interaction: discord.Interaction, local_only: bool = True):
    is_admin = interaction.user.id in ADMIN_USER_IDS or (interaction.user.guild_permissions.administrator if interaction.guild else False)
    if not is_admin:
        await interaction.response.send_message("❌ You need administrator privileges to trigger database re-indexing.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    start_time = time.time()

    loop = asyncio.get_running_loop()
    try:
        new_count = await loop.run_in_executor(None, run_full_reindex, local_only)
        knowledge_base.reload_dynamic_entities()
        elapsed = time.time() - start_time
        embed = discord.Embed(
            title="✨ Knowledge Base & Hero Data Auto-Synced",
            description=f"Frosty's brain and hero codex have been refreshed with the latest data!\n\n• **Total Chunks in DB:** `{new_count}`\n• **Active Generations:** `Gen 0 through Gen {knowledge_base.max_generation}+`\n• **Heroes Synced:** `{len(knowledge_base.known_heroes)} heroes`\n• **Elapsed Time:** `{elapsed:.2f}s`",
            color=SUCCESS_COLOR
        )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Re-indexing Failed",
            description=f"An error occurred during re-indexing: `{str(e)}`",
            color=ERROR_COLOR
        )
        await interaction.followup.send(embed=embed)


def estimate_state_launch_date(state_number: int) -> datetime:
    """Estimates the historical launch date of a Whiteout Survival State."""
    base_date = datetime(2023, 2, 14)
    if state_number <= 1:
        offset_days = 0.0
    elif state_number <= 100:
        offset_days = state_number * 1.0
    elif state_number <= 500:
        offset_days = 100.0 + (state_number - 100) * 0.625
    elif state_number <= 1000:
        offset_days = 350.0 + (state_number - 500) * 0.70
    elif state_number <= 1500:
        offset_days = 700.0 + (state_number - 1000) * 0.50
    elif state_number <= 2000:
        offset_days = 950.0 + (state_number - 1500) * 0.40
    else:
        offset_days = 1150.0 + (state_number - 2000) * 0.35

    return base_date + timedelta(days=int(round(offset_days)))


def calculate_state_telemetry(input_val: int, is_state_number: bool = True) -> Dict:
    """Calculates State Age, Generation, Active Heroes, Unlocked Features, and Next Milestone."""
    if is_state_number:
        launch_date = estimate_state_launch_date(input_val)
        age = (datetime.now() - launch_date).days
        age = max(1, min(3000, age))
    else:
        age = max(1, min(3000, input_val))

    # Dynamically load from state_timeline.json if present
    milestones = []
    if os.path.exists("state_timeline.json"):
        try:
            with open("state_timeline.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    milestones.append((item.get("day", 0), item.get("title", ""), item.get("category", "Event")))
        except Exception:
            pass

    if not milestones:
        # Fallback milestones
        milestones = [
            (0, "Gen 1 Heroes (Jeronimo, Natalia, Molly)", "Hero"),
            (14, "Tundra Territory Opens", "Event"),
            (40, "Gen 2 Heroes (Flint, Alonso, Philly)", "Hero"),
            (45, "Chief Gear & Charms T1", "Gear"),
            (53, "Sunfire Castle Battle", "Event"),
            (54, "Pet Gen 1 & Beast Cage (Hyena, Wolf, Ox)", "Pet"),
            (60, "Fire Crystal 1–3 Age (FC Troops)", "Fire Crystal"),
            (80, "State vs State (SvS) & King of Icefield", "Event"),
            (90, "Pet Gen 2 (Titan Roc, Giant Tapir)", "Pet"),
            (100, "State Transfer Phase 1", "Event"),
            (120, "Gen 3 Heroes (Mia, Logan, Greg)", "Hero"),
            (140, "Pet Gen 3 (Snow Leopard, Giant Elk)", "Pet"),
            (150, "Fire Crystal 4–5 & Crystal Lab", "Fire Crystal"),
            (180, "Gen 4 Heroes (Lynn, Ahmose, Reina)", "Hero"),
            (200, "Pet Gen 4 (Cave Lion, Snow Ape)", "Pet"),
            (220, "War Academy & T11 Troops", "Academy"),
            (250, "Gen 5 Heroes (Hector, Norah, Gwen)", "Hero"),
            (280, "Pet Gen 5 (Iron Rhino, Saber-tooth)", "Pet"),
            (300, "Fire Crystal 6–8 Age", "Fire Crystal"),
            (320, "Gen 6 Heroes (Renee, Wayne, Wu Ming)", "Hero"),
            (360, "Pet Gen 6 (Titan Beaver, Gorgon Viper)", "Pet"),
            (400, "Gen 7 Heroes (Bradley, Edith, Gordon)", "Hero"),
            (450, "Chief Gear T4 & Legendary Charms", "Gear"),
            (480, "Gen 8 Heroes (Hendrik, Gatot, Sonya) & Pet Gen 7", "Hero"),
            (500, "Fire Crystal 9–10 Age", "Fire Crystal"),
            (550, "Gen 9 Heroes (Magnus, Fred, Xura)", "Hero"),
            (620, "Gen 10 Heroes (Blanchette, Gregory, Freya)", "Hero"),
            (690, "Gen 11 Heroes (Eleonora, Lloyd, Rufus)", "Hero"),
            (750, "Fire Crystal 11–12 & T12 Troops", "Fire Crystal"),
            (760, "Gen 12 Heroes (Ligeia, Hervor, Karol)", "Hero"),
            (830, "Gen 13 Heroes (Gisela, Flora, Vulcanus)", "Hero"),
            (900, "Gen 14 Heroes (Cara, Elif, Dominic)", "Hero"),
            (960, "Gen 15 Heroes (Hank, Estrella, Viveca)", "Hero"),
            (1160, "Gen 16 Heroes (Seigel, Ursar, Aisling)", "Hero"),
            (1240, "Gen 17 Heroes (Aiden, Bertha, Eleanor)", "Hero"),
        ]

    unlocked = [m for m in milestones if age >= m[0]]
    upcoming = [m for m in milestones if age < m[0]]
    next_m = upcoming[0] if upcoming else None

    # Dynamic Gen calculation from heroes_data.json if present
    gen_unlocks = {}
    if os.path.exists("heroes_data.json"):
        try:
            with open("heroes_data.json", "r", encoding="utf-8") as f:
                h_data = json.load(f)
                for g_item in h_data:
                    gen_num = g_item.get("gen", 0)
                    day_val = g_item.get("unlock_day", 0)
                    if gen_num > 0:
                        gen_unlocks[gen_num] = day_val
        except Exception:
            pass

    if not gen_unlocks:
        gen_unlocks = {
            1: 0, 2: 40, 3: 120, 4: 180, 5: 250, 6: 320, 7: 400, 8: 480,
            9: 550, 10: 620, 11: 690, 12: 760, 13: 830, 14: 900, 15: 960, 16: 1160, 17: 1240
        }

    cur_gen = 1
    for g in sorted(gen_unlocks.keys(), reverse=True):
        if age >= gen_unlocks[g]:
            cur_gen = g
            break

    return {
        "age": age,
        "gen": cur_gen,
        "unlocked_count": len(unlocked),
        "total_count": len(milestones),
        "recent_unlocked": [m[1] for m in unlocked[-3:]],
        "next_milestone": next_m,
        "days_to_next": (next_m[0] - age) if next_m else None
    }


@bot.tree.command(name="state", description="Check state timeline, server age, unlocked features, and upcoming milestones.")
@app_commands.describe(state_or_days="Enter your State Number (e.g. 750) or direct server age in days (e.g. 450d)")
async def slash_state(interaction: discord.Interaction, state_or_days: str):
    await interaction.response.defer(thinking=True)
    raw = state_or_days.lower().replace("state", "").replace("s", "").replace("d", "").replace("days", "").strip()
    val = int(raw) if raw.isdigit() else 750
    is_days = "d" in state_or_days.lower() or "day" in state_or_days.lower()

    t = calculate_state_telemetry(val, is_state_number=not is_days)

    embed = discord.Embed(
        title=f"⏱️ Whiteout Survival State Timeline — {'State #' + str(val) if not is_days else 'Server Day ' + str(val)}",
        description=f"**Estimated Server Age:** `Day ~{t['age']}`\n**Current Active Generation:** `Generation {t['gen']}`",
        color=FROSTY_COLOR
    )

    if t['recent_unlocked']:
        embed.add_field(
            name="✅ Recently Unlocked Features",
            value="\n".join([f"• {item}" for item in t['recent_unlocked']]),
            inline=False
        )

    if t['next_milestone']:
        embed.add_field(
            name="⏳ Next Major Milestone",
            value=f"• **{t['next_milestone'][1]}**\n• Unlocks on **Day {t['next_milestone'][0]}** (*in ~{t['days_to_next']} days*)",
            inline=False
        )

    embed.add_field(
        name="📜 Feature Progress",
        value=f"**{t['unlocked_count']}/{t['total_count']}** verified timeline features unlocked.",
        inline=False
    )
    embed.set_footer(text="💡 Tip: Check your Monument 'Kindling Embers' task for exact Day 1 launch date.")
    await interaction.followup.send(embed=embed)


# --- Utility Calculation Helpers ---
def load_utility_data() -> Dict[str, Any]:
    json_path = os.path.join(os.path.dirname(__file__), "utility_data.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

FC_BUILDING_TABLE = {
    1: (600, 0, 350, 0, 8),
    2: (1200, 0, 700, 0, 12),
    3: (2000, 0, 1150, 0, 16),
    4: (3200, 0, 1800, 0, 22),
    5: (4800, 0, 2700, 0, 30),
    6: (2500, 180, 1400, 100, 40),
    7: (3500, 320, 1950, 180, 52),
    8: (5000, 550, 2800, 300, 65),
    9: (7000, 850, 3900, 480, 80),
    10: (10000, 1300, 5500, 720, 100),
    11: (14000, 1900, 7800, 1050, 120),
    12: (19500, 2700, 11000, 1500, 145),
}

CHARM_TABLE = {
    1: (10, 0, 2.5, 7000),
    2: (25, 5, 5.5, 17500),
    3: (50, 15, 9.0, 35000),
    4: (90, 30, 14.0, 63000),
    5: (150, 55, 20.5, 105000),
    6: (240, 95, 28.5, 168000),
    7: (360, 150, 38.0, 252000),
    8: (520, 230, 50.0, 364000),
    9: (720, 340, 64.5, 504000),
    10: (980, 490, 82.0, 686000),
    11: (1300, 680, 105.0, 910000),
    12: (1750, 920, 132.0, 1225000),
}

SVS_RATES = {
    "fc": {"name": "Fire Crystals", "rate": 2000, "unit": "FC", "best_day": "Day 1 (City Construction) & Day 5 (Power Boost)"},
    "rfc": {"name": "Refined Fire Crystals", "rate": 30000, "unit": "RFC", "best_day": "Day 1 (City Construction) & Day 5 (Power Boost)"},
    "speedup_min": {"name": "Speedups (Minutes)", "rate": 30, "unit": "mins", "best_day": "Day 1 (Building), Day 2 (Research), Day 5 (All)"},
    "speedup_hr": {"name": "Speedups (Hours)", "rate": 1800, "unit": "hrs", "best_day": "Day 1 (Building), Day 2 (Research), Day 5 (All)"},
    "fc_shard": {"name": "FC Shards (Helios Research)", "rate": 1000, "unit": "shards", "best_day": "Day 2 (Research Day) & Day 5 (Power Boost)"},
    "lucky_wheel": {"name": "Lucky Wheel Spins", "rate": 4000, "unit": "spins", "best_day": "Day 2 (Research Day)"},
    "hero_shard": {"name": "Mythic Hero Shards", "rate": 6000, "unit": "shards", "best_day": "Day 2 (Research Day)"},
    "expert_sigil": {"name": "Dawn Expert Sigils", "rate": 6000, "unit": "sigils", "best_day": "Day 2 (Research Day)"},
    "polar_terror": {"name": "Polar Terror Rallies", "rate": 30000, "unit": "rallies", "best_day": "Day 3 (Beast Slay) — Best F2P Points!"},
    "mithril": {"name": "Mithril (Exclusive Gear)", "rate": 144000, "unit": "mithril", "best_day": "Day 4 (Hero Dev) & Day 5 (Power Boost) — Highest Value!"},
    "t10_train": {"name": "T10 Troops Trained", "rate": 60, "unit": "troops", "best_day": "Day 4 (Hero Dev / Troops)"},
    "t11_train": {"name": "T11 Troops Trained", "rate": 75, "unit": "troops", "best_day": "Day 4 (Hero Dev / Troops)"},
    "t12_train": {"name": "T12 Troops Trained", "rate": 90, "unit": "troops", "best_day": "Day 4 (Hero Dev / Troops)"},
}


def calculate_fc_cost(building_type: str, start_lvl: int, target_lvl: int) -> Dict[str, Any]:
    util_data = load_utility_data()
    raw_table = util_data.get("fc_table", {})
    
    is_furnace = "furnace" in building_type.lower() or "embassy" in building_type.lower() or "command" in building_type.lower()
    total_fc = 0
    total_rfc = 0
    total_days = 0

    max_lvl = max([int(k) for k in raw_table.keys()] + [12]) if raw_table else 12

    for lvl in range(max(1, start_lvl + 1), min(max_lvl + 1, target_lvl + 1)):
        row_data = raw_table.get(str(lvl))
        if row_data:
            if is_furnace:
                total_fc += row_data.get("furnace_fc", 0)
                total_rfc += row_data.get("furnace_rfc", 0)
            else:
                total_fc += row_data.get("camp_fc", 0)
                total_rfc += row_data.get("camp_rfc", 0)
            total_days += row_data.get("days", 0)
        else:
            row = FC_BUILDING_TABLE.get(lvl, (0, 0, 0, 0, 0))
            if is_furnace:
                total_fc += row[0]
                total_rfc += row[1]
            else:
                total_fc += row[2]
                total_rfc += row[3]
            total_days += row[4]

    svs_pts = (total_fc * 2000) + (total_rfc * 30000)
    return {
        "building": "Furnace / Embassy / Command Center" if is_furnace else "Troop Camp (Inf/Lan/Mar)",
        "from": start_lvl,
        "to": target_lvl,
        "fc": total_fc,
        "rfc": total_rfc,
        "days": total_days,
        "svs_pts": svs_pts
    }


def calculate_charms_cost(start_lvl: int, target_lvl: int) -> Dict[str, Any]:
    util_data = load_utility_data()
    raw_table = util_data.get("charm_table", {})

    total_guides = 0
    total_designs = 0
    total_svs = 0
    total_boost = 0.0

    max_lvl = max([int(k) for k in raw_table.keys()] + [12]) if raw_table else 12

    for lvl in range(max(1, start_lvl + 1), min(max_lvl + 1, target_lvl + 1)):
        row_data = raw_table.get(str(lvl))
        if row_data:
            total_guides += row_data.get("guides", 0)
            total_designs += row_data.get("designs", 0)
            total_boost += float(row_data.get("boost", 0.0))
            total_svs += row_data.get("svs_pts", 0)
        else:
            row = CHARM_TABLE.get(lvl, (0, 0, 0.0, 0))
            total_guides += row[0]
            total_designs += row[1]
            total_boost += row[2]
            total_svs += row[3]

    return {
        "from": start_lvl,
        "to": target_lvl,
        "guides": total_guides,
        "designs": total_designs,
        "boost": total_boost,
        "svs_pts": total_svs
    }


def calculate_transfer_passes(power_m: float) -> Tuple[int, str]:
    if power_m < 30:
        return 1, "Ordinary Transfer"
    elif power_m < 50:
        return 2, "Ordinary Transfer"
    elif power_m < 75:
        return 3, "Ordinary Transfer"
    elif power_m < 100:
        return 5, "Ordinary Transfer"
    elif power_m < 130:
        return 8, "Ordinary Transfer"
    elif power_m < 170:
        return 12, "Ordinary Transfer"
    elif power_m < 220:
        return 18, "Ordinary Transfer"
    elif power_m < 280:
        return 25, "Ordinary Transfer"
    elif power_m < 350:
        return 35, "High Power Transfer"
    elif power_m < 450:
        return 50, "High Power Transfer"
    elif power_m < 600:
        return 65, "Top Tier Transfer"
    else:
        return 80, "Whale Transfer (Requires State President Leading Invite)"


def parse_utc_time_or_duration(time_str: str) -> Optional[datetime]:
    now_utc = datetime.now(timezone.utc)
    s = time_str.strip().lower()

    if "in " in s or "h" in s or "m" in s or "d" in s:
        hours, minutes, days = 0, 0, 0
        h_match = re.search(r'(\d+)\s*h', s)
        m_match = re.search(r'(\d+)\s*m', s)
        d_match = re.search(r'(\d+)\s*d', s)
        if h_match: hours = int(h_match.group(1))
        if m_match: minutes = int(m_match.group(1))
        if d_match: days = int(d_match.group(1))

        if hours > 0 or minutes > 0 or days > 0:
            return now_utc + timedelta(days=days, hours=hours, minutes=minutes)

    clean = s.replace("utc", "").strip()
    try:
        parts = clean.split(":")
        if len(parts) >= 2:
            hr = int(parts[0])
            mn = int(parts[1])
            target = now_utc.replace(hour=hr, minute=mn, second=0, microsecond=0)
            if target <= now_utc:
                target += timedelta(days=1)
            return target
    except Exception:
        pass

    return None


# ==========================================
# 💎 UTILITY SLASH COMMANDS
# ==========================================

@bot.tree.command(name="fc", description="Calculate Fire Crystal (FC & RFC) costs, speedups, and SvS points.")
@app_commands.describe(
    building="Type of building to upgrade",
    from_level="Current FC level (0 for Lv 30, or 1 to 9)",
    to_level="Target FC level (1 to 10)"
)
@app_commands.choices(building=[
    app_commands.Choice(name="Furnace / Embassy / Command Center", value="furnace"),
    app_commands.Choice(name="Troop Camp (Infantry / Lancer / Marksman)", value="camp"),
])
async def slash_fc(interaction: discord.Interaction, building: app_commands.Choice[str], from_level: int, to_level: int):
    if from_level >= to_level:
        await interaction.response.send_message("❌ Target level must be greater than current level.", ephemeral=True)
        return

    res = calculate_fc_cost(building.value, from_level, to_level)
    embed = discord.Embed(
        title=f"💎 Fire Crystal Upgrade Calculator — {res['building']}",
        description=f"Upgrade Plan: **FC {res['from']} ➔ FC {res['to']}**",
        color=FROSTY_COLOR
    )
    embed.add_field(name="Regular Fire Crystals (FC)", value=f"💎 **{res['fc']:,} FC**", inline=True)
    if res['rfc'] > 0:
        embed.add_field(name="Refined Fire Crystals (RFC)", value=f"🔮 **{res['rfc']:,} RFC**", inline=True)
    embed.add_field(name="Base Build Time", value=f"⏱️ **~{res['days']} Days**", inline=True)
    embed.add_field(name="SvS City Construction Points", value=f"🏆 **{res['svs_pts']:,} Points** *(Day 1 / Day 5)*", inline=False)
    embed.set_footer(text="💡 Tip: Start construction on SvS Day 1 for maximum score contribution.")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="charms", description="Calculate Chief Charms materials, guides, and SvS points.")
@app_commands.describe(
    from_level="Current Charm level (0 for unequipped, or 1 to 10)",
    to_level="Target Charm level (1 to 11)"
)
async def slash_charms(interaction: discord.Interaction, from_level: int, to_level: int):
    if from_level >= to_level:
        await interaction.response.send_message("❌ Target level must be greater than current level.", ephemeral=True)
        return

    res = calculate_charms_cost(from_level, to_level)
    embed = discord.Embed(
        title="🛡️ Chief Charms Upgrade Calculator (Per Slot)",
        description=f"Upgrade Plan: **Level {res['from']} ➔ Level {res['to']}**",
        color=FROSTY_COLOR
    )
    embed.add_field(name="Charm Guides", value=f"📜 **{res['guides']:,} Guides**", inline=True)
    embed.add_field(name="Charm Designs", value=f"✨ **{res['designs']:,} Designs**", inline=True)
    embed.add_field(name="Total Combat Boost", value=f"⚡ **+{res['boost']:.1f}% Lethality/HP**", inline=True)
    embed.add_field(name="SvS Prep Points", value=f"🏆 **{res['svs_pts']:,} Points** *(70 pts / score)*", inline=False)
    embed.set_footer(text="💡 Tip: Charm score earns points on SvS Day 1, Day 3, and Day 4.")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="svs", description="Calculate SvS prep phase points and find the highest-value day.")
@app_commands.describe(
    activity="Select activity",
    amount="Quantity of items or hours"
)
@app_commands.choices(activity=[
    app_commands.Choice(name="💎 Fire Crystals used (FC)", value="fc"),
    app_commands.Choice(name="🔮 Refined Fire Crystals (RFC)", value="rfc"),
    app_commands.Choice(name="⏱️ General / Build Speedups (Hours)", value="speedup_hr"),
    app_commands.Choice(name="📜 FC Shards (Helios Research)", value="fc_shard"),
    app_commands.Choice(name="🎡 Lucky Wheel Spins", value="lucky_wheel"),
    app_commands.Choice(name="👑 Mythic Hero Shards", value="hero_shard"),
    app_commands.Choice(name="🐻 Polar Terror Rallies", value="polar_terror"),
    app_commands.Choice(name="🗡️ Mithril (Exclusive Gear)", value="mithril"),
    app_commands.Choice(name="⚔️ T10 Troop Training", value="t10_train"),
    app_commands.Choice(name="⚡ T11 Troop Training", value="t11_train"),
])
async def slash_svs(interaction: discord.Interaction, activity: app_commands.Choice[str], amount: int):
    info = SVS_RATES.get(activity.value, {"name": activity.name, "rate": 1, "unit": "units", "best_day": "Day 5"})
    pts = amount * info["rate"]

    embed = discord.Embed(
        title="🏆 SvS Prep Phase Points Calculator",
        description=f"**Activity:** `{info['name']}`\n**Quantity:** `{amount:,} {info['unit']}`",
        color=SUCCESS_COLOR
    )
    embed.add_field(name="Total SvS Points Earned", value=f"🌟 **{pts:,} Points**", inline=False)
    embed.add_field(name="Optimal Day to Use", value=f"📅 **{info['best_day']}**", inline=False)
    embed.set_footer(text="Frosty AI • State vs State Tactical Intelligence")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="transfer", description="Calculate required State Transfer Passes based on Chief Power.")
@app_commands.describe(power_millions="Your Chief Power in Millions (e.g. 150 for 150M Power)")
async def slash_transfer(interaction: discord.Interaction, power_millions: float):
    passes, tier = calculate_transfer_passes(power_millions)
    embed = discord.Embed(
        title="🚀 State Transfer Pass Calculator",
        description=f"**Chief Power:** `{power_millions:.1f}M Power`\n**Transfer Tier:** `{tier}`",
        color=FROSTY_COLOR
    )
    embed.add_field(name="Required Transfer Passes", value=f"🎫 **{passes} Passes**", inline=False)
    embed.add_field(
        name="Transfer Requirements",
        value="• Furnace Lv 25 minimum\n• Empty Infirmary & no active marches\n• 30-Day Transfer cooldown satisfied\n• Target state must have open quota in your state bracket",
        inline=False
    )
    embed.set_footer(text="Check transfer.foxfiver.com for live state group brackets.")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="codes", description="View active Whiteout Survival gift codes and redemption link.")
async def slash_codes(interaction: discord.Interaction):
    codes = load_utility_data().get("gift_codes", ACTIVE_GIFT_CODES)
    embed = discord.Embed(
        title="🎁 Whiteout Survival Active Gift Codes",
        description="Redeem these codes for free Gems, Speedups, Gold Keys, and Stamina:",
        color=SUCCESS_COLOR
    )
    for c in codes:
        embed.add_field(name=f"🔑 `{c['code']}`", value=f"Rewards: {c['rewards']}", inline=False)

    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        label="🌐 Redeem Codes Portal",
        url="https://wos-giftcode.centurygame.com/",
        style=discord.ButtonStyle.link,
        emoji="🎁"
    ))
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="timer", description="Manage UTC alliance countdown timers (up to 5 active).")
@app_commands.describe(
    action="Set, View, or Delete a timer",
    event="Select event (for 'set')",
    time_utc="Time in UTC (e.g. 19:00 UTC, or 'in 2h 30m', '45m')",
    timer_id="Timer ID (for 'delete')"
)
@app_commands.choices(
    action=[
        app_commands.Choice(name="Set Timer", value="set"),
        app_commands.Choice(name="List Active Timers", value="list"),
        app_commands.Choice(name="Delete Timer", value="delete"),
    ],
    event=[
        app_commands.Choice(name="Foundry Battle", value="Foundry Battle"),
        app_commands.Choice(name="Canyon Clash", value="Canyon Clash"),
        app_commands.Choice(name="SVS Battle Phase", value="SVS Battle Phase"),
        app_commands.Choice(name="Bear Trap", value="Bear Trap"),
        app_commands.Choice(name="Fortress Battle", value="Fortress Battle"),
    ]
)
async def slash_timer(
    interaction: discord.Interaction,
    action: app_commands.Choice[str],
    event: Optional[app_commands.Choice[str]] = None,
    time_utc: Optional[str] = None,
    timer_id: Optional[int] = None
):
    global _timer_counter
    key = interaction.guild_id or interaction.channel_id
    if key not in ACTIVE_TIMERS:
        ACTIVE_TIMERS[key] = []

    timers = ACTIVE_TIMERS[key]

    if action.value == "set":
        if not event or not time_utc:
            await interaction.response.send_message("❌ Please specify both `event` and `time_utc` (e.g. `19:00 UTC` or `in 2h 30m`).", ephemeral=True)
            return

        if len(timers) >= 5:
            await interaction.response.send_message("⚠️ Maximum limit of **5 active timers** reached for this server/channel. Delete an old timer first.", ephemeral=True)
            return

        target_dt = parse_utc_time_or_duration(time_utc)
        if not target_dt:
            await interaction.response.send_message("❌ Invalid time format. Examples: `19:00 UTC`, `in 2h 30m`, `45m`.", ephemeral=True)
            return

        new_t = {
            "id": _timer_counter,
            "event": event.value,
            "target_time": target_dt,
            "channel_id": interaction.channel_id,
            "user_id": interaction.user.id
        }
        _timer_counter += 1
        timers.append(new_t)

        ts_unix = int(target_dt.timestamp())
        embed = discord.Embed(
            title=f"⏰ Alliance Timer Created — #{new_t['id']}",
            description=f"**Event:** `{new_t['event']}`\n**Target Time:** <t:{ts_unix}:F> (<t:{ts_unix}:R>)\n**Set By:** {interaction.user.mention}",
            color=SUCCESS_COLOR
        )
        embed.set_footer(text=f"Active timers: {len(timers)}/5 • Alerts will mention @here when timer expires")
        await interaction.response.send_message(embed=embed)

    elif action.value == "list":
        if not timers:
            await interaction.response.send_message("ℹ️ No active alliance timers in this server. Use `/timer set` to create one!", ephemeral=True)
            return

        embed = discord.Embed(title="⏰ Active Alliance Timers", color=FROSTY_COLOR)
        for t in timers:
            ts = int(t["target_time"].timestamp())
            embed.add_field(
                name=f"#{t['id']} — {t['event']}",
                value=f"• Starts: <t:{ts}:F>\n• Countdown: <t:{ts}:R>\n• Creator: <@{t['user_id']}>",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    elif action.value == "delete":
        if timer_id is None:
            await interaction.response.send_message("❌ Please provide the `timer_id` to delete.", ephemeral=True)
            return

        found = next((t for t in timers if t["id"] == timer_id), None)
        if found:
            timers.remove(found)
            await interaction.response.send_message(f"✅ Timer **#{timer_id}** (`{found['event']}`) deleted successfully.")
        else:
            await interaction.response.send_message(f"❌ Timer **#{timer_id}** not found.", ephemeral=True)


@bot.tree.command(name="help", description="Show Frosty AI commands and strategic capabilities.")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="❄️ Frosty AI - Tactical Command Center",
        description="Welcome Chief! I am **Frosty**, your tactical AI advisor for Whiteout Survival.\nUse either `/` Slash Commands or `!` prefix commands:",
        color=FROSTY_COLOR
    )
    embed.add_field(name="⚔️ `/wos [question]` or `!wos`", value="Ask any strategic question (e.g. *'what is a hero lineup'*, *'Flint vs Jeronimo'*).", inline=False)
    embed.add_field(name="💎 `/fc [building] [from] [to]` or `!fc`", value="Fire Crystal (FC & RFC) upgrade calculator & SvS points.", inline=True)
    embed.add_field(name="🛡️ `/charms [from] [to]` or `!charms`", value="Chief Charms material cost, guides, and combat boosts.", inline=True)
    embed.add_field(name="🏆 `/svs [activity] [amount]` or `!svs`", value="Calculate SvS prep phase points & find the best day.", inline=True)
    embed.add_field(name="⏰ `/timer [set/list/delete]` or `!timer`", value="Set up to 5 UTC alliance countdowns (Foundry, Canyon, SvS, Bear, Fortress).", inline=True)
    embed.add_field(name="🚀 `/transfer [power]` or `!transfer`", value="State Transfer Pass calculator & eligibility rules.", inline=True)
    embed.add_field(name="🎁 `/codes` or `!codes`", value="Active Whiteout Survival gift codes & redemption portal.", inline=True)
    embed.add_field(name="⏱️ `/state [number]` or `!state`", value="Server age, unlocked features (FC, Pets, SvS), and milestones.", inline=True)
    embed.add_field(name="👑 `/hero [name]` or `!hero`", value="Hero skill breakdowns, exclusive gear, and tier evaluations.", inline=True)
    embed.add_field(name="🐻 `/bear` or `!bear`", value="Bear Trap rally leader setups & Jessie joiner damage buffs.", inline=True)
    embed.add_field(name="📊 `/status` or `!status`", value="Bot system health, latency, AI engine, and indexed archives.", inline=True)
    embed.set_footer(text="Frosty AI • Powered by Google Gemini & ChromaDB")
    await interaction.response.send_message(embed=embed)


# ==========================================
# ⌨️ PREFIX COMMANDS (Backwards Compatibility)
# ==========================================

@bot.command(name="wos")
async def prefix_wos(ctx, *, question: str):
    async with ctx.typing():
        embed, view = await generate_frosty_response(ctx.channel.id, ctx.author, question)
        await ctx.send(embed=embed, view=view)


@bot.command(name="fc")
async def prefix_fc(ctx, *, args: str = "furnace 0 5"):
    parts = args.strip().split()
    b_type = "furnace"
    from_lvl, to_lvl = 0, 5
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        from_lvl, to_lvl = int(parts[0]), int(parts[1])
    elif len(parts) >= 3:
        b_type = parts[0]
        from_lvl = int(parts[1]) if parts[1].isdigit() else 0
        to_lvl = int(parts[2]) if parts[2].isdigit() else 5

    res = calculate_fc_cost(b_type, from_lvl, to_lvl)
    embed = discord.Embed(
        title=f"💎 Fire Crystal Upgrade Calculator — {res['building']}",
        description=f"Upgrade Plan: **FC {res['from']} ➔ FC {res['to']}**",
        color=FROSTY_COLOR
    )
    embed.add_field(name="Regular Fire Crystals (FC)", value=f"💎 **{res['fc']:,} FC**", inline=True)
    if res['rfc'] > 0:
        embed.add_field(name="Refined Fire Crystals (RFC)", value=f"🔮 **{res['rfc']:,} RFC**", inline=True)
    embed.add_field(name="Base Build Time", value=f"⏱️ **~{res['days']} Days**", inline=True)
    embed.add_field(name="SvS City Construction Points", value=f"🏆 **{res['svs_pts']:,} Points** *(Day 1 / Day 5)*", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="charms")
async def prefix_charms(ctx, *, args: str = "0 5"):
    parts = [int(p) for p in args.strip().split() if p.isdigit()]
    from_lvl = parts[0] if len(parts) >= 1 else 0
    to_lvl = parts[1] if len(parts) >= 2 else 5

    res = calculate_charms_cost(from_lvl, to_lvl)
    embed = discord.Embed(
        title="🛡️ Chief Charms Upgrade Calculator (Per Slot)",
        description=f"Upgrade Plan: **Level {res['from']} ➔ Level {res['to']}**",
        color=FROSTY_COLOR
    )
    embed.add_field(name="Charm Guides", value=f"📜 **{res['guides']:,} Guides**", inline=True)
    embed.add_field(name="Charm Designs", value=f"✨ **{res['designs']:,} Designs**", inline=True)
    embed.add_field(name="Total Combat Boost", value=f"⚡ **+{res['boost']:.1f}% Lethality/HP**", inline=True)
    embed.add_field(name="SvS Prep Points", value=f"🏆 **{res['svs_pts']:,} Points** *(70 pts / score)*", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="svs")
async def prefix_svs(ctx, *, args: str = "fc 1000"):
    parts = args.strip().split()
    act = parts[0].lower() if parts else "fc"
    amt = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1000

    info = SVS_RATES.get(act, SVS_RATES["fc"])
    pts = amt * info["rate"]

    embed = discord.Embed(
        title="🏆 SvS Prep Phase Points Calculator",
        description=f"**Activity:** `{info['name']}`\n**Quantity:** `{amt:,} {info['unit']}`",
        color=SUCCESS_COLOR
    )
    embed.add_field(name="Total SvS Points Earned", value=f"🌟 **{pts:,} Points**", inline=False)
    embed.add_field(name="Optimal Day to Use", value=f"📅 **{info['best_day']}**", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="transfer")
async def prefix_transfer(ctx, *, power: str = "150"):
    raw = re.sub(r'[^0-9.]', '', power)
    p_val = float(raw) if raw else 150.0
    passes, tier = calculate_transfer_passes(p_val)
    embed = discord.Embed(
        title="🚀 State Transfer Pass Calculator",
        description=f"**Chief Power:** `{p_val:.1f}M Power`\n**Transfer Tier:** `{tier}`",
        color=FROSTY_COLOR
    )
    embed.add_field(name="Required Transfer Passes", value=f"🎫 **{passes} Passes**", inline=False)
    embed.add_field(
        name="Transfer Requirements",
        value="• Furnace Lv 25 minimum\n• Empty Infirmary & no active marches\n• 30-Day Transfer cooldown satisfied",
        inline=False
    )
    await ctx.send(embed=embed)


@bot.command(name="codes")
async def prefix_codes(ctx):
    codes = load_utility_data().get("gift_codes", ACTIVE_GIFT_CODES)
    embed = discord.Embed(
        title="🎁 Whiteout Survival Active Gift Codes",
        description="Redeem these codes for free Gems, Speedups, Gold Keys, and Stamina:",
        color=SUCCESS_COLOR
    )
    for c in codes:
        embed.add_field(name=f"🔑 `{c['code']}`", value=f"Rewards: {c['rewards']}", inline=False)
    embed.set_footer(text="Redeem at https://wos-giftcode.centurygame.com/")
    await ctx.send(embed=embed)


@bot.command(name="timer")
async def prefix_timer(ctx, *, args: str = "list"):
    global _timer_counter
    key = ctx.guild.id if ctx.guild else ctx.channel.id
    if key not in ACTIVE_TIMERS:
        ACTIVE_TIMERS[key] = []
    timers = ACTIVE_TIMERS[key]

    parts = args.strip().split(maxsplit=2)
    sub = parts[0].lower() if parts else "list"

    if sub in ["set", "add"] and len(parts) >= 3:
        if len(timers) >= 5:
            await ctx.send("⚠️ Maximum limit of 5 active timers reached.")
            return

        ev_name = parts[1]
        t_str = parts[2]
        target_dt = parse_utc_time_or_duration(t_str)
        if not target_dt:
            await ctx.send("❌ Invalid time format. Examples: `!timer set BearTrap in 2h 30m` or `!timer set Foundry 19:00 UTC`")
            return

        new_t = {
            "id": _timer_counter,
            "event": ev_name,
            "target_time": target_dt,
            "channel_id": ctx.channel.id,
            "user_id": ctx.author.id
        }
        _timer_counter += 1
        timers.append(new_t)
        ts_unix = int(target_dt.timestamp())
        await ctx.send(f"⏰ **Timer #{new_t['id']} set for {ev_name}** (<t:{ts_unix}:R> at <t:{ts_unix}:F>)!")

    elif sub in ["delete", "remove", "del"] and len(parts) >= 2 and parts[1].isdigit():
        t_id = int(parts[1])
        found = next((t for t in timers if t["id"] == t_id), None)
        if found:
            timers.remove(found)
            await ctx.send(f"✅ Timer **#{t_id}** deleted.")
        else:
            await ctx.send(f"❌ Timer **#{t_id}** not found.")

    else:
        if not timers:
            await ctx.send("ℹ️ No active timers. Use `!timer set <event> <time>` (e.g. `!timer set BearTrap in 45m`).")
            return
        embed = discord.Embed(title="⏰ Active Alliance Timers", color=FROSTY_COLOR)
        for t in timers:
            ts = int(t["target_time"].timestamp())
            embed.add_field(name=f"#{t['id']} — {t['event']}", value=f"• Starts: <t:{ts}:F>\n• Countdown: <t:{ts}:R>", inline=False)
        await ctx.send(embed=embed)


@bot.command(name="timers")
async def prefix_timers_alias(ctx):
    await prefix_timer(ctx, args="list")


# --- Error Handling ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Missing argument. Example: `{COMMAND_PREFIX}wos what is a hero lineup`")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        logger.error(f"Command error: {error}")
        await ctx.send(f"⚠️ Error executing command: `{str(error)}`")


if __name__ == "__main__":
    if not DISCORD_TOKEN or DISCORD_TOKEN == "your_discord_bot_token_here":
        logger.error("❌ DISCORD_TOKEN is not configured in .env! Please set your token.")
        print("\n[ERROR] DISCORD_TOKEN is missing or not set in .env file.")
        print("Please copy .env.example to .env and insert your valid Discord bot token.\n")
    else:
        bot.run(DISCORD_TOKEN)
