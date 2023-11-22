
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, Embed, SlashOption


class Utility(commands.Cog):

    @nextcord.slash_command(name="vx", description="convert x.com to vxtwitter.com")
    async def play(self, interaction: Interaction, *, link: str = SlashOption(description="x.com, twitter.com")):

        if "x.com" in link:
            modified_url = link.replace("x.com", "vxtwitter.com")
            return await interaction.response.send_message(modified_url)
        elif "twitter.com" in link:
            modified_url = link.replace("twitter.com", "vxtwitter.com")
            return await interaction.response.send_message(modified_url)
        else:
            return await interaction.response.send_message(
                "The URL does not contain 'x.com' or 'twitter.com'. No replacement performed.")


def setup(bot):
    bot.add_cog(Utility(bot))
