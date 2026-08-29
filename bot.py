"""
❄️ Frosty AI - Next-Level Whiteout Survival Discord Bot
Features Slash Commands, Autocomplete, Hybrid RAG, Multi-Provider AI (Gemini/Groq/OpenAI),
Interactive UI Buttons, Rich Embeds, and Multi-Turn Conversation Memory.
"""

import os
import time
import asyncio
import logging
import psutil
from typing import Optional, List, Dict, Tuple

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
        elapsed = time.time() - start_time
        embed = discord.Embed(
            title="✨ Knowledge Base Re-indexed Successfully",
            description=f"Frosty's brain has been refreshed with the latest strategy guides!\n\n• **Total Chunks in DB:** `{new_count}`\n• **Elapsed Time:** `{elapsed:.2f}s`",
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


@bot.tree.command(name="help", description="Show Frosty AI commands and strategic capabilities.")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="❄️ Frosty AI - Tactical Command Center",
        description="Welcome Chief! I am **Frosty**, your tactical AI advisor for Whiteout Survival.\nUse either `/` Slash Commands or `!` prefix commands:",
        color=FROSTY_COLOR
    )
    embed.add_field(name="⚔️ `/wos [question]` or `!wos`", value="Ask any strategic question (e.g. *'what is a hero lineup'*, *'Flint vs Jeronimo'*).", inline=False)
    embed.add_field(name="👑 `/hero [name]` or `!hero`", value="Get detailed skill breakdowns, gear recommendations, and evaluations for any hero.", inline=False)
    embed.add_field(name="🛡️ `/lineup [mode] [gen]` or `!lineup`", value="Get recommended 3-hero formations and troop ratios (50/20/30, 4-1-1).", inline=False)
    embed.add_field(name="🐻 `/bear` or `!bear`", value="Instant Bear Trap guide (10/10/80 ratio, Jessie/Seo-yoon joiner damage buffs).", inline=False)
    embed.add_field(name="📅 `/event [name]` or `!event`", value="Walkthroughs for Crazy Joe, Foundry Battle, Frostfire Mine, and SvS.", inline=False)
    embed.add_field(name="📚 `/expert [name]` or `!expert`", value="Dawn Academy expert advice and breakpoint pausing guide.", inline=False)
    embed.add_field(name="📊 `/status` or `!status`", value="Check live Discord servers, total members reached, AI model, and RAM usage.", inline=False)
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


@bot.command(name="hero")
async def prefix_hero(ctx, *, hero_name: str):
    async with ctx.typing():
        query = f"Provide a complete tactical guide and evaluation for Hero: {hero_name}."
        embed, view = await generate_frosty_response(ctx.channel.id, ctx.author, query)
        await ctx.send(embed=embed, view=view)


@bot.command(name="lineup")
async def prefix_lineup(ctx, *, args: str = "Exploration"):
    async with ctx.typing():
        query = f"What is the optimal hero lineup and troop ratio for: {args}?"
        embed, view = await generate_frosty_response(ctx.channel.id, ctx.author, query)
        await ctx.send(embed=embed, view=view)


@bot.command(name="bear")
async def prefix_bear(ctx):
    async with ctx.typing():
        query = "Give a concise master guide for Bear Trap: troop ratios, rally leader heroes, and Jessie joiner damage buffs."
        embed, view = await generate_frosty_response(ctx.channel.id, ctx.author, query)
        await ctx.send(embed=embed, view=view)


@bot.command(name="event")
async def prefix_event(ctx, *, event_name: str):
    async with ctx.typing():
        query = f"Provide an in-depth master guide for event: {event_name}."
        embed, view = await generate_frosty_response(ctx.channel.id, ctx.author, query)
        await ctx.send(embed=embed, view=view)


@bot.command(name="expert")
async def prefix_expert(ctx, *, expert_name: str):
    async with ctx.typing():
        query = f"Provide a complete breakdown for Dawn Academy Expert: {expert_name}."
        embed, view = await generate_frosty_response(ctx.channel.id, ctx.author, query)
        await ctx.send(embed=embed, view=view)


@bot.command(name="status")
async def prefix_status(ctx):
    process = psutil.Process(os.getpid())
    ram = process.memory_info().rss / 1024 / 1024
    total_guilds = len(bot.guilds)
    total_members = sum(g.member_count for g in bot.guilds if g.member_count)

    embed = discord.Embed(title="📊 Frosty Stats", color=FROSTY_COLOR)
    embed.add_field(name="🌐 Servers", value=f"**{total_guilds}**", inline=True)
    embed.add_field(name="👥 Members", value=f"**{total_members:,}**", inline=True)
    embed.add_field(name="Engine", value=f"`{ai_engine.get_active_model_name()}`", inline=True)
    embed.add_field(name="Database", value=f"`{knowledge_base.get_count()} chunks`", inline=True)
    embed.add_field(name="RAM Usage", value=f"`{ram:.1f} MB`", inline=True)
    embed.add_field(name="Ping", value=f"`{bot.latency * 1000:.1f} ms`", inline=True)
    await ctx.send(embed=embed)


@bot.command(name="reindex")
async def prefix_reindex(ctx, local_only: str = "true"):
    is_admin = ctx.author.id in ADMIN_USER_IDS or (ctx.author.guild_permissions.administrator if ctx.guild else False)
    if not is_admin:
        await ctx.send("❌ You need administrator permissions to reindex.")
        return

    is_local = local_only.lower() in ["true", "1", "yes", "local"]
    async with ctx.typing():
        loop = asyncio.get_running_loop()
        try:
            new_count = await loop.run_in_executor(None, run_full_reindex, is_local)
            await ctx.send(f"✨ **Re-indexing Complete!** Database now contains `{new_count}` knowledge chunks.")
        except Exception as e:
            await ctx.send(f"❌ **Re-indexing Error:** `{str(e)}`")


@bot.command(name="help")
async def prefix_help(ctx):
    embed = discord.Embed(
        title="❄️ Frosty AI - Command List",
        description=f"Use prefix `{COMMAND_PREFIX}` or `/` Slash commands:\n\n"
                    f"• `{COMMAND_PREFIX}wos <question>` - Ask anything\n"
                    f"• `{COMMAND_PREFIX}hero <name>` - Hero guides\n"
                    f"• `{COMMAND_PREFIX}lineup <mode>` - Lineups & ratios\n"
                    f"• `{COMMAND_PREFIX}bear` - Bear Trap tactics\n"
                    f"• `{COMMAND_PREFIX}event <name>` - Event walkthroughs\n"
                    f"• `{COMMAND_PREFIX}expert <name>` - Dawn Academy advice\n"
                    f"• `{COMMAND_PREFIX}status` - System health\n"
                    f"• `{COMMAND_PREFIX}reindex` - [Admin] Refresh database",
        color=FROSTY_COLOR
    )
    await ctx.send(embed=embed)


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
