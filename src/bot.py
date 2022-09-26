from distutils import extension
import os
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, Embed, SlashOption
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


@nextcord.slash_command(name="load", description="reload cog")
async def reload_cog(self, interaction: Interaction, *, extention: str = SlashOption(description="cog name")):
    if interaction.user.id == 218427048153055233:
        bot.load_extension(f"cogs.{extention}")
        await interaction.response.send_message("Loaded Cog!")
    else:
        await interaction.response.send_message("You need to be an Aplication Admin!")

@nextcord.slash_command(name="unload", description="unload cog")
async def unload_cog(self, interaction: Interaction, *, extention: str = SlashOption(description="cog name")):
    if interaction.user.id == 218427048153055233:
        bot.unload_extension(f"cogs.{extention}")
        await interaction.response.send_message("Unloaded Cog!" + extention)
    else:
        await interaction.response.send_message("You need to be an Aplication Admin!")

@nextcord.slash_command(name="reload", description="reload cog")
async def reload_cog(self, interaction: Interaction, *, extention: str = SlashOption(description="cog name")):
    if interaction.user.id == 218427048153055233:
        bot.reload_extension(f"cogs.{extention}")
        await interaction.response.send_message("Reloaded Cog!")
    else:
        await interaction.response.send_message("You need to be an Aplication Admin!")



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