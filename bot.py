import discord
from discord.ext import commands
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv
import os
import psutil

# 1. Load Secrets
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# 2. Setup AI & Database
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Connect to the brain you already built
chroma_client = chromadb.PersistentClient(path="./frosty_brain")
collection = chroma_client.get_or_create_collection(name="wos_knowledge")

# 3. Setup Discord Bot
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

def get_ai_response(user_question):
    # Search the brain for relevant facts
    results = collection.query(query_texts=[user_question], n_results=2)
    context = "\n\n".join(results['documents'][0])
    
    prompt = f"""
    You are 'Frosty', a Whiteout Survival expert AI. 
    Using this data: {context}
    Answer this question: {user_question}
    Tone: Professional, expert Chief.
    """
    response = model.generate_content(prompt)
    return response.text

@bot.event
async def on_ready():
    print(f'❄️ Frosty is active and using the brain built from {collection.count()} pages!')

@bot.command(name='wos')
async def wos(ctx, *, question):
    async with ctx.typing():
        answer = get_ai_response(question)
        await ctx.send(answer[:2000]) # Stay under Discord's limit

@bot.command(name='status')
async def status(ctx):
    ram = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    await ctx.send(f"📊 **Frosty Stats:** RAM Usage: {ram:.2f} MB")

bot.run(DISCORD_TOKEN)
