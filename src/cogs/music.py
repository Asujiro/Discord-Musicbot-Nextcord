import os
import re

from discord import Interaction, Embed
from dotenv import load_dotenv, find_dotenv
import wavelink
from typing import cast

import discord
from discord.ext import commands
from discord import app_commands
import wavelink



url_rx = re.compile(r'https?://(?:www\.)?.+')

# loads Bot ID from .env
load_dotenv(find_dotenv())
BOT_ID = os.getenv('BOT_ID')
IP = os.getenv('IP')
PORT = os.getenv('PORT')
REGION = os.getenv('REGION')
NODE = os.getenv('NODE_NAME')
PASSWORD = os.getenv('PASSWORD')


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #Send connsole message when Node is connected    
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        print(f"Wavelink Node connected: {payload.node!r} | Resumed: {payload.resumed}")

    #Sends Now Playing message on start of new track
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        player: wavelink.Player | None = payload.player
        if not player:
            # Handle edge cases...
            return

        original: wavelink.Playable | None = payload.original
        track: wavelink.Playable = payload.track

        embed: discord.Embed = discord.Embed(title="Now Playing:")
        embed.description = f"**[{track.title}]({track.uri})** by `{track.author}`"

        if track.artwork:
            embed.set_image(url=track.artwork)

        if original and original.recommended:
            embed.description += f"\n\n`This track was recommended via {track.source}`"

        if track.album.name:
            embed.add_field(name="Album", value=track.album.name)

        await player.home.send(embed=embed)

    #Handels disconnect when queue is empty
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player: wavelink.Player | None = payload.player
        if not player.queue.is_empty:
            await player.play(player.queue.get())
        else:
            await player.disconnect()

    @app_commands.command(name="play", description="Play Song")
    async def play(self, interaction:Interaction, query: str):
        """Play a song with the given query."""
        print(query)
        if not Interaction.guild:
            return

        player: wavelink.Player
        player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore

        if not player:
            try:
                player = await interaction.user.voice.channel.connect(cls=wavelink.Player)  # type: ignore
            except AttributeError:
                embed = Embed(title="Please join a voice channel first before using this command.", color=discord.Color.blurple())
                await interaction.response.send_message(embed = embed)
                return
            except discord.ClientException:

                embed = Embed(title="I was unable to join this voice channel. Please try again.", color=discord.Color.blurple())
                await interaction.response.send_message(embed = embed)
                return

        # Turn on AutoPlay to enabled mode.
        # enabled = AutoPlay will play songs for us and fetch recommendations...
        # partial = AutoPlay will play songs for us, but WILL NOT fetch recommendations...
        # disabled = AutoPlay will do nothing...
        player.autoplay = wavelink.AutoPlayMode.disabled

        # Lock the player to this channel...
        if not hasattr(player, "home"):
            player.home = interaction.channel
        elif player.home != interaction.channel:
            embed = Embed(title=f"You can only play songs in {player.home.mention}, as the player has already started there.", color=discord.Color.blurple())
            await interaction.response.send_message(embed = embed)
            return

        # This will handle fetching Tracks and Playlists...
        # Seed the doc strings for more information on this method...
        # If spotify is enabled via LavaSrc, this will automatically fetch Spotify tracks if you pass a URL...
        # Defaults to YouTube for non URL based queries...
        tracks: wavelink.Search = await wavelink.Playable.search(query)
        if not tracks:
            embed = Embed(title="Could not find any tracks with that query. Please try again.", color=discord.Color.blurple())
            await interaction.response.send_message(embed = embed)
            return

        if isinstance(tracks, wavelink.Playlist):
            # tracks is a playlist...
            added: int = await player.queue.put_wait(tracks)
            embed = Embed(title=f"Added the playlist:", color=discord.Color.blurple())
            embed.description = f"**`{tracks.name}`** ({added} songs) to the queue."
            await interaction.response.send_message(embed = embed)
        else:
            track: wavelink.Playable = tracks[0]
            await player.queue.put_wait(track)
            embed: discord.Embed = discord.Embed(title="Track Enqueued:", color=discord.Color.blurple())
            embed.description = f"Added **[{track.title}]({track.uri})** to the queue."
            await interaction.response.send_message(embed = embed)

        if not player.playing:
            # Play now since we aren't playing anything...
            await player.play(player.queue.get(), volume=30)


    @app_commands.command(name="skip", description="Skip current track")
    async def skip(self, interaction: Interaction):
        """Skip the current song."""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        if not player:
            embed = Embed(title="Not Connected", color=discord.Color.blurple())
            await interaction.response.send_message(embed = embed)
        
        embed = Embed(title="Track Skipped", color=discord.Color.blurple())
        await player.skip(force=True)
        await interaction.response.send_message(embed = embed)

    @app_commands.command(name="nightcore", description="apply nightcore filter")
    async def nightcore(self, interaction: Interaction):
        """Set the filter to a nightcore style."""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        if not player:
            embed = Embed(title="Not Connected", color=discord.Color.blurple())
            await interaction.response.send_message(embed = embed)

        filters: wavelink.Filters = player.filters
        filters.timescale.set(pitch=1.2, speed=1.2, rate=1)
        await player.set_filters(filters)
        embed = Embed(title="Nightcore Filter activated", color=discord.Color.blurple())
        await interaction.response.send_message(embed = embed)

    @app_commands.command(name="toggle",description="pause and resume track")
    async def pause_resume(self, interaction: Interaction):
        """Pause or Resume the Player depending on its current state."""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        if not player:
            embed = Embed(title="Not Connected", color=discord.Color.blurple())
            await interaction.response.send_message(embed = embed)
        
        await player.pause(not player.paused)
        if(player.paused):
            embed = Embed(title="Player paused", color=discord.Color.blurple())
        else:
            embed = Embed(title="Player resumed", color=discord.Color.blurple())
        await interaction.response.send_message(embed = embed)

    @app_commands.command(name="volume", description="set volume of the Player")
    async def volume(self, interaction: Interaction, value: int):
        """Change the volume of the player."""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        if not player:
            embed = Embed(title="Not Connected", color=discord.Color.blurple())
            await interaction.response.send_message(embed = embed)

        await player.set_volume(value)
        embed = Embed(title=f'Volume set to {value}', color=discord.Color.blurple())
        await interaction.response.send_message(embed = embed)

    @app_commands.command(name="leave")
    async def leave(self, interaction: Interaction):
        """Disconnect the Player."""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        if not player:
            embed = Embed(title="Not Connected", color=discord.Color.blurple())
            await interaction.response.send_message(embed = embed)

        await player.disconnect()
        embed = Embed(title="Player Disconnected", color=discord.Color.blurple())
        await interaction.response.send_message(embed = embed)


async def setup(bot):
    await bot.add_cog(Music(bot))
