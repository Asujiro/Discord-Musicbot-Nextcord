import asyncio
import logging
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

import wavelink
# path for cog loading
dirname = os.path.dirname(__file__)

# load .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('COMMAND_PREFIX')
ADMIN_USER = os.getenv('ADMIN_USER')
OPENAI_KEY = os.getenv('API_KEY')
PASSWORD = os.getenv('PASSWORD')
my_server = 390194259405438989

initial_extensions = ['cogs.music', 'cogs.events']


# Here we load our extensions(cogs) listed above in [initial_extensions].

# commands

class Bot(commands.Bot):
    def __init__(self) -> None:
        intents: discord.Intents = discord.Intents.default()
        intents.message_content = True

        discord.utils.setup_logging(level=logging.INFO)
        super().__init__(command_prefix="?", intents=intents)

    async def setup_hook(self) -> None:

        nodes = [wavelink.Node(uri="http://localhost:2333", password=PASSWORD)]

        # cache_capacity is EXPERIMENTAL. Turn it off by passing None
        await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=None)
        await bot.tree.sync()
        
  

        

bot: Bot = Bot()

async def load_extension() -> None:
    if __name__ == '__main__':
        for extension in initial_extensions:
            await bot.load_extension(extension)
            print(extension)

# Welcome Message for my server





# Console message on start up
@bot.event
async def on_ready():
    print(f'{bot.user} has logged in.')

async def main() -> None:
    async with bot:
        await load_extension()
        await bot.start(TOKEN)

asyncio.run(main())