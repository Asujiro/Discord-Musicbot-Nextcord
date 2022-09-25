
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
from nextcord import utils

TESTING_GUILD_ID = [383717798813106186, 390194259405438989]

class testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    

    @nextcord.slash_command(name = "test", description="hallo sagen", guild_ids=TESTING_GUILD_ID)
    async def test(self, interaction: Interaction):
        await interaction.response.send_message("Hello, sag hallo")

    @nextcord.slash_command(guild_ids=TESTING_GUILD_ID)
    async def ping(self, interaction: Interaction):
        await interaction.response.send_message("Pong!")


    @nextcord.slash_command(guild_ids=TESTING_GUILD_ID)
    async def echo(self, interaction: Interaction, arg: str):
        await interaction.response.send_message(arg)


    @nextcord.slash_command(guild_ids=TESTING_GUILD_ID)
    async def enter_a_number(self, interaction: Interaction, number: int = SlashOption(required=False)):
        if not number:
            await interaction.response.send_message("You need to specify a number!", ephemeral=True)
        else:
            await interaction.response.send_message(f"You chose {number}!")
        

    
            

def setup(bot):
    bot.add_cog(testing(bot))
