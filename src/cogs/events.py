
import discord
from discord.ext import commands
from urllib.parse import urlparse, urlunparse
my_server = 390194259405438989

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, ctx):
        guild = ctx.guild
        guild_id = guild.id
        if guild.system_channel is not None and guild_id == my_server:
            msg = f"da kommen ja noch mehr affen rein in den discord, cool hallo {ctx.mention}\nich hab schon viele sachen über dich gehört\nmostly flame von lukas und den anderen, aber das ist ja normal von denen ^^"
            await guild.system_channel.send(msg)

    @commands.Cog.listener()
    async def on_message(slef, ctx):
        if ctx.author.bot:
            return

        if ctx.guild.id == my_server:
            words = ctx.content.split()
            modified_content = ctx.content
            for word in words:
                parsed_url = urlparse(word)
                if parsed_url.scheme and parsed_url.netloc:
                    if parsed_url.netloc in ["twitter.com", "x.com"] and parsed_url.path:
                        # Ersetze "twitter.com" oder "x.com" durch "vxtwitter"
                        modified_netloc = "vxtwitter.com"
                        modified_url = parsed_url._replace(netloc=modified_netloc)
                        # Ersetze das original Wort mit dem modifizierten URL in der Nachricht
                        modified_content = modified_content.replace(word, urlunparse(modified_url))

                        mentioned_users = ctx.mentions
                        # Baue die modifizierte Nachricht mit den getaggten Benutzern
                        modified_content = f'{modified_content} {" ".join(user.mention for user in mentioned_users)}'

                        await ctx.delete()
                        await ctx.channel.send(f'Send by {ctx.author.mention}: {modified_content}')

                        await self.bot.process_commands(ctx)
    

async def setup(bot):
    await bot.add_cog(Events(bot))
