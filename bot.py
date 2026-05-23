import discord
from discord.ext import commands
import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
import psutil

# 1. Load Secrets
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# 2. Setup Groq
client = Groq(api_key=GROQ_API_KEY)
MODEL_ID = "llama-3.1-8b-instant"

# Connect to the local vector database
chroma_client = chromadb.PersistentClient(path="./frosty_brain")
collection = chroma_client.get_or_create_collection(name="wos_knowledge")

# 3. Setup Discord Bot
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

def get_ai_response(user_question):
    try:
        # Searching 3 results as requested
        results = collection.query(query_texts=[user_question], n_results=3)
        context = "\n\n".join(results['documents'][0])
        
        # Upgraded Balanced System Prompt
        system_prompt = f"""
You are 'Frosty', the premier Whiteout Survival tactical oracle. You must use the provided data to answer accurately without inventing stats, multipliers, or fake values.

Data Context: {context}

Strict Layout Budget (To prevent token overflow and formatting errors):
1. Give a 1-2 sentence direct summary answer first.
2. Use a short bulleted list comparing *only* the specific stats requested. Skip long skill fluff.
3. Conclude with a single clear line marked '**Final Verdict**'.
Keep your writing factual, concise, and dense with real data.
"""
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            temperature=0.7
        )

        return completion.choices[0].message.content

    except Exception as e:
        return f"⚠️ Engine Error: {str(e)}"

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
    await ctx.send(f"📊 **Frosty Stats:**\n• Engine: {MODEL_ID}\n• RAM Usage: {ram:.2f} MB\n• Database: {collection.count()} pages indexed")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
