import os
import re
from dotenv import load_dotenv, find_dotenv
import nextcord
import lavalink
from nextcord.ext import commands
from lavalink.filters import LowPass
from nextcord import Interaction, Embed, SlashOption
class Utility(commands.Cog):

    @nextcord.slash_command(name="vx", description="convert x.com to vxtwitter.com")
    async def play(self, interaction: Interaction, *, original_url: str = SlashOption(description="x.com")):

        if "x.com" in original_url:
            modified_url = original_url.replace("x.com", "vxtwitter.com")
            print(modified_url)
        else:
            return await interaction.response.send_message("The URL does not contain 'x.com'. No replacement performed.")

def setup(bot):
    bot.add_cog(Utility(bot))