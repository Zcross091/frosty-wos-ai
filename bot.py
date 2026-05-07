import discord
from discord.ext import commands
import chromadb
from google import genai
from dotenv import load_dotenv
import os
import psutil
import logging

# 1. Load Secrets
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# 2. Setup AI & Database
# Using the 2026 Recommended SDK
client = genai.Client(api_key=GEMINI_API_KEY)
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

        # Generate response using the new 2026 client
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt
        )

        if response.text:
            return response.text
        return "I processed the data, but couldn't generate a clear answer. Try rephrasing!"

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
        # Running the AI query
        answer = get_ai_response(question)
        
        # Split message if it exceeds Discord's 2000 char limit
        if len(answer) > 2000:
            for i in range(0, len(answer), 2000):
                await ctx.send(answer[i:i+2000])
        else:
            await ctx.send(answer)

@bot.command(name='status')
async def status(ctx):
    process = psutil.Process(os.getpid())
    ram = process.memory_info().rss / 1024 / 1024
    uptime = "Online" # You can add a proper timer here if needed
    await ctx.send(f"📊 **Frosty Stats:**\n• Status: {uptime}\n• RAM Usage: {ram:.2f} MB\n• Database: {collection.count()} pages")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
