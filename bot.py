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
import unicodedata
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Tuple, Any

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

from ai_engine import AIEngine
from knowledge_base import KnowledgeBase, KNOWN_HEROES, KNOWN_EVENTS, KNOWN_EXPERTS
from ingest import run_full_reindex
from wos_giftcode_api import redeem_gift_code, ERROR_CODE_MESSAGES
import registered_players
from sync_data import scrape_online_gift_codes

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("FrostyAI")

# Load environment
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!").strip() or "!"
ADMIN_USER_IDS = [int(uid.strip()) for uid in os.getenv("ADMIN_USER_IDS", "").split(",") if uid.strip().isdigit()]

# ==============================================================================
# 👑 BOT ADMIN & OWNER CONFIGURATION
# To change or add authorized admins, simply add usernames or IDs below!
# Anyone sharing or self-hosting this bot can put their own Discord username here.
# ==============================================================================
AUTHORIZED_ADMIN_USERNAMES = [
    "zcross071",      # Supreme Commander / Bot Owner
]

AUTHORIZED_ADMIN_IDS = [
    # Optional: Put your numeric Discord User ID here (e.g. 123456789012345678)
]

def is_authorized_admin(user: discord.User | discord.Member) -> bool:
    """Check if the user is an authorized bot owner by username or numerical ID."""
    uname = getattr(user, "name", "").lower().strip()
    gname = getattr(user, "global_name", "")
    gname = gname.lower().strip() if gname else ""

    for admin_u in AUTHORIZED_ADMIN_USERNAMES:
        clean_target = admin_u.lower().strip()
        if clean_target and (clean_target == uname or clean_target == gname):
            return True

    if user.id in AUTHORIZED_ADMIN_IDS or user.id in ADMIN_USER_IDS:
        return True

    return False

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
    {"code": "gogoWOS", "status": "🟢 Active & Verified", "rewards": "500 Gems, 2x Gold Keys, 10,000 Hero XP, 20x 5m Speedups"},
    {"code": "OFFICIALSTORE", "status": "⚡ Webstore Event Code", "rewards": "1,000 Gems, 5x 1h Speedups, 10x Gold Keys, Stamina Potions"},
    {"code": "GuDokYTKOR", "status": "⚡ Limited Event Code", "rewards": "300 Gems, 5x 1h Speedups, 2,000 Hero XP"},
    {"code": "2ndYoutubeKR", "status": "⚡ Limited Event Code", "rewards": "300 Gems, 5x 1h Speedups, 2,000 Hero XP"},
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
    if not auto_sync_gift_codes.is_running():
        auto_sync_gift_codes.start()
    bot.add_view(CodesActionView())


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


# Calibrated Whiteout Survival Historical Launch Anchor Points (State Number, Launch Date UTC)
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


def calculate_state_telemetry(input_val: int, is_state_number: bool = True) -> Dict:
    """Calculates State Age, Generation, Active Heroes, Unlocked Features, and Next Milestone."""
    now_dt = datetime.now()
    if is_state_number:
        launch_date = estimate_state_launch_date(input_val)
        age = (now_dt - launch_date).days
        age = max(0, min(3000, age))
    else:
        launch_date = now_dt - timedelta(days=input_val)
        age = max(0, min(3000, input_val))

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
            (34, "Arena Pool Expansion", "Event"),
            (39, "Fertile Land Opens", "Event"),
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
            (180, "Legendary Chief Gear", "Gear"),
            (195, "Gen 4 Heroes (Lynn, Ahmose, Reina)", "Hero"),
            (200, "Pet Gen 4 (Cave Lion, Snow Ape)", "Pet"),
            (220, "War Academy & T11 Troops", "Academy"),
            (270, "Gen 5 Heroes (Hector, Norah, Gwen)", "Hero"),
            (280, "Pet Gen 5 (Iron Rhino, Saber-tooth)", "Pet"),
            (315, "Fire Crystal 6–8 Age", "Fire Crystal"),
            (360, "Gen 6 Heroes (Renee, Wayne, Wu Ming)", "Hero"),
            (370, "Mammoth Pet Update", "Pet"),
            (440, "Gen 7 Heroes (Bradley, Edith, Gordon)", "Hero"),
            (450, "Chief Gear T4 & Legendary Charms", "Gear"),
            (500, "Fire Crystal 9–10 Age", "Fire Crystal"),
            (520, "Gen 8 Heroes (Hendrik, Gatot, Sonya) & Pet Gen 7", "Hero"),
            (600, "Gen 9 Heroes (Magnus, Fred, Xura)", "Hero"),
            (700, "Gen 10 Heroes (Blanchette, Gregory, Freya)", "Hero"),
            (750, "Fire Crystal 11–12 & T12 Troops", "Fire Crystal"),
            (800, "Gen 11 Heroes (Eleonora, Lloyd, Rufus)", "Hero"),
            (870, "Gen 12 Heroes (Ligeia, Hervor, Karol)", "Hero"),
            (951, "Gen 13 Heroes (Gisela, Flora, Vulcanus)", "Hero"),
            (1030, "Gen 14 Heroes (Cara, Elif, Dominic)", "Hero"),
            (1115, "Gen 15 Heroes (Hank, Estrella, Viveca)", "Hero"),
            (1220, "Gen 16 Heroes (Seigel, Ursar, Aisling)", "Hero"),
            (1280, "Gen 17 Heroes (Aiden, Bertha, Eleanor)", "Hero"),
        ]

    unlocked = [m for m in milestones if age >= m[0]]
    upcoming = [m for m in milestones if age < m[0]]
    next_m = upcoming[0] if upcoming else None

    # Calibrated generation schedule (matching State 266 @ Gen 15, Gen 16 in ~2.5 months)
    gen_unlocks = {
        1: 0, 2: 40, 3: 120, 4: 195, 5: 270, 6: 360, 7: 440, 8: 520,
        9: 600, 10: 700, 11: 800, 12: 870, 13: 951, 14: 1030, 15: 1115, 16: 1220, 17: 1280
    }

    cur_gen = 1
    for g in sorted(gen_unlocks.keys(), reverse=True):
        if age >= gen_unlocks[g]:
            cur_gen = g
            break

    # Calculate days to next generation
    next_gen = cur_gen + 1 if (cur_gen + 1) in gen_unlocks else None
    days_to_next_gen = (gen_unlocks[next_gen] - age) if next_gen else None

    return {
        "age": age,
        "gen": cur_gen,
        "next_gen": next_gen,
        "days_to_next_gen": days_to_next_gen,
        "launch_date": launch_date.strftime("%B %d, %Y") if launch_date else "Unknown",
        "unlocked_count": len(unlocked),
        "total_count": len(milestones),
        "recent_unlocked": [m[1] for m in unlocked[-3:]],
        "next_milestone": next_m,
        "days_to_next": (next_m[0] - age) if next_m else None
    }


