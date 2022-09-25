import re
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, Embed, SlashOption
import lavasnek_rs as lava

#Filter for Url
url_rx = re.compile(r"https?://(?:www\.)?.+")

#VoiceHandler 
class LavalinkVoiceClient(nextcord.VoiceClient):
    """
    This is the preferred way to handle external voice sending
    This client will be created via a cls in the connect method of the channel
    see the following documentation:
    https://nextcord.readthedocs.io/en/latest/api.html#voiceprotocol
    """

    def __init__(self, client: nextcord.Client, channel: nextcord.abc.Connectable):
        self.client = client
        self.channel = channel
        # ensure there exists a client already
        if hasattr(self.client, "lavalink"):
            self.lavalink = self.client.lavalink
        else:
            self.client.lavalink = lava.Client(client.user.id)
            self.client.lavalink.add_node(
                'localhost', 8000, 'testing', 'eu', 'music-node'
            )
            self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {"t": "VOICE_SERVER_UPDATE", "d": data}
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        # voice_update_handler
        lavalink_data = {"t": "VOICE_STATE_UPDATE", "d": data}
        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool) -> None:
        
        await self.channel.guild.change_voice_state(channel=self.channel)

    async def disconnect(self, *, force: bool) -> None:
        """
        Handles the disconnect.
        Cleans up running player and leaves the voice client.
        """
        player = self.lavalink.player_manager.get(self.channel.guild.id)

        # no need to disconnect if we are not connected
        if not force and not player.is_connected:
            return

        # None means disconnect
        await self.channel.guild.change_voice_state(channel=None)

        # update the channel_id of the player to None
        # this must be done because the on_voice_state_update that
        # would set channel_id to None doesn't get dispatched after the
        # disconnect
        player.channel_id = None
        self.cleanup()


