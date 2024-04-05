import os
from urllib.parse import urlparse, urlunparse
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, Embed, SlashOption
from dotenv import load_dotenv

#path for cog loading
dirname = os.path.dirname(__file__)

#load .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('COMMAND_PREFIX')
ADMIN_USER = os.getenv('ADMIN_USER')
my_server = 390194259405438989

#comands
intents = nextcord.Intents.all()
bot = commands.Bot(PREFIX, intents = intents)
initial_extensions = []

#load cogs
for filename in os.listdir(dirname + "/cogs"):
        if filename.endswith('.py'):
            bot.load_extension(f"cogs.{filename[:-3]}")
            print(filename)
#Welcome Message for my server
@bot.event
async def on_member_join(member):
    guild = member.guild
    guild_id = guild.id
    if guild.system_channel is not None and guild_id == my_server:
        msg = f"da kommen ja noch mehr affen rein in den discord, cool hallo {member.mention}\nich hab schon viele sachen über dich gehört\nmostly flame von lukas und den anderen, aber das ist ja normal von denen ^^"
        await guild.system_channel.send(msg)


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.guild.id == my_server:
        words = message.content.split()
        modified_content = message.content
        for word in words:
            parsed_url = urlparse(word)
            if parsed_url.scheme and parsed_url.netloc:
                if parsed_url.netloc in ["twitter.com", "x.com"] and parsed_url.path:
                    # Ersetze "twitter.com" oder "x.com" durch "vxtwitter"
                    modified_netloc = "vxtwitter.com"
                    modified_url = parsed_url._replace(netloc=modified_netloc)
                    # Ersetze das original Wort mit dem modifizierten URL in der Nachricht
                    modified_content = modified_content.replace(word, urlunparse(modified_url))
        
                    mentioned_users = message.mentions
        # Baue die modifizierte Nachricht mit den getaggten Benutzern
                    modified_content = f'{modified_content} {" ".join(user.mention for user in mentioned_users).join(" ")}'
        
                    await message.delete()
                    await message.channel.send(f'Send by {message.author.mention}: {modified_content}')
        
                    await bot.process_commands(message)
                     
                


#Console message on start up
@bot.event
async def on_ready():
    print(f'{bot.user} has logged in.')


bot.run(TOKEN)