import os
from nextcord import Intents
import nextcord
from dotenv import load_dotenv
from nextcord import Interaction, SlashOption
from nextcord.ext import commands


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('COMMAND_PREFIX')

intents = nextcord.Intents.all()

bot = commands.Bot(PREFIX, intents = intents)
path = "src/cogs"

initial_extensions = []


for filename in os.listdir(path):
        if filename.endswith('.py'):
            initial_extensions.append("cogs." + filename[:-3])
if __name__ == '__main__':
        for extension in initial_extensions:
            bot.load_extension(extension)




@bot.event
async def on_ready():
    print(f'{bot.user} has logged in.')

@bot.event
async def on_member_join(member):
    guild = member.guild
    guild_id = guild.id
    my_server = 390194259405438989
    if guild.system_channel is not None and guild_id == my_server:
        msg = f"da kommen ja noch mehr affen rein in den discord, cool hallo {member.mention}\nich hab schon viele sachen über dich gehört\nmostly flame von lukas und den anderen, aber das ist ja normal von denen ^^"
        await guild.system_channel.send(msg)    


testServerId = [383717798813106186, 390194259405438989]


bot.run(TOKEN)