#MusicCog/Bot-Commands
class music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        if not hasattr(
            bot, "lavalink"
        ):  # This ensures the client isn't overwritten during cog reloads.
            self.bot.lavalink = lava.Client(889602797912326176)
            self.bot.lavalink.add_node(
                'localhost', 8000, 'testing', 'eu', 'music-node'
            )  # Host, Port, Password, Region, Name

        lava.add_event_hook(self.track_hook)

    async def track_hook(self, event):
        if isinstance(event, lava.events.QueueEndEvent):
            try:  
            # When this track_hook receives a "QueueEndEvent" from lava
            # it indicates that there are no tracks left in the player's queue.
            # To save on resources, we can tell the bot to disconnect from the voicechannel.
                guild_id = int(event.player.guild_id)
                guild = self.bot.get_guild(guild_id)
                await guild.voice_client.disconnect(force=True)
                await self.bot.lavalink.player_manager.remove(guild_id) #löscht den Player trotz Fehlermeldung 
            except Exception as error:
                print(error)


    @nextcord.slash_command(name="play", description="Play's music")
    async def play(self, interaction: Interaction, *, song: str = SlashOption(description="song link")):
        """Searches and plays a song from a given query."""
        # Get the player for this guild from cache.
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)
        if player == None:
            player = self.bot.lavalink.player_manager.create(interaction.guild.id)
            await interaction.user.voice.channel.connect(cls=LavalinkVoiceClient)
        else:
            player = self.bot.lavalink.player_manager.get(interaction.guild.id)
        # Remove leading and trailing <>. <> may be used to suppress embedding links in nextcord.
        query = song.strip("<>")

        # Check if the user input might be a URL. If it isn't, we can Lavalink do a YouTube search for it instead.
        # SoundCloud searching is possible by prefixing "scsearch:" instead.
        if not url_rx.match(query):
            query = f"ytsearch:{query}"

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        # Results could be None if Lavalink returns an invalid response (non-JSON/non-200 (OK)).
        # ALternatively, resullts['tracks'] could be an empty array if the query yielded no tracks.
        if not results or not results["tracks"]:
            return await interaction.response.send_message("**Nothing found!**")

        embed = nextcord.Embed(color=nextcord.Color.blurple())

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        if results["loadType"] == "PLAYLIST_LOADED":
            tracks = results["tracks"]

            for track in tracks:
                # Add all of the tracks from the playlist to the queue.
                player.add(requester=interaction.user.id, track=track)

            embed.title = "Playlist Enqueued!"
            embed.description = (
                f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks'
            )
        else:
            track = results["tracks"][0]
            embed.title = "Track Enqueued"
            embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'

            # You can attach additional information to audiotracks through kwargs, however this involves
            # constructing the AudioTrack class yourself.
            track = lava.models.AudioTrack(track, interaction.user.id, recommended=True)
            player.add(requester=interaction.user.id, track=track)

        await interaction.response.send_message(embed=embed)
        # We don't want to call .play() if the player is playing as that will effectively skip
        # the current track.
        if not player.is_playing:
            await player.play()


    
    @nextcord.slash_command(name="leave", description="leaves channel an stop playing", )
    async def leave(self, interaction: Interaction):
        """Disconnects the player from the voice channel and clears its queue."""
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await interaction.response.send_message("Not connected.")

        if not interaction.user.voice or (
            player.is_connected
            and interaction.user.voice.channel.id != int(player.channel_id)
        ):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await interaction.response.send_message("**You're not in my voicechannel!**")

        # Clear the queue to ensure old tracks don't start playing
        # when someone else queues something.
        player.queue.clear()
        # Stop the current track so Lavalink consumes less resources.
        await player.stop()
        try:# Disconnect from the voice channel.
            guild_id =interaction.guild.id
            guild = self.bot.get_guild(guild_id)
            await guild.voice_client.disconnect(force=True)
            await self.bot.lavalink.player_manager.remove(guild_id)
        except Exception as error:
            print(error)     
        await interaction.response.send_message("** *⃣ | Disconnected.**")


    @nextcord.slash_command(name="skip", description="skip queued song")
    async def skip(self, interaction: Interaction):
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)
        if int(player.channel_id) == interaction.user.voice.channel.id:
               
            await player.skip()
            if player.current == None:
                await interaction.response.send_message("**No queue remaining I left your channel**")
            else:     
                embed=Embed(title="Now Playing:", url=player.current.uri, description=player.current.title, color=nextcord.Color.blurple())
                await interaction.response.send_message(embed=embed)           
        else:
            await interaction.response.send_message('**You need to be in my voicechannel.**')

    
    @nextcord.slash_command(name='pause', description="pause the curent player")
    async def pause(self, interaction: Interaction):
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)
        if int(player.channel_id) == interaction.user.voice.channel.id:
            await player.set_pause(True)
            await interaction.response.send_message('**Player paused**')
        else:
            await interaction.response.send_message('**You need to be in my voicechannel.**')

    @nextcord.slash_command(name='resume', description="resumes paused player")
    async def resume(self, interaction: Interaction):
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)
        if int(player.channel_id) == interaction.user.voice.channel.id:
            await player.set_pause(False)
            await interaction.response.send_message('**Player resumed**')
        else:
            await interaction.response.send_message('**You need to be in my voicechannel.**')

    @nextcord.slash_command(name="loop", description="loops curent song")        
    async def loop(self, interaction: Interaction):
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)
        if int(player.channel_id) == interaction.user.voice.channel.id:
            if player.repeat == False:
                player.set_repeat(True)
                await interaction.response.send_message('**Song is now looping**')
            elif player.repeat == True:
                player.set_repeat(False)
                await interaction.response.send_message('**Song stopped looping**')
        else:
            await interaction.response.send_message('**You need to be in my voicechannel.**')

    @nextcord.slash_command(name="volume", description="changes volume of the player to a number between 0-1000")
    async def volume(self, interaction: Interaction, volume: int = SlashOption(description="volume number")):
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)
        if int(player.channel_id) == interaction.user.voice.channel.id:
            if volume > 1000:
                await interaction.response.send_message("**Choose an number between 0 and 1000**")
            else:
                await player.set_volume(volume)
                await interaction.response.send_message(f'volume changed to {volume}')
        else:
            await interaction.response.send_message('**You need to be in my voicechannel.**')

def setup(bot):
    bot.add_cog(music(bot))