@bot.tree.command(name="state", description="Check state timeline, server age, unlocked features, and upcoming milestones.")
@app_commands.describe(state_or_days="Enter your State Number (e.g. 266) or direct server age in days (e.g. 450d)")
async def slash_state(interaction: discord.Interaction, state_or_days: str):
    await interaction.response.defer(thinking=True)
    raw = state_or_days.lower().replace("state", "").replace("s", "").replace("d", "").replace("days", "").strip()
    val = int(raw) if raw.isdigit() else 750
    is_days = "d" in state_or_days.lower() or "day" in state_or_days.lower()

    t = calculate_state_telemetry(val, is_state_number=not is_days)

    gen_str = f"Generation {t['gen']}"
    if t.get('next_gen') and t.get('days_to_next_gen'):
        gen_str += f" *(Gen {t['next_gen']} in ~{t['days_to_next_gen']} days / ~{max(1, t['days_to_next_gen'] // 30)} mo)*"

    embed = discord.Embed(
        title=f"⏱️ Whiteout Survival State Timeline — {'State #' + str(val) if not is_days else 'Server Day ' + str(val)}",
        description=(
            f"**Estimated Server Age:** `Day ~{t['age']}`\n"
            f"**Estimated Launch Date:** `{t['launch_date']}`\n"
            f"**Active Hero Generation:** `{gen_str}`"
        ),
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


def save_utility_data(data: Dict[str, Any]) -> bool:
    json_path = os.path.join(os.path.dirname(__file__), "utility_data.json")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving utility data: {e}")
        return False

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
# 💎 UTILITY DASHBOARDS & INTERACTIVE VIEWS
# ==========================================

def generate_progress_bar(from_lvl: int, to_lvl: int, max_lvl: int = 12, length: int = 14) -> str:
    filled = max(0, min(length, int((to_lvl / max_lvl) * length)))
    empty = length - filled
    return f"`[{'█' * filled}{'░' * empty}]` **{(to_lvl / max_lvl * 100):.0f}%** *(Max: Lv {max_lvl})*"


def build_fc_embed(building_type: str, from_lvl: int, to_lvl: int) -> discord.Embed:
    res = calculate_fc_cost(building_type, from_lvl, to_lvl)
    is_rfc = to_lvl >= 6
    tier_label = "🔮 Refined Fire Crystal Tier (RFC 6-12+)" if is_rfc else "💎 Standard Fire Crystal Tier (FC 1-5)"

    embed = discord.Embed(
        title=f"💎 Fire Crystal Blueprint — {res['building']}",
        description=f"**Target Progression:** FC **{from_lvl}** ➔ FC **{to_lvl}**\n"
                    f"**Phase:** `{tier_label}`\n"
                    f"**Progress:** {generate_progress_bar(from_lvl, to_lvl, max_lvl=12)}",
        color=FROSTY_COLOR if not is_rfc else discord.Color.from_rgb(186, 85, 211)
    )

    embed.add_field(name="💎 Regular Fire Crystals", value=f"**{res['fc']:,} FC**", inline=True)
    if res['rfc'] > 0:
        embed.add_field(name="🔮 Refined Fire Crystals", value=f"**{res['rfc']:,} RFC**", inline=True)
    else:
        embed.add_field(name="🔮 Refined Fire Crystals", value="*None Required (FC 1-5)*", inline=True)

    embed.add_field(name="⏱️ Base Construction Time", value=f"**~{res['days']} Days**", inline=True)
    embed.add_field(
        name="🏆 SvS City Construction Points",
        value=f"⭐ **{res['svs_pts']:,} Points** *(Day 1 / Day 5)*\n"
              f"• Regular FC: `{(res['fc'] * 2000):,} pts` (2,000 / FC)\n"
              f"• Refined RFC: `{(res['rfc'] * 30000):,} pts` (30,000 / RFC)",
        inline=False
    )
    embed.set_footer(text="💡 Tip: Use the interactive buttons below to switch building & tier presets instantly!")
    return embed


class FCCalculatorView(discord.ui.View):
    def __init__(self, building: str = "furnace", from_lvl: int = 0, to_lvl: int = 5, author_id: Optional[int] = None):
        super().__init__(timeout=180)
        self.building = building
        self.from_lvl = from_lvl
        self.to_lvl = to_lvl
        self.author_id = author_id

    @discord.ui.button(label="🏛️ Furnace / Embassy", style=discord.ButtonStyle.primary, row=0)
    async def btn_furnace(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.building = "furnace"
        embed = build_fc_embed(self.building, self.from_lvl, self.to_lvl)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⚔️ Troop Camp", style=discord.ButtonStyle.secondary, row=0)
    async def btn_camp(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.building = "camp"
        embed = build_fc_embed(self.building, self.from_lvl, self.to_lvl)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="FC 1-5", style=discord.ButtonStyle.success, row=1)
    async def btn_fc1_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.from_lvl, self.to_lvl = 0, 5
        embed = build_fc_embed(self.building, self.from_lvl, self.to_lvl)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="FC 5-8", style=discord.ButtonStyle.success, row=1)
    async def btn_fc5_8(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.from_lvl, self.to_lvl = 5, 8
        embed = build_fc_embed(self.building, self.from_lvl, self.to_lvl)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="FC 8-10", style=discord.ButtonStyle.success, row=1)
    async def btn_fc8_10(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.from_lvl, self.to_lvl = 8, 10
        embed = build_fc_embed(self.building, self.from_lvl, self.to_lvl)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="FC 10-12", style=discord.ButtonStyle.success, row=1)
    async def btn_fc10_12(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.from_lvl, self.to_lvl = 10, 12
        embed = build_fc_embed(self.building, self.from_lvl, self.to_lvl)
        await interaction.response.edit_message(embed=embed, view=self)


def build_charms_embed(from_lvl: int, to_lvl: int, is_all_slots: bool = False) -> discord.Embed:
    res = calculate_charms_cost(from_lvl, to_lvl)
    multiplier = 6 if is_all_slots else 1
    slot_label = "👑 Full Chief Set (All 6 Slots)" if is_all_slots else "🛡️ Single Slot Mode (1 Slot)"

    guides = res['guides'] * multiplier
    designs = res['designs'] * multiplier
    boost = res['boost'] * multiplier
    svs_pts = res['svs_pts'] * multiplier

    embed = discord.Embed(
        title="🛡️ Chief Charms Master Calculator",
        description=f"**Target Progression:** Level **{from_lvl}** ➔ Level **{to_lvl}**\n"
                    f"**Scope:** `{slot_label}`\n"
                    f"**Progress:** {generate_progress_bar(from_lvl, to_lvl, max_lvl=12)}",
        color=FROSTY_COLOR if not is_all_slots else WARN_COLOR
    )

    embed.add_field(name="📜 Charm Guides", value=f"**{guides:,} Guides**", inline=True)
    embed.add_field(name="✨ Charm Designs", value=f"**{designs:,} Designs**", inline=True)
    embed.add_field(name="⚡ Combat Stat Surge", value=f"**+{boost:.1f}%** Lethality & HP", inline=True)
    embed.add_field(
        name="🏆 SvS Prep Points Earned",
        value=f"⭐ **{svs_pts:,} Points** *(Day 1, 3, 4)*\n• Charm Score: `{(svs_pts // 70):,} Score` (70 pts / score)",
        inline=False
    )
    embed.set_footer(text="💡 Tip: Click 'Toggle 6-Slot Full Set' to see total costs for all 6 Chief Charms!")
    return embed


class CharmsCalculatorView(discord.ui.View):
    def __init__(self, from_lvl: int = 0, to_lvl: int = 5, is_all_slots: bool = False, author_id: Optional[int] = None):
        super().__init__(timeout=180)
        self.from_lvl = from_lvl
        self.to_lvl = to_lvl
        self.is_all_slots = is_all_slots
        self.author_id = author_id

    @discord.ui.button(label="👑 Toggle 6-Slot Full Set", style=discord.ButtonStyle.primary, row=0)
    async def btn_toggle_scope(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.is_all_slots = not self.is_all_slots
        embed = build_charms_embed(self.from_lvl, self.to_lvl, self.is_all_slots)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Lv 1-5", style=discord.ButtonStyle.success, row=1)
    async def btn_lv1_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.from_lvl, self.to_lvl = 0, 5
        embed = build_charms_embed(self.from_lvl, self.to_lvl, self.is_all_slots)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Lv 5-8", style=discord.ButtonStyle.success, row=1)
    async def btn_lv5_8(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.from_lvl, self.to_lvl = 5, 8
        embed = build_charms_embed(self.from_lvl, self.to_lvl, self.is_all_slots)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Lv 8-10", style=discord.ButtonStyle.success, row=1)
    async def btn_lv8_10(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.from_lvl, self.to_lvl = 8, 10
        embed = build_charms_embed(self.from_lvl, self.to_lvl, self.is_all_slots)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Lv 10-12", style=discord.ButtonStyle.success, row=1)
    async def btn_lv10_12(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.from_lvl, self.to_lvl = 10, 12
        embed = build_charms_embed(self.from_lvl, self.to_lvl, self.is_all_slots)
        await interaction.response.edit_message(embed=embed, view=self)


# ==========================================
# 💎 UTILITY SLASH COMMANDS
# ==========================================

@bot.tree.command(name="fc", description="Interactive Fire Crystal (FC & RFC) upgrade calculator.")
@app_commands.describe(
    building="Type of building to upgrade",
    from_level="Current FC level (0 for Lv 30, or 1 to 11)",
    to_level="Target FC level (1 to 12)"
)
@app_commands.choices(building=[
    app_commands.Choice(name="Furnace / Embassy / Command Center", value="furnace"),
    app_commands.Choice(name="Troop Camp (Infantry / Lancer / Marksman)", value="camp"),
])
async def slash_fc(interaction: discord.Interaction, building: Optional[app_commands.Choice[str]] = None, from_level: Optional[int] = None, to_level: Optional[int] = None):
    b_val = building.value if building else "furnace"
    f_val = from_level if from_level is not None else 0
    t_val = to_level if to_level is not None else 5

    if f_val >= t_val:
        await interaction.response.send_message("❌ Target level must be greater than current level.", ephemeral=True)
        return

    embed = build_fc_embed(b_val, f_val, t_val)
    view = FCCalculatorView(building=b_val, from_lvl=f_val, to_lvl=t_val, author_id=interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="charms", description="Interactive Chief Charms materials and combat boost calculator.")
@app_commands.describe(
    from_level="Current Charm level (0 for unequipped, or 1 to 11)",
    to_level="Target Charm level (1 to 12)",
    all_six_slots="Set to True to calculate materials for all 6 Chief gear slots"
)
async def slash_charms(interaction: discord.Interaction, from_level: Optional[int] = None, to_level: Optional[int] = None, all_six_slots: bool = False):
    f_val = from_level if from_level is not None else 0
    t_val = to_level if to_level is not None else 5

    if f_val >= t_val:
        await interaction.response.send_message("❌ Target level must be greater than current level.", ephemeral=True)
        return

    embed = build_charms_embed(f_val, t_val, is_all_slots=all_six_slots)
    view = CharmsCalculatorView(from_lvl=f_val, to_lvl=t_val, is_all_slots=all_six_slots, author_id=interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view)


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


@bot.tree.command(name="bear", description="Instant Bear Trap rally setup cheat sheet & joiner buff guide.")
async def slash_bear(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🐻 Master Bear Trap Strategy Cheat Sheet",
        description="Maximize your alliance Bear Trap damage score with core Whiteout Survival battle mechanics:",
        color=FROSTY_COLOR
    )
    embed.add_field(
        name="🏹 Optimal Troop Ratio: `10 / 10 / 80`",
        value="• **10% Infantry**\n• **10% Lancers**\n• **80% Marksmen**\n*(Bear deals zero lethal damage to frontlines—Marksmen deal ~2.2x damage!)*",
        inline=False
    )
    embed.add_field(
        name="⭐ Top 4 Rally Joiners: Jessie / Jader / Seo-yoon",
        value="• The **first 4 joiners** MUST send **Jessie (+25% Dmg)**, **Jader (+25% Dmg)**, or **Seo-yoon (+20% Attack)** as their 1st Hero.\n• Stacks up to **+100% total damage boost** for the entire rally!",
        inline=False
    )
    embed.add_field(
        name="⚡ Fast March Rotation",
        value="• Use 25% March Speedups to return quickly.\n• Keep all 4-6 march queues cycling into open alliance rallies without downtime.",
        inline=False
    )
    embed.set_footer(text="Frosty AI • Bear Trap Intelligence")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="bearsim", description="Calculate estimated Bear Trap DPS multiplier and exact troop breakdown.")
@app_commands.describe(
    march_capacity="Total troops in your march (e.g. 150000)",
    troop_tier="Select troop tier (e.g. T10)",
    ratio="Troop composition preset",
    joiner_buff_count="Number of top rally joiners with Jessie (+25% each, 0 to 4)"
)
@app_commands.choices(
    troop_tier=[
        app_commands.Choice(name="T8 Troops", value="T8"),
        app_commands.Choice(name="T9 Troops", value="T9"),
        app_commands.Choice(name="T10 Troops", value="T10"),
        app_commands.Choice(name="T11 Troops", value="T11"),
        app_commands.Choice(name="T12 Troops", value="T12"),
    ],
    ratio=[
        app_commands.Choice(name="10/10/80 (Meta High-DPS Marksman)", value="10/10/80"),
        app_commands.Choice(name="0/20/80 (Pure DPS)", value="0/20/80"),
        app_commands.Choice(name="33/33/33 (Standard Default)", value="33/33/33"),
    ]
)
async def slash_bearsim(interaction: discord.Interaction, march_capacity: int, troop_tier: app_commands.Choice[str], ratio: app_commands.Choice[str], joiner_buff_count: int = 4):
    joiners = max(0, min(4, joiner_buff_count))
    tier_mults = {"T8": 1.0, "T9": 1.35, "T10": 1.85, "T11": 2.45, "T12": 3.20}
    t_mult = tier_mults.get(troop_tier.value, 1.85)

    if ratio.value == "10/10/80":
        inf_pct, lan_pct, mrk_pct, r_mult = 0.10, 0.10, 0.80, 1.95
    elif ratio.value == "0/20/80":
        inf_pct, lan_pct, mrk_pct, r_mult = 0.0, 0.20, 0.80, 1.90
    else:
        inf_pct, lan_pct, mrk_pct, r_mult = 0.334, 0.333, 0.333, 1.00

    inf_count = int(march_capacity * inf_pct)
    lan_count = int(march_capacity * lan_pct)
    mrk_count = march_capacity - inf_count - lan_count

    joiner_bonus_pct = joiners * 25
    joiner_mult = 1.0 + (joiner_bonus_pct / 100.0)

    total_multiplier = t_mult * r_mult * joiner_mult
    surge_pct = ((total_multiplier / (t_mult * 1.0 * 1.0)) - 1.0) * 100.0

    embed = discord.Embed(
        title="🐻 Bear Trap Tactical Damage Simulator",
        description=f"Configuration: **{march_capacity:,} Troops** ({troop_tier.name}) with **{ratio.name}**",
        color=SUCCESS_COLOR
    )
    embed.add_field(name="Overall Damage Multiplier", value=f"💥 **{total_multiplier:.2f}x Damage Boost**", inline=True)
    embed.add_field(name="DPS Surge vs Standard", value=f"🚀 **+{surge_pct:.0f}% Damage**", inline=True)
    embed.add_field(name="Joiner Buff Contribution", value=f"⭐ **{joiners} Jessie Joiners (+{joiner_bonus_pct}%)**", inline=True)
    embed.add_field(
        name="🏹 Exact Troop Breakdown",
        value=f"• 🛡️ **Infantry:** `{inf_count:,}` ({(inf_pct*100):.0f}%)\n"
              f"• 🐎 **Lancers:** `{lan_count:,}` ({(lan_pct*100):.0f}%)\n"
              f"• 🏹 **Marksmen:** `{mrk_count:,}` ({(mrk_pct*100):.0f}%)",
        inline=False
    )
    embed.set_footer(text="💡 Tip: Marksmen deal ~2.2x damage vs Bear Trap!")
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


# ==============================================================================
# 🎁 WHITEOUT SURVIVAL AUTOMATED GIFT CODES & REDEMPTION SYSTEM
# ==============================================================================

class RegisterModal(discord.ui.Modal, title="Whiteout Survival Auto-Claim"):
    player_id_input = discord.ui.TextInput(
        label="Your In-Game Player ID",
        placeholder="e.g. 123456789 (find under Avatar top-left)",
        min_length=4,
        max_length=15,
        required=True
    )
    state_input = discord.ui.TextInput(
        label="Your State / Kingdom Number",
        placeholder="e.g. 542 (numbers only)",
        min_length=1,
        max_length=5,
        required=True
    )
    label_input = discord.ui.TextInput(
        label="Account Label / Nickname (Optional)",
        placeholder="e.g. Main, Farm 1, Farm 2 (default: Main / Farm #)",
        min_length=1,
        max_length=15,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        pid = self.player_id_input.value.strip()
        state_str = self.state_input.value.strip()
        label_val = self.label_input.value.strip() if self.label_input.value else None

        if not pid.isdigit():
            await interaction.response.send_message("❌ **Invalid Player ID:** Player ID must consist only of digits.", ephemeral=True)
            return
        if not state_str.isdigit():
            await interaction.response.send_message("❌ **Invalid State Number:** State must be a valid number (e.g. 542).", ephemeral=True)
            return

        state_num = int(state_str)
        if state_num <= 0:
            await interaction.response.send_message("❌ **Invalid State Number:** State must be a positive number.", ephemeral=True)
            return

        current_accounts = registered_players.get_player_accounts(interaction.user.id)
        existing_pids = [a["player_id"] for a in current_accounts]
        if len(current_accounts) >= registered_players.MAX_ACCOUNTS_PER_USER and pid not in existing_pids:
            await interaction.response.send_message(
                f"⚠️ You already have **{registered_players.MAX_ACCOUNTS_PER_USER} accounts** registered (the maximum limit).\n"
                f"Use `/codes action:Unregister from Auto-Claim` with a Player ID to free up a slot.",
                ephemeral=True
            )
        owner_uid = registered_players.get_player_owner(pid)
        if owner_uid and owner_uid != str(interaction.user.id):
            await interaction.response.send_message(
                "⚠️ This Player ID is already registered by another Discord user. If this is your account, ask them to unregister it.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Quick verification against Century Games API using a known promo code
        test_code = "gogoWOS"
        check_res = await redeem_gift_code(pid, state_num, test_code)

        if check_res.get("err_code") == 40020:
            await interaction.followup.send(
                f"❌ **Character Verification Failed:**\n"
                f"Player ID `{pid}` was not found in State `{state_num}` on Century Games servers.\n\n"
                f"• Please open Whiteout Survival and tap your **Avatar** (top-left) to confirm your exact Player ID and State number!",
                ephemeral=True
            )
            return

        success, msg, acc = registered_players.register_player(
            interaction.user.id, pid, state_num, label=label_val, notify_dm=True
        )

        if not success:
            await interaction.followup.send(msg, ephemeral=True)
            return

        total_accs = len(registered_players.get_player_accounts(interaction.user.id))
        embed = discord.Embed(
            title="✅ Registered for Frosty Auto-Claim!",
            description=(
                f"Welcome aboard, Chief! Your character is now registered for automated gift code redemption.\n\n"
                f"🏷️ **Account Label:** **{acc.get('label', 'Main')}**\n"
                f"👤 **Player ID:** `{pid}`\n"
                f"🏰 **State:** `{state_num}`\n"
                f"📊 **Account Slots:** `{total_accs}/{registered_players.MAX_ACCOUNTS_PER_USER} Used`\n"
                f"⚡ **Auto-Claim Status:** `🟢 Active (ON)`\n"
                f"📬 **Direct Message Alerts:** `🔔 Enabled`\n\n"
                f"🎁 **What happens next?**\n"
                f"Whenever a new Whiteout Survival gift code is released, Frosty Bot will automatically redeem it directly to your in-game mailbox!\n\n"
                f"💡 *You can register up to {registered_players.MAX_ACCOUNTS_PER_USER} accounts (e.g. Main + Farm accounts) under this Discord account.*"
            ),
            color=SUCCESS_COLOR
        )
        embed.set_footer(text="Use /codes action:My Registration Status to check or update your settings anytime.")
        await interaction.followup.send(embed=embed, ephemeral=True)


BANNER_FILE_PATH = os.path.join(os.path.dirname(__file__), "assets", "wos_giftcode_banner.jpg")


def build_codes_dashboard_embed(user: Optional[discord.User | discord.Member] = None) -> Tuple[discord.Embed, Optional[discord.File]]:
    """Builds the public-safe Whiteout Survival Gift Code Command Center embed."""
    data = load_utility_data()
    gift_codes = data.get("gift_codes", list(ACTIVE_GIFT_CODES))

    embed = discord.Embed(
        title="❄️ Whiteout Survival • Gift Code Command Center",
        description=(
            "Never miss out on official Century Games promo rewards! Claim free **Gems, Chief Stamina, "
            "Speedups, Gold Keys & Hero Shards** with instant 1-click batch claiming or automatic 24/7 background redemption.\n"
        ),
        color=0x00D8F6
    )

    # 1. System Overview & Usefulness
    embed.add_field(
        name="⭐ What This Service Does For You",
        value=(
            "• 🤖 **24/7 Auto-Claim:** Link your character once and Frosty will automatically claim all newly released codes to your in-game mailbox — even while you're offline!\n"
            "• ⚡ **1-Tap Batch Redemption:** Click **`[ ⚡ Claim All Now ]`** to redeem all active codes across all your linked characters in seconds.\n"
            "• 🎮 **Multi-Account Support:** Connect up to **5 characters** (Main + Farm accounts) per Discord user.\n"
            "• 🔒 **100% Private & Secure:** Character names and Player IDs are strictly confidential and never displayed in public chat."
        ),
        inline=False
    )

    # 2. Active Promo Codes (Card layout)
    code_lines = []
    for c in gift_codes[:6]:
        code_str = c.get("code", "")
        status = c.get("status", "🟢 Active & Verified")
        rewards = c.get("rewards", "Free In-Game Rewards")
        code_lines.append(f"💎 **`{code_str}`** — {status}\n↳ *Rewards: {rewards}*")

    if not code_lines:
        code_lines.append("ℹ️ *No active codes at this exact moment. Check back soon!*")

    embed.add_field(
        name="🎁 Active & Verified Gift Codes",
        value="\n\n".join(code_lines),
        inline=False
    )

    # 3. Interactive Buttons Guide
    embed.add_field(
        name="📱 Interactive Features & Controls",
        value=(
            "• **`[ ⚡ Claim All Now ]`** — Batch-redeems all active codes for your characters *(results sent privately)*.\n"
            "• **`[ ➕ Register Account ]`** — Securely link a new character using your Player ID and State *(private modal)*.\n"
            "• **`[ 📋 My Accounts ]`** — Privately view your linked characters, claim history, and toggle DM alerts.\n"
            "• **`[ 🌐 Century Games Portal ]`** — Open the official Century Games web redemption page."
        ),
        inline=False
    )

    file = None
    if os.path.exists(BANNER_FILE_PATH):
        file = discord.File(BANNER_FILE_PATH, filename="wos_giftcode_banner.jpg")
        embed.set_image(url="attachment://wos_giftcode_banner.jpg")

    embed.set_footer(text="Frosty AI • Automated Gift Code Network • Private & Secure")
    return embed, file


class AdminGiftCodeModal(discord.ui.Modal, title="Gift Code Admin Manager"):
    action_input = discord.ui.TextInput(
        label="Action (add or remove)",
        placeholder="add or remove",
        min_length=3,
        max_length=6,
        required=True,
        default="add"
    )
    code_input = discord.ui.TextInput(
        label="Promo Code",
        placeholder="e.g. NEWYEAR2026",
        min_length=3,
        max_length=30,
        required=True
    )
    rewards_input = discord.ui.TextInput(
        label="Rewards Description (if adding)",
        placeholder="e.g. 500 Gems, 5x Speedups",
        required=False,
        default="Free In-Game Rewards (Gems, Speedups, Gold Keys)"
    )

    async def on_submit(self, interaction: discord.Interaction):
        if not is_authorized_admin(interaction.user):
            await interaction.response.send_message("⛔ **Access Denied:** Admin only.", ephemeral=True)
            return

        act = self.action_input.value.strip().lower()
        clean_code = self.code_input.value.strip()
        clean_rewards = self.rewards_input.value.strip() or "Free In-Game Rewards (Gems, Speedups, Gold Keys)"
        data = load_utility_data()
        gift_codes = data.get("gift_codes", list(ACTIVE_GIFT_CODES))

        if act == "add":
            existing = [c for c in gift_codes if c["code"].lower() == clean_code.lower()]
            if existing:
                existing[0]["code"] = clean_code
                existing[0]["rewards"] = clean_rewards
                existing[0]["status"] = "🟢 Active & Verified"
            else:
                gift_codes.insert(0, {
                    "code": clean_code,
                    "status": "🟢 Active & Verified",
                    "rewards": clean_rewards
                })
            data["gift_codes"] = gift_codes
            save_utility_data(data)
            asyncio.create_task(dispatch_auto_claim(clean_code))
            await interaction.response.send_message(
                f"✅ **Gift Code Added & Auto-Claim Triggered:** `{clean_code}` with rewards: *{clean_rewards}*.",
                ephemeral=True
            )
        elif act == "remove":
            data["gift_codes"] = [c for c in gift_codes if c["code"].lower() != clean_code.lower()]
            save_utility_data(data)
            await interaction.response.send_message(f"🗑️ **Code Removed:** `{clean_code}` from active database.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Action must be `add` or `remove`.", ephemeral=True)


class AccountSelect(discord.ui.Select):
    def __init__(self, user_id: int):
        self.user_id = user_id
        accounts = registered_players.get_player_accounts(user_id)
        options = []
        for i, acc in enumerate(accounts, 1):
            lbl = acc.get("label", f"Account #{i}")
            pid = acc.get("player_id", "")
            st = acc.get("state", "")
            options.append(discord.SelectOption(
                label=f"{lbl} (State {st})",
                value=pid,
                description=f"Player ID: {pid}",
                emoji="🏷️"
            ))
        if len(accounts) > 1:
            options.append(discord.SelectOption(
                label="Unregister ALL Accounts",
                value="__ALL__",
                description="Remove all registered accounts from Frosty",
                emoji="🗑️"
            ))
        if not options:
            options.append(discord.SelectOption(
                label="No Accounts Registered",
                value="__NONE__",
                description="Click 'Register Account' to link your character",
                emoji="ℹ️"
            ))
        super().__init__(
            placeholder="Select an account to view or delete...",
            min_values=1,
            max_values=1,
            options=options,
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        selected_pid = self.values[0]
        if selected_pid == "__NONE__":
            await interaction.response.send_message("ℹ️ You have no accounts registered yet.", ephemeral=True)
            return

        if selected_pid == "__ALL__":
            ok, msg = registered_players.unregister_player(interaction.user.id)
            await interaction.response.send_message(f"{msg}", ephemeral=True)
            return

        accounts = registered_players.get_player_accounts(interaction.user.id)
        target = next((a for a in accounts if a["player_id"] == selected_pid), None)
        if not target:
            await interaction.response.send_message("⚠️ Account not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"🏷️ Account Details: {target.get('label', 'Main')}",
            description=(
                f"👤 **Player ID:** `{target['player_id']}`\n"
                f"🏰 **State Number:** `{target['state']}`\n"
                f"🎁 **Total Claimed Codes:** `{len(target.get('claimed_codes', []))}`\n"
                f"⏱️ **Last Activity:** `{target.get('last_status', 'Registered')}`\n\n"
                f"Click below to delete this account from your auto-claim list:"
            ),
            color=SUCCESS_COLOR
        )

        view = discord.ui.View(timeout=120)
        delete_btn = discord.ui.Button(
            label=f"Delete '{target.get('label', 'Account')}'",
            style=discord.ButtonStyle.danger,
            emoji="🗑️"
        )

        async def delete_cb(btn_interaction: discord.Interaction):
            ok, msg = registered_players.unregister_player(btn_interaction.user.id, selected_pid)
            await btn_interaction.response.send_message(msg, ephemeral=True)

        delete_btn.callback = delete_cb
        view.add_item(delete_btn)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class AccountManagementView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.add_item(AccountSelect(user_id))

    @discord.ui.button(label="Register Another Account", style=discord.ButtonStyle.primary, emoji="➕", row=1)
    async def add_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        accounts = registered_players.get_player_accounts(interaction.user.id)
        if len(accounts) >= registered_players.MAX_ACCOUNTS_PER_USER:
            await interaction.response.send_message(
                f"⚠️ Maximum limit of **{registered_players.MAX_ACCOUNTS_PER_USER} accounts** reached! Please remove an account from the dropdown first.",
                ephemeral=True
            )
            return
        await interaction.response.send_modal(RegisterModal())

    @discord.ui.button(label="Toggle DM Alerts", style=discord.ButtonStyle.secondary, emoji="🔔", row=1)
    async def toggle_dm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_status = registered_players.toggle_dm_notification(interaction.user.id)
        status_text = "🟢 Enabled (You will receive private DMs when rewards are claimed)" if new_status else "🔴 Disabled"
        await interaction.response.send_message(f"📬 **Direct Message Alerts:** {status_text}", ephemeral=True)


class CodesActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Link buttons (Row 1)
        self.add_item(discord.ui.Button(
            label="Century Games Portal",
            url="https://wos-giftcode.centurygame.com/",
            style=discord.ButtonStyle.link,
            emoji="🌐",
            row=1
        ))
        self.add_item(discord.ui.Button(
            label="Official Discord",
            url="https://discord.gg/whiteoutsurvival",
            style=discord.ButtonStyle.link,
            emoji="📢",
            row=1
        ))

    @discord.ui.button(
        label="Claim All Now",
        style=discord.ButtonStyle.success,
        emoji="⚡",
        custom_id="frosty_codes_claim_all_btn",
        row=0
    )
    async def claim_all_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        accounts = registered_players.get_player_accounts(interaction.user.id)
        if not accounts:
            embed = discord.Embed(
                title="📋 No Accounts Registered Yet",
                description=(
                    "You haven't linked any Whiteout Survival characters yet!\n\n"
                    "Click **`[ ➕ Register Account ]`** below to add your **Player ID** and **State**, "
                    "then you can claim every code in 1 click!"
                ),
                color=WARN_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        data = load_utility_data()
        gift_codes = data.get("gift_codes", list(ACTIVE_GIFT_CODES))
        active_codes = [c["code"].strip() for c in gift_codes if c.get("code")][:5]

        if not active_codes:
            await interaction.followup.send("ℹ️ No active gift codes found in the database right now.", ephemeral=True)
            return

        lines = [f"Processed **{len(accounts)}** character(s) across **{len(active_codes)}** active code(s):\n"]

        for acc in accounts:
            pid = acc["player_id"]
            st = acc["state"]
            lbl = acc.get("label", "Main")
            lines.append(f"**🏷️ {lbl}** (`{pid}`, State `{st}`):")
            for cdk in active_codes:
                claimed_list = [c.upper() for c in acc.get("claimed_codes", [])]
                if cdk.upper() in claimed_list:
                    lines.append(f"• ℹ️ `{cdk}`: Already redeemed")
                    continue

                res = await redeem_gift_code(pid, st, cdk)
                registered_players.record_claim_for_account(interaction.user.id, pid, cdk, res["success"], res["message"])
                icon = "✅" if res["success"] else "ℹ️"
                lines.append(f"• {icon} `{cdk}`: {res['message']}")
                await asyncio.sleep(1.0)
            lines.append("")

        result_embed = discord.Embed(
            title="🎁 Gift Code Claim Results",
            description="\n".join(lines),
            color=SUCCESS_COLOR
        )
        result_embed.set_footer(text="Rewards have been sent to your in-game mailbox in Whiteout Survival!")
        await interaction.followup.send(embed=result_embed, ephemeral=True)

    @discord.ui.button(
        label="Register Account",
        style=discord.ButtonStyle.primary,
        emoji="➕",
        custom_id="frosty_codes_register_btn",
        row=0
    )
    async def register_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        accounts = registered_players.get_player_accounts(interaction.user.id)
        if len(accounts) >= registered_players.MAX_ACCOUNTS_PER_USER:
            await interaction.response.send_message(
                f"⚠️ You already have **{registered_players.MAX_ACCOUNTS_PER_USER} accounts** registered (the maximum limit).\n"
                f"Click **`[ 📋 My Accounts ]`** to remove an account first.",
                ephemeral=True
            )
            return
        await interaction.response.send_modal(RegisterModal())

    @discord.ui.button(
        label="My Accounts",
        style=discord.ButtonStyle.secondary,
        emoji="📋",
        custom_id="frosty_codes_status_btn",
        row=0
    )
    async def manage_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        accounts = registered_players.get_player_accounts(interaction.user.id)
        if not accounts:
            embed = discord.Embed(
                title="📋 No Accounts Registered Yet",
                description=(
                    "You haven't registered any Whiteout Survival characters yet.\n\n"
                    "Click **`[ ➕ Register Account ]`** to link your character (up to 5 accounts supported)!"
                ),
                color=FROSTY_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        slot_count = len(accounts)
        max_slots = registered_players.MAX_ACCOUNTS_PER_USER
        filled_bar = "▰" * slot_count + "▱" * (max_slots - slot_count)

        embed = discord.Embed(
            title="📊 Whiteout Survival Account Manager",
            description=(
                f"`[ {filled_bar} ]` **{slot_count}/{max_slots} Account Slots Used**\n"
                f"⚡ **Auto-Claim Status:** `🟢 Active (Auto-Redeems New Codes)`\n\n"
                f"Use the dropdown menu below to inspect or remove an account:"
            ),
            color=SUCCESS_COLOR
        )

        for i, acc in enumerate(accounts, 1):
            lbl = acc.get("label", f"Account #{i}")
            pid = acc.get("player_id", "Unknown")
            st = acc.get("state", "Unknown")
            claimed_cnt = len(acc.get("claimed_codes", []))
            last_status = acc.get("last_status", "Registered")

            embed.add_field(
                name=f"🏷️ #{i} {lbl} (State {st})",
                value=(
                    f"• **Player ID:** `{pid}`\n"
                    f"• **Codes Claimed:** `{claimed_cnt}`\n"
                    f"• **Status:** `{last_status}`"
                ),
                inline=False
            )

        view = AccountManagementView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(
        label="Admin",
        style=discord.ButtonStyle.secondary,
        emoji="⚙️",
        custom_id="frosty_codes_admin_btn",
        row=1
    )
    async def admin_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_authorized_admin(interaction.user):
            await interaction.response.send_message(
                f"⛔ **Access Denied:** Only Supreme Commander (`{', '.join(AUTHORIZED_ADMIN_USERNAMES)}`) can manage gift codes.",
                ephemeral=True
            )
            return
        await interaction.response.send_modal(AdminGiftCodeModal())


async def dispatch_auto_claim(code: str):
    """
    Background worker queue: Iterates through all registered player accounts with auto-claim enabled
    and redeems the new gift code sequentially with rate-limit pacing.
    """
    clean_code = code.strip()
    active_accounts = registered_players.get_all_active_accounts()
    if not active_accounts:
        logger.info(f"Auto-claim dispatched for code '{clean_code}', but no registered accounts found.")
        return

    logger.info(f"🚀 [Auto-Claim] Starting redemption queue for code '{clean_code}' across {len(active_accounts)} registered accounts...")
    claimed_count = 0
    skipped_count = 0
    failed_count = 0

    for acc in active_accounts:
        uid_str = acc.get("discord_uid")
        pid = acc.get("player_id")
        state = acc.get("state")
        label = acc.get("label", "Main")
        notify_dm = acc.get("notify_dm", True)

        if not pid or not state or not uid_str:
            continue

        claimed_list = [c.upper() for c in acc.get("claimed_codes", [])]
        if clean_code.upper() in claimed_list:
            skipped_count += 1
            continue

        try:
            res = await redeem_gift_code(pid, state, clean_code)
            is_success = res["success"]
            registered_players.record_claim_for_account(int(uid_str), pid, clean_code, is_success, res["message"])

            if is_success:
                claimed_count += 1
                if notify_dm:
                    try:
                        user = bot.get_user(int(uid_str)) or await bot.fetch_user(int(uid_str))
                        if user:
                            dm_embed = discord.Embed(
                                title="🎁 Frosty Auto-Claim: Gift Code Redeemed!",
                                description=(
                                    f"A new Whiteout Survival gift code was automatically claimed for your character!\n\n"
                                    f"🏷️ **Account:** **{label}**\n"
                                    f"🔑 **Gift Code:** `{clean_code}`\n"
                                    f"👤 **Player ID:** `{pid}`\n"
                                    f"🏰 **State:** `{state}`\n\n"
                                    f"📫 Check your in-game mailbox in Whiteout Survival to collect your rewards!"
                                ),
                                color=SUCCESS_COLOR
                            )
                            dm_embed.set_footer(text="Frosty Bot • Automated Gift Code Center")
                            await user.send(embed=dm_embed)
                    except Exception as dm_err:
                        logger.debug(f"Could not send DM to {uid_str}: {dm_err}")
            else:
                failed_count += 1
                logger.info(f"[Auto-Claim] Player {pid} [{label}] (State {state}) code '{clean_code}' returned: {res['message']}")

        except Exception as claim_err:
            failed_count += 1
            logger.error(f"[Auto-Claim] Error for account {pid} (user {uid_str}): {claim_err}")

        # Human-like delay & Century Games API rate-limit protection
        await asyncio.sleep(1.5)

    logger.info(f"✨ [Auto-Claim] Finished queue for '{clean_code}': {claimed_count} claimed, {skipped_count} skipped, {failed_count} failed.")


@tasks.loop(hours=4)
async def auto_sync_gift_codes():
    """Periodically scans online sources for new promo codes and auto-claims for registered players."""
    try:
        data = load_utility_data()
        gift_codes = data.get("gift_codes", list(ACTIVE_GIFT_CODES))
        existing_codes = {c["code"].upper() for c in gift_codes}

        new_online = await asyncio.to_thread(scrape_online_gift_codes)
        found_new = []
        for oc in new_online:
            clean_c = oc["code"].strip().upper()
            if clean_c not in existing_codes and len(clean_c) >= 5:
                gift_codes.insert(0, oc)
                existing_codes.add(clean_c)
                found_new.append(oc["code"].strip())

        if found_new:
            data["gift_codes"] = gift_codes
            save_utility_data(data)
            logger.info(f"🎁 Discovered {len(found_new)} new gift codes: {', '.join(found_new)}")
            for new_code in found_new:
                asyncio.create_task(dispatch_auto_claim(new_code))
    except Exception as e:
        logger.debug(f"Periodic gift codes check notice: {e}")


@bot.tree.command(name="codes", description="Whiteout Survival Gift Code Center & Auto-Claim Dashboard")
@app_commands.describe(code="Optional: Enter a specific promo code to redeem immediately across your accounts")
async def slash_codes(
    interaction: discord.Interaction,
    code: Optional[str] = None
):
    if code:
        clean_code = code.strip()
        accounts = registered_players.get_player_accounts(interaction.user.id)
        if not accounts:
            await interaction.response.send_message(
                f"⚠️ You don't have any characters registered yet!\n"
                f"Please run `/codes` and click **`[ ➕ Register Account ]`** first to redeem `{clean_code}`.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        results = []
        for acc in accounts:
            pid = acc["player_id"]
            st = acc["state"]
            lbl = acc.get("label", "Main")
            res = await redeem_gift_code(pid, st, clean_code)
            registered_players.record_claim_for_account(interaction.user.id, pid, clean_code, res["success"], res["message"])
            icon = "✅" if res["success"] else "ℹ️"
            results.append(f"{icon} **{lbl}** (`{pid}`, State `{st}`): {res['message']}")
            if len(accounts) > 1:
                await asyncio.sleep(1.0)

        embed = discord.Embed(
            title=f"🎁 Gift Code Redemption: `{clean_code}`",
            description=f"Processed **{len(accounts)}** registered account(s):\n\n" + "\n".join(results),
            color=SUCCESS_COLOR
        )
        embed.set_footer(text="Whiteout Survival Official Redeem Service")
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    # Default Interactive Dashboard
    embed, file = build_codes_dashboard_embed()
    view = CodesActionView()
    if file:
        await interaction.response.send_message(embed=embed, file=file, view=view)
    else:
        await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="giftcode_admin", description="[Admin Only] Add or remove Whiteout Survival promo codes.")
@app_commands.describe(
    action="Add new code or remove expired code",
    code="The promo code (e.g. gogoWOS)",
    rewards="Description of rewards (when adding)"
)
@app_commands.choices(action=[
    app_commands.Choice(name="Add Code & Trigger Auto-Claim", value="add"),
    app_commands.Choice(name="Remove Expired Code", value="remove"),
])
async def slash_giftcode_admin(
    interaction: discord.Interaction,
    action: app_commands.Choice[str],
    code: str,
    rewards: Optional[str] = None
):
    if not is_authorized_admin(interaction.user):
        await interaction.response.send_message(
            f"⛔ **Access Denied:** Only Supreme Commander (`{', '.join(AUTHORIZED_ADMIN_USERNAMES)}`) can manage gift codes.",
            ephemeral=True
        )
        return

    clean_code = code.strip()
    data = load_utility_data()
    gift_codes = data.get("gift_codes", list(ACTIVE_GIFT_CODES))

    if action.value == "add":
        clean_rewards = rewards.strip() if rewards else "Free In-Game Rewards (Gems, Speedups, Gold Keys)"
        existing = [c for c in gift_codes if c["code"].lower() == clean_code.lower()]
        if existing:
            existing[0]["code"] = clean_code
            existing[0]["rewards"] = clean_rewards
            existing[0]["status"] = "🟢 Active & Verified"
        else:
            gift_codes.insert(0, {
                "code": clean_code,
                "status": "🟢 Active & Verified",
                "rewards": clean_rewards
            })
        data["gift_codes"] = gift_codes
        save_utility_data(data)
        asyncio.create_task(dispatch_auto_claim(clean_code))
        await interaction.response.send_message(
            f"✅ **Gift Code Added & Auto-Claim Triggered!**\n"
            f"• Code `{clean_code}` is live with rewards: *{clean_rewards}*.\n"
            f"• Background auto-claim dispatched across all registered players!",
            ephemeral=True
        )
    elif action.value == "remove":
        new_codes = [c for c in gift_codes if c["code"].lower() != clean_code.lower()]
        if len(new_codes) == len(gift_codes):
            await interaction.response.send_message(f"⚠️ Code `{clean_code}` not found in database.", ephemeral=True)
            return
        data["gift_codes"] = new_codes
        save_utility_data(data)
        await interaction.response.send_message(f"🗑️ Code `{clean_code}` removed.", ephemeral=True)


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


@bot.tree.command(name="reindex", description="[Admin Only] Rebuild and refresh ChromaDB archives and game data.")
@app_commands.describe(local_only="Set to True for instant local indexing, or False for web crawl")
async def slash_reindex(interaction: discord.Interaction, local_only: bool = True):
    if not is_authorized_admin(interaction.user):
        await interaction.response.send_message(
            f"⛔ **Access Denied:** Only authorized Commander(s) (`{', '.join(AUTHORIZED_ADMIN_USERNAMES)}`) can trigger database reindexing.",
            ephemeral=True
        )
        return

    await interaction.response.defer(thinking=True)
    loop = asyncio.get_running_loop()
    try:
        new_count = await loop.run_in_executor(None, run_full_reindex, local_only)
        knowledge_base.reload_dynamic_entities()
        
        embed = discord.Embed(
            title="✨ Knowledge Re-indexing Complete!",
            description=f"Commander **{interaction.user.display_name}** (`@{interaction.user.name}`), tactical archives have been refreshed!",
            color=SUCCESS_COLOR
        )
        embed.add_field(name="📚 Total Chunks", value=f"`{new_count}` knowledge chunks", inline=True)
        embed.add_field(name="👑 Hero Generations", value=f"Gen 0 ➔ Gen `{knowledge_base.max_generation}+`", inline=True)
        embed.add_field(name="🛡️ Active Heroes", value=f"`{len(knowledge_base.known_heroes)}` heroes indexed", inline=True)
        embed.set_footer(text="Frosty AI • Tactical Intelligence Synchronization")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ **Reindexing Error:** `{str(e)}`")


def normalize_channel_name(name: str) -> str:
    """Normalizes stylized Unicode fonts (math sans-serif, bold, cursive, etc.) and symbols to clean ASCII."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_str = nfkd.encode("ascii", "ignore").decode("utf-8").lower()
    return re.sub(r'[\s_]+', '-', ascii_str).strip('-')


def find_best_announcement_channel(guild: discord.Guild) -> Optional[discord.TextChannel]:
    """
    Intelligently select the most visible, appropriate public text channel in a guild for official broadcasts.
    Filters out private channels, moderation logs, rules, verification, website links, tickets, and static guides.
    Handles fancy Unicode fonts (e.g. 𝖦eneral-𝖢hat, 𝖠nnouncements).
    """
    ignored_keywords = [
        "rule", "rules", "verify", "verification", "welcome", "goodbye", "leave",
        "log", "logs", "audit", "mod", "admin", "staff", "ticket", "tickets",
        "mute", "ban", "voice", "archive", "afk", "role", "roles", "reaction",
        "join", "member-log", "server-log", "bot-log", "testing", "sandbox",
        "website", "site", "link", "links", "guide", "access", "faq", "info",
        "information", "about", "statetube", "tube", "media", "video", "videos",
        "stream", "streams", "patch", "patch-note", "patch-notes", "changelog", "readme",
        "task-list", "appointment", "agreement", "agreements", "introduction", "intro",
        "poll", "polls", "stat", "stats", "report", "reports", "fortress", "fortresses"
    ]

    def is_channel_ignored(ch_name: str) -> bool:
        clean = normalize_channel_name(ch_name)
        return any(k in clean for k in ignored_keywords)

    def can_bot_and_everyone_use(ch: discord.TextChannel) -> bool:
        bot_perms = ch.permissions_for(guild.me)
        if not bot_perms.send_messages or not bot_perms.embed_links:
            return False
        everyone_perms = ch.permissions_for(guild.default_role)
        if not everyone_perms.view_channel:
            return False
        return True

    # Gather candidate channels where bot can write & everyone can view
    valid_channels = [ch for ch in guild.text_channels if can_bot_and_everyone_use(ch)]
    if not valid_channels:
        # Fallback: channels where bot has write perms even if everyone perms are custom
        valid_channels = [
            ch for ch in guild.text_channels 
            if ch.permissions_for(guild.me).send_messages and ch.permissions_for(guild.me).embed_links
        ]
        if not valid_channels:
            return None

    # Priority groups for community announcements
    priority_groups = [
        ["frosty-announcements", "frosty-announcement", "frosty-bot", "frosty-news", "frosty-chat", "frosty"],
        ["announcements", "announcement", "announcement-chat", "updates", "update", "news", "server-announcements", "alliance-announcements", "broadcast"],
        ["general", "general-chat", "main-chat", "chat", "lounge", "discussion", "talk"],
        ["wos-chat", "wos", "whiteout-survival", "whiteout", "alliance-chat", "game-chat", "strategy"],
        ["bot-commands", "bot-command", "bot-chat", "bot-spam", "commands", "bots", "bot"]
    ]

    for group in priority_groups:
        for keyword in group:
            for ch in valid_channels:
                if is_channel_ignored(ch.name):
                    continue
                clean_name = normalize_channel_name(ch.name)
                if keyword in clean_name:
                    return ch

    # Fallback to system channel if public and not ignored
    if guild.system_channel and guild.system_channel in valid_channels and not is_channel_ignored(guild.system_channel.name):
        return guild.system_channel

    # Fallback to channels where @everyone can talk (active discussion channels)
    active_chats = [
        ch for ch in valid_channels
        if not is_channel_ignored(ch.name) and ch.permissions_for(guild.default_role).send_messages
    ]
    if active_chats:
        return active_chats[0]

    # Fallback to first non-ignored valid channel
    for ch in valid_channels:
        if not is_channel_ignored(ch.name):
            return ch

    return valid_channels[0]


async def broadcast_announcement_to_guilds(
    sender: discord.User | discord.Member, 
    message_text: str
) -> Tuple[int, int, List[Dict[str, Any]]]:
    """
    Broadcast an official announcement from the bot owner across all active guilds.
    Returns (success_count, fail_count, delivery_reports).
    """
    success_count = 0
    fail_count = 0
    delivery_reports: List[Dict[str, Any]] = []

    embed = discord.Embed(
        title="📢 Frosty Official Announcement",
        description=message_text,
        color=FROSTY_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    if sender.display_avatar:
        embed.set_author(name=f"Announcement from {sender.display_name} (@{sender.name})", icon_url=sender.display_avatar.url)
    else:
        embed.set_author(name=f"Announcement from {sender.display_name} (@{sender.name})")
    embed.set_footer(text="Frosty AI • Tactical Command Network")

    for guild in bot.guilds:
        target_channel = find_best_announcement_channel(guild)

        if target_channel:
            try:
                await target_channel.send(embed=embed)
                success_count += 1
                delivery_reports.append({
                    "guild": guild.name,
                    "channel": f"#{target_channel.name}",
                    "channel_id": target_channel.id,
                    "status": "success"
                })
                logger.info(f"📢 [Broadcast] Delivered to '{guild.name}' ➔ #{target_channel.name} (ID: {target_channel.id})")
                await asyncio.sleep(0.35)  # Anti-rate-limit spacing
            except Exception as e:
                logger.warning(f"⚠️ [Broadcast] Could not send to guild '{guild.name}' in #{target_channel.name}: {e}")
                fail_count += 1
                delivery_reports.append({
                    "guild": guild.name,
                    "channel": f"#{target_channel.name}",
                    "channel_id": target_channel.id,
                    "status": f"error: {e}"
                })
        else:
            logger.warning(f"⚠️ [Broadcast] No suitable writable channel found for guild '{guild.name}'")
            fail_count += 1
            delivery_reports.append({
                "guild": guild.name,
                "channel": "None (No Perms)",
                "channel_id": None,
                "status": "missing_perms"
            })

    return success_count, fail_count, delivery_reports


@bot.tree.command(name="sendmessage", description="[Owner Only] Broadcast an official announcement to all servers.")
@app_commands.describe(message="The announcement message to broadcast across all Discord servers")
async def slash_sendmessage(interaction: discord.Interaction, message: str):
    if not is_authorized_admin(interaction.user):
        await interaction.response.send_message(
            f"⛔ **Access Denied:** Only the Supreme Commander (`{', '.join(AUTHORIZED_ADMIN_USERNAMES)}`) can broadcast announcements across servers.",
            ephemeral=True
        )
        return

    await interaction.response.defer(thinking=True, ephemeral=True)
    success, fail, reports = await broadcast_announcement_to_guilds(interaction.user, message)

    lines = []
    for r in reports[:30]:
        status_icon = "✅" if r["status"] == "success" else "⚠️"
        lines.append(f"{status_icon} **{r['guild'][:22]}** ➔ `{r['channel']}`")

    breakdown_text = "\n".join(lines)
    if len(reports) > 30:
        breakdown_text += f"\n*...and {len(reports) - 30} more servers.*"

    res_embed = discord.Embed(
        title="📢 Broadcast Transmission Complete",
        description=f"Your message was broadcast across active Discord servers!\n\n"
                    f"• ✅ **Delivered to:** `{success}` servers\n"
                    f"• ⚠️ **Skipped (No Perms/Hidden):** `{fail}` servers\n"
                    f"• 🌐 **Total Connected Servers:** `{len(bot.guilds)}`\n\n"
                    f"**📋 Delivery Destinations:**\n{breakdown_text}",
        color=SUCCESS_COLOR
    )
    await interaction.followup.send(embed=res_embed, ephemeral=True)




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
    from_lvl = 0
    to_lvl = 5

    if parts:
        if "camp" in parts[0].lower():
            b_type = "camp"
        if len(parts) >= 2 and parts[1].isdigit():
            from_lvl = int(parts[1])
        if len(parts) >= 3 and parts[2].isdigit():
            to_lvl = int(parts[2])
        elif len(parts) == 2 and parts[1].isdigit():
            to_lvl = int(parts[1])
            from_lvl = 0

    embed = build_fc_embed(b_type, from_lvl, to_lvl)
    view = FCCalculatorView(building=b_type, from_lvl=from_lvl, to_lvl=to_lvl, author_id=ctx.author.id)
    await ctx.send(embed=embed, view=view)


@bot.command(name="charms")
async def prefix_charms(ctx, *, args: str = "0 5"):
    parts = [int(p) for p in args.strip().split() if p.isdigit()]
    is_all = "all" in args.lower() or "6" in args.lower() and len(parts) < 2
    from_lvl = parts[0] if len(parts) >= 1 else 0
    to_lvl = parts[1] if len(parts) >= 2 else 5

    embed = build_charms_embed(from_lvl, to_lvl, is_all_slots=is_all)
    view = CharmsCalculatorView(from_lvl=from_lvl, to_lvl=to_lvl, is_all_slots=is_all, author_id=ctx.author.id)
    await ctx.send(embed=embed, view=view)


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


@bot.command(name="bear")
async def prefix_bear(ctx):
    embed = discord.Embed(
        title="🐻 Master Bear Trap Strategy Cheat Sheet",
        description="Maximize your alliance Bear Trap damage score with core Whiteout Survival battle mechanics:",
        color=FROSTY_COLOR
    )
    embed.add_field(
        name="🏹 Optimal Troop Ratio: `10 / 10 / 80`",
        value="• **10% Infantry**\n• **10% Lancers**\n• **80% Marksmen**\n*(Bear deals zero lethal damage to frontlines—Marksmen deal ~2.2x damage!)*",
        inline=False
    )
    embed.add_field(
        name="⭐ Top 4 Rally Joiners: Jessie / Jader / Seo-yoon",
        value="• The **first 4 joiners** MUST send **Jessie (+25% Dmg)**, **Jader (+25% Dmg)**, or **Seo-yoon (+20% Attack)** as their 1st Hero.\n• Stacks up to **+100% total damage boost** for the entire rally!",
        inline=False
    )
    embed.add_field(
        name="⚡ Fast March Rotation",
        value="• Use 25% March Speedups to return quickly.\n• Keep all 4-6 march queues cycling into open alliance rallies without downtime.",
        inline=False
    )
    await ctx.send(embed=embed)


@bot.command(name="bearsim")
async def prefix_bearsim(ctx, *, args: str = "150000 T10 10/10/80 4"):
    parts = args.strip().split()
    cap = 150000
    tier = "T10"
    ratio_str = "10/10/80"
    joiners = 4

    if len(parts) >= 1 and parts[0].isdigit():
        cap = int(parts[0])
    if len(parts) >= 2:
        tier = parts[1].upper()
    if len(parts) >= 3:
        ratio_str = parts[2]
    if len(parts) >= 4 and parts[3].isdigit():
        joiners = max(0, min(4, int(parts[3])))

    tier_mults = {"T8": 1.0, "T9": 1.35, "T10": 1.85, "T11": 2.45, "T12": 3.20}
    t_mult = tier_mults.get(tier, 1.85)

    if "0/20/80" in ratio_str:
        inf_pct, lan_pct, mrk_pct, r_mult = 0.0, 0.20, 0.80, 1.90
    elif "33/33/33" in ratio_str or "equal" in ratio_str.lower():
        inf_pct, lan_pct, mrk_pct, r_mult = 0.334, 0.333, 0.333, 1.00
    else:
        inf_pct, lan_pct, mrk_pct, r_mult = 0.10, 0.10, 0.80, 1.95

    inf_count = int(cap * inf_pct)
    lan_count = int(cap * lan_pct)
    mrk_count = cap - inf_count - lan_count

    joiner_bonus_pct = joiners * 25
    joiner_mult = 1.0 + (joiner_bonus_pct / 100.0)

    total_multiplier = t_mult * r_mult * joiner_mult
    surge_pct = ((total_multiplier / (t_mult * 1.0 * 1.0)) - 1.0) * 100.0

    embed = discord.Embed(
        title="🐻 Bear Trap Tactical Damage Simulator",
        description=f"Configuration: **{cap:,} Troops** ({tier}) with **{ratio_str}**",
        color=SUCCESS_COLOR
    )
    embed.add_field(name="Overall Damage Multiplier", value=f"💥 **{total_multiplier:.2f}x Damage Boost**", inline=True)
    embed.add_field(name="DPS Surge vs Standard", value=f"🚀 **+{surge_pct:.0f}% Damage**", inline=True)
    embed.add_field(name="Joiner Buff Contribution", value=f"⭐ **{joiners} Jessie Joiners (+{joiner_bonus_pct}%)**", inline=True)
    embed.add_field(
        name="🏹 Exact Troop Breakdown",
        value=f"• 🛡️ **Infantry:** `{inf_count:,}` ({(inf_pct*100):.0f}%)\n"
              f"• 🐎 **Lancers:** `{lan_count:,}` ({(lan_pct*100):.0f}%)\n"
              f"• 🏹 **Marksmen:** `{mrk_count:,}` ({(mrk_pct*100):.0f}%)",
        inline=False
    )
    embed.set_footer(text="💡 Tip: Marksmen deal ~2.2x damage vs Bear Trap!")
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
async def prefix_codes(ctx, action: Optional[str] = None, arg1: Optional[str] = None, arg2: Optional[str] = None, *, extra: Optional[str] = None):
    data = load_utility_data()
    gift_codes = data.get("gift_codes", list(ACTIVE_GIFT_CODES))

    act = action.lower() if action else "view"

    if act == "register":
        if not arg1 or not arg2 or not arg1.isdigit() or not arg2.isdigit():
            await ctx.send(f"⚠️ Usage: `{COMMAND_PREFIX}codes register <PLAYER_ID> <STATE> [LABEL]` (e.g. `{COMMAND_PREFIX}codes register 12345678 542 Farm1`)")
            return
        pid = arg1.strip()
        state = int(arg2)
        label = extra.strip() if extra else None

        current_accounts = registered_players.get_player_accounts(ctx.author.id)
        existing_pids = [a["player_id"] for a in current_accounts]
        if len(current_accounts) >= registered_players.MAX_ACCOUNTS_PER_USER and pid not in existing_pids:
            await ctx.send(f"⚠️ You already have {registered_players.MAX_ACCOUNTS_PER_USER} accounts registered. Use `{COMMAND_PREFIX}codes unregister <PID>` first.")
            return

        check_res = await redeem_gift_code(pid, state, "gogoWOS")
        if check_res.get("err_code") == 40020:
            await ctx.send(f"❌ **Verification Failed:** Player ID `{pid}` was not found in State `{state}` on Century Games servers.")
            return
        success, msg, acc = registered_players.register_player(ctx.author.id, pid, state, label=label, notify_dm=True)
        if not success:
            await ctx.send(msg)
            return

        total = len(registered_players.get_player_accounts(ctx.author.id))
        await ctx.send(f"✅ **Registered {acc.get('label', 'Main')}!** Player ID `{pid}` (State `{state}`) active for auto-claim! (Slot {total}/{registered_players.MAX_ACCOUNTS_PER_USER})")
        return

    elif act == "status":
        accounts = registered_players.get_player_accounts(ctx.author.id)
        if not accounts:
            await ctx.send(f"📋 You are not registered yet. Use `{COMMAND_PREFIX}codes register <PLAYER_ID> <STATE>` to sign up!")
            return

        lines = [f"📊 **Auto-Claim Status ({len(accounts)}/{registered_players.MAX_ACCOUNTS_PER_USER} Accounts):**"]
        for i, acc in enumerate(accounts, 1):
            lbl = acc.get("label", f"Account #{i}")
            pid = acc.get("player_id")
            st = acc.get("state")
            cnt = len(acc.get("claimed_codes", []))
            lines.append(f"• **{lbl}:** ID `{pid}` | State `{st}` | Claimed: `{cnt}`")
        await ctx.send("\n".join(lines))
        return

    elif act == "unregister":
        clean_pid = arg1.strip() if arg1 else None
        success, msg = registered_players.unregister_player(ctx.author.id, clean_pid)
        await ctx.send(msg)
        return

    elif act == "claim":
        user_accounts = registered_players.get_player_accounts(ctx.author.id)
        # Case A: Specific PID and state supplied
        if arg1 and arg2 and arg1.isdigit() and arg2.isdigit():
            pid = arg1.strip()
            st = int(arg2)
            cdk = extra.strip() if extra else (gift_codes[0]["code"] if gift_codes else "gogoWOS")
            res = await redeem_gift_code(pid, st, cdk)
            registered_players.record_claim_for_account(ctx.author.id, pid, cdk, res["success"], res["message"])
            await ctx.send(f"🎁 **Redemption Result ({pid}):** {res['message']}")
            return

        # Case B: Claim for all registered accounts
        if not user_accounts:
            await ctx.send(f"⚠️ Register first with `{COMMAND_PREFIX}codes register <ID> <STATE>` or run `/codes claim`.")
            return

        cdk = arg1.strip() if arg1 else (gift_codes[0]["code"] if gift_codes else "gogoWOS")
        results = []
        for acc in user_accounts:
            pid = acc["player_id"]
            st = acc["state"]
            lbl = acc.get("label", "Account")
            res = await redeem_gift_code(pid, st, cdk)
            registered_players.record_claim_for_account(ctx.author.id, pid, cdk, res["success"], res["message"])
            icon = "✅" if res["success"] else "ℹ️"
            results.append(f"{icon} **{lbl}** (`{pid}`): {res['message']}")
            if len(user_accounts) > 1:
                await asyncio.sleep(1.0)

        await ctx.send(f"🎁 **Claim Results for `{cdk}`:**\n" + "\n".join(results))
        return

    elif act in ["add", "remove"]:
        if not is_authorized_admin(ctx.author):
            await ctx.send("⛔ Access Denied.")
            return
        clean_code = arg1.strip() if arg1 else None
        if not clean_code:
            await ctx.send(f"⚠️ Usage: `{COMMAND_PREFIX}codes add <CODE> <rewards>` or `{COMMAND_PREFIX}codes remove <CODE>`")
            return
        if act == "add":
            rew = f"{arg2} {extra}".strip() if (arg2 or extra) else "Free In-Game Rewards"
            gift_codes.insert(0, {"code": clean_code, "status": "🟢 Active & Verified", "rewards": rew})
            data["gift_codes"] = gift_codes
            save_utility_data(data)
            asyncio.create_task(dispatch_auto_claim(clean_code))
            await ctx.send(f"✅ Code `{clean_code}` added and auto-claim queue triggered across all registered players!")
            return
        elif act == "remove":
            data["gift_codes"] = [c for c in gift_codes if c["code"].lower() != clean_code.lower()]
            save_utility_data(data)
            await ctx.send(f"🗑️ Code `{clean_code}` removed.")
            return

    # View codes (Default Dashboard)
    embed, file = build_codes_dashboard_embed()
    view = CodesActionView()
    if file:
        await ctx.send(embed=embed, file=file, view=view)
    else:
        await ctx.send(embed=embed, view=view)


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


@bot.command(name="reindex")
async def prefix_reindex(ctx, local_only: str = "true"):
    if not is_authorized_admin(ctx.author):
        await ctx.send(f"⛔ **Access Denied:** Only authorized Commander(s) (`{', '.join(AUTHORIZED_ADMIN_USERNAMES)}`) can trigger database reindexing.")
        return

    is_local = local_only.lower() in ["true", "1", "yes", "local"]
    async with ctx.typing():
        loop = asyncio.get_running_loop()
        try:
            new_count = await loop.run_in_executor(None, run_full_reindex, is_local)
            knowledge_base.reload_dynamic_entities()

            embed = discord.Embed(
                title="✨ Knowledge Re-indexing Complete!",
                description=f"Commander **{ctx.author.display_name}** (`@{ctx.author.name}`), tactical archives have been refreshed!",
                color=SUCCESS_COLOR
            )
            embed.add_field(name="📚 Total Chunks", value=f"`{new_count}` knowledge chunks", inline=True)
            embed.add_field(name="👑 Hero Generations", value=f"Gen 0 ➔ Gen `{knowledge_base.max_generation}+`", inline=True)
            embed.add_field(name="🛡️ Active Heroes", value=f"`{len(knowledge_base.known_heroes)}` heroes indexed", inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ **Reindexing Error:** `{str(e)}`")


@bot.command(name="sendmessage")
async def prefix_sendmessage(ctx, *, message: str):
    if not is_authorized_admin(ctx.author):
        await ctx.send(f"⛔ **Access Denied:** Only the Supreme Commander (`{', '.join(AUTHORIZED_ADMIN_USERNAMES)}`) can broadcast announcements across servers.")
        return

    async with ctx.typing():
        success, fail, reports = await broadcast_announcement_to_guilds(ctx.author, message)
        lines = []
        for r in reports[:30]:
            status_icon = "✅" if r["status"] == "success" else "⚠️"
            lines.append(f"{status_icon} **{r['guild'][:22]}** ➔ `{r['channel']}`")

        breakdown_text = "\n".join(lines)
        if len(reports) > 30:
            breakdown_text += f"\n*...and {len(reports) - 30} more servers.*"

        res_embed = discord.Embed(
            title="📢 Broadcast Transmission Complete",
            description=f"Your message was broadcast across active Discord servers!\n\n"
                        f"• ✅ **Delivered to:** `{success}` servers\n"
                        f"• ⚠️ **Skipped (No Perms/Hidden):** `{fail}` servers\n"
                        f"• 🌐 **Total Connected Servers:** `{len(bot.guilds)}`\n\n"
                        f"**📋 Delivery Destinations:**\n{breakdown_text}",
            color=SUCCESS_COLOR
        )
        await ctx.send(embed=res_embed)



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
