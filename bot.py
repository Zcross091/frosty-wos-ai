import discord
from discord.ext import commands
import chromadb
from google import genai
from google.genai import types 
from dotenv import load_dotenv
import os
import psutil
import logging

# 1. Load Secrets
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# 2. Setup AI with Correct 2026 Syntax & Retry Logic
# HttpRetryOptions is the required syntax for the 2026 SDK.
retry_config = types.HttpRetryOptions(
    attempts=3,
    initial_delay=2.0,
    http_status_codes=[408, 429, 500, 502, 503, 504]
)

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(retry_options=retry_config)
)

# CHANGED: Moving to 3.1 Flash-Lite for the highest FREE quota available in 2026.
MODEL_ID = 'gemini-3.1-flash-lite-preview'

# Connect to your 3,391-page vector database
chroma_client = chromadb.PersistentClient(path="./frosty_brain")
collection = chroma_client.get_or_create_collection(name="wos_knowledge")

# 3. Setup Discord Bot
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

def get_ai_response(user_question):
    try:
        # Search the database for relevant Whiteout Survival strategy
        results = collection.query(query_texts=[user_question], n_results=3)
        context = "\n\n".join(results['documents'][0])
        
        prompt = f"""
        You are 'Frosty', a Whiteout Survival expert AI. 
        Using this data: {context}
        Answer this question: {user_question}
        Tone: Professional, expert Chief.
        """

        # Generate response using the high-volume Lite model
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt
        )

        # Enhanced Parsing: Filters out AI 'thought' blocks
        if response.candidates and response.candidates[0].content.parts:
            full_text = "".join([part.text for part in response.candidates[0].content.parts if part.text])
            if full_text.strip():
                return full_text
        
        return "I processed the data, but the response was empty. Please try again!"

    except Exception as e:
        logging.error(f"Error in get_ai_response: {e}")
        return "I'm having a bit of a brain freeze (Quota Limit). Please try again in a moment!"

@bot.event
async def on_ready():
    print(f'❄️ Frosty is active on {MODEL_ID}!')
    await bot.change_presence(activity=discord.Game(name="Whiteout Survival | !wos"))

@bot.command(name='wos')
async def wos(ctx, *, question):
    async with ctx.typing():
        answer = get_ai_response(question)
        if len(answer) > 2000:
            for i in range(0, len(answer), 2000):
                await ctx.send(answer[i:i+2000])
        else:
            await ctx.send(answer)

@bot.command(name='status')
async def status(ctx):
    process = psutil.Process(os.getpid())
    ram = process.memory_info().rss / 1024 / 1024
    await ctx.send(f"📊 **Frosty Stats:**\n• Model: {MODEL_ID}\n• Status: Online\n• RAM Usage: {ram:.2f} MB\n• Database: {collection.count()} pages indexed")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
