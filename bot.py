import discord
from discord.ext import commands
import chromadb
from google import genai
from google.genai import types  # Added for retry options
from dotenv import load_dotenv
import os
import psutil
import logging

# 1. Load Secrets
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# 2. Setup AI with Auto-Retry Logic
# This configuration will automatically retry up to 3 times if the API fails
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        retry_options=types.RetryOptions(max_attempts=3)
    )
)
MODEL_ID = 'gemini-3-flash-preview'

# Connect to the brain you already built
chroma_client = chromadb.PersistentClient(path="./frosty_brain")
collection = chroma_client.get_or_create_collection(name="wos_knowledge")

# 3. Setup Discord Bot
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

def get_ai_response(user_question):
    try:
        # Search the brain for relevant facts
        results = collection.query(query_texts=[user_question], n_results=3)
        context = "\n\n".join(results['documents'][0])
        
        prompt = f"""
        You are 'Frosty', a Whiteout Survival expert AI. 
        Using this data: {context}
        Answer this question: {user_question}
        Tone: Professional, expert Chief.
        """

        # Generate response using the retry-enabled client
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt
        )

        # Enhanced Parsing: Handle Gemini 3's multi-part responses
        if response.candidates and response.candidates[0].content.parts:
            # Filter for text parts and join them (skips internal "thinking" blocks)
            full_text = "".join([part.text for part in response.candidates[0].content.parts if part.text])
            if full_text.strip():
                return full_text
        
        return "I processed the data, but the response was empty. Please try again!"

    except Exception as e:
        logging.error(f"Error in get_ai_response: {e}")
        return "I'm having a bit of a brain freeze right now. Please try again in a second!"

@bot.event
async def on_ready():
    print(f'❄️ Frosty is active and using the brain built from {collection.count()} pages!')
    await bot.change_presence(activity=discord.Game(name="Whiteout Survival | !wos"))

@bot.command(name='wos')
async def wos(ctx, *, question):
    async with ctx.typing():
        answer = get_ai_response(question)
        
        # Handle Discord's 2000 character limit
        if len(answer) > 2000:
            for i in range(0, len(answer), 2000):
                await ctx.send(answer[i:i+2000])
        else:
            await ctx.send(answer)

@bot.command(name='status')
async def status(ctx):
    process = psutil.Process(os.getpid())
    ram = process.memory_info().rss / 1024 / 1024
    await ctx.send(f"📊 **Frosty Stats:**\n• Status: Online\n• RAM Usage: {ram:.2f} MB\n• Database: {collection.count()} pages indexed")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
