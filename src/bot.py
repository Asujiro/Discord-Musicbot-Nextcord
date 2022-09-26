import os
import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv

dirname = os.path.dirname(__file__)

#load .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('COMMAND_PREFIX')

#comands
intents = nextcord.Intents.all()
bot = commands.Bot(PREFIX, intents = intents)
initial_extensions = []


#load cogs
for filename in os.listdir(dirname + "/cogs"):
        if filename.endswith('.py'):
            bot.load_extension(f"cogs.{filename[:-3]}")

#Welcome Message for my server
@bot.event
async def on_member_join(member):
    guild = member.guild
    guild_id = guild.id
    my_server = 390194259405438989
    if guild.system_channel is not None and guild_id == my_server:
        msg = f"da kommen ja noch mehr affen rein in den discord, cool hallo {member.mention}\nich hab schon viele sachen über dich gehört\nmostly flame von lukas und den anderen, aber das ist ja normal von denen ^^"
        await guild.system_channel.send(msg)    

#Console message on start up
@bot.event
async def on_ready():
    print(f'{bot.user} has logged in.')

bot.run(TOKEN)