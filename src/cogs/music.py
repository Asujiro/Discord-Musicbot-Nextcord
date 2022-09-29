"""
This example cog demonstrates basic usage of Lavalink.py, using the DefaultPlayer.
As this example primarily showcases usage in conjunction with nextcord.py, you will need to make
modifications as necessary for use with another nextcord library.
Usage of this cog requires Python 3.6 or higher due to the use of f-strings.
Compatibility with Python 3.5 should be possible if f-strings are removed.
"""
from code import interact
import re
from discord import slash_command

import nextcord
import lavalink
from nextcord.ext import commands
from lavalink.filters import LowPass
from nextcord import Interaction, Embed, SlashOption

url_rx = re.compile(r'https?://(?:www\.)?.+')
test_ids = [390194259405438989]


class LavalinkVoiceClient(nextcord.VoiceClient):
    """
    This is the preferred way to handle external voice sending
    This client will be created via a cls in the connect method of the channel
    see the following documentation:
    https://nextcordpy.readthedocs.io/en/latest/api.html#voiceprotocol
    """

    def __init__(self, client: nextcord.Client, channel: nextcord.abc.Connectable):
        self.client = client
        self.channel = channel
        # ensure a client already exists
        if hasattr(self.client, 'lavalink'):
            self.lavalink = self.client.lavalink
        else:
            self.client.lavalink = lavalink.Client(902902788009377812)
            self.client.lavalink.add_node(
                'localhost',
                8000,
                'testing',
                'eu',
                'default-node'
            )
            self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
            't': 'VOICE_SERVER_UPDATE',
            'd': data
        }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
            't': 'VOICE_STATE_UPDATE',
            'd': data
        }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False) -> None:
        """
        Connect the bot to the voice channel and create a player_manager
        if it doesn't exist yet.
        """
        # ensure there is a player_manager when creating a new voice_client
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

    async def disconnect(self, *, force: bool = False) -> None:
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
        # this must be done because the on_voice_state_update that would set channel_id
        # to None doesn't get dispatched after the disconnect
        player.channel_id = None
        self.cleanup()


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            bot.lavalink = lavalink.Client(902902788009377812)
            bot.lavalink.add_node('localhost', 8000, 'testing', 'eu', 'default-node')  # Host, Port, Password, Region, Name

        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.lavalink._event_hooks.clear()

  
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(error.original)
            # The above handles errors thrown in this cog and shows them to the user.
            # This shouldn't be a problem as the only errors thrown in this cog are from `ensure_voice`
            # which contain a reason string, such as "Join a voicechannel" etc. You can modify the above
            # if you want to do things differently.

    

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            # When this track_hook receives a "QueueEndEvent" from lavalink.py
            # it indicates that there are no tracks left in the player's queue.
            # To save on resources, we can tell the bot to disconnect from the voicechannel.
            guild_id = event.player.guild_id
            guild = self.bot.get_guild(guild_id)
            await guild.voice_client.disconnect(force=True)

    @nextcord.slash_command(name="play", description="Play's music", guild_ids=test_ids)
    async def play(self, interaction: Interaction, *, song: str = SlashOption(description="song link")):
        """ Searches and plays a song from a given query. """
        query = song

        
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)
        
        if not interaction.guild.voice_client:
            # We can't connect, if we're not connected.
            return await interaction.response.send_message('Not connected.')

        if not interaction.user.voice or (player.is_connected and interaction.user.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not connect the bot.
            return await interaction.response.send_message('You\'re not in my voicechannel!')
        
        # Get the player for this guild from cache. When there is no player creat one. 
        if player == None:
            player = self.bot.lavalink.player_manager.create(interaction.guild.id)
            await interaction.user.voice.channel.connect(cls=LavalinkVoiceClient)
        else:
            player = self.bot.lavalink.player_manager.get(interaction.guild.id)

        # Remove leading and trailing <>. <> may be used to suppress embedding links in nextcord.
        query = query.strip('<>')

        # Check if the user input might be a URL. If it isn't, we can Lavalink do a YouTube search for it instead.
        # SoundCloud searching is possible by prefixing "scsearch:" instead.
        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        # Results could be None if Lavalink returns an invalid response (non-JSON/non-200 (OK)).
        # ALternatively, resullts.tracks could be an empty array if the query yielded no tracks.
        if not results or not results.tracks:
            return await interaction.response.send_message("**Nothing found!**")

        embed = nextcord.Embed(color=nextcord.Color.blurple())

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        if results.load_type == 'PLAYLIST_LOADED':
            tracks = results.tracks

            for track in tracks:
                # Add all of the tracks from the playlist to the queue.
                player.add(requester=interaction.user.id, track=track)

            embed.title = 'Playlist Enqueued!'
            embed.description = f'{results.playlist_info.name} - {len(tracks)} tracks'
        else:
            track = results.tracks[0]
            embed.title = 'Track Enqueued'
            embed.description = f'[{track.title}]({track.uri})'

            player.add(requester=interaction.user.id, track=track)

        await interaction.response.send_message(embed=embed)

        # We don't want to call .play() if the player is playing as that will effectively skip
        # the current track.
        if not player.is_playing:
            await player.play()

    @nextcord.slash_command(name="leave", description="leaves channel an stop playing", guild_ids=test_ids )
    async def leave(self, interaction: Interaction):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.bot.lavalink.player_manager.get(interaction.guild_id)
        
        
        if not interaction.guild.voice_client:
            # We can't disconnect, if we're not connected.
            return await interaction.response.send_message('Not connected.')

        if not interaction.user.voice or (player.is_connected and interaction.user.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await interaction.response.send_message('You\'re not in my voicechannel!')

        # Clear the queue to ensure old tracks don't start playing
        # when someone else queues something.
        player.queue.clear()
        # Stop the current track so Lavalink consumes less resources.
        await player.stop()

        # Disconnect from the voice channel and delete Player.
        guild_id = interaction.guild.id
        guild = self.bot.get_guild(guild_id)
        await guild.voice_client.disconnect(force=True)
        self.bot.lavalink.player_manager.remove(guild_id)

        await interaction.response.send_message('*⃣ | Disconnected.')

    
    @nextcord.slash_command(name="skip", description="skip current track")
    async def skip(self, interaction: Interaction):
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)
        if not interaction.guild.voice_client:
            # We cant pause, if we're not connected.
            return await interaction.response.send_message('Not connected.')

        if not interaction.user.voice or (player.is_connected and interaction.user.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not pause the bot.
            return await interaction.response.send_message('You\'re not in my voicechannel!')
               
        await player.skip()
        if player.current == None:
            await interaction.response.send_message("**No queue remaining I left your channel**")
        else:     
            embed=Embed(title="Now Playing:", url=player.current.uri, description=player.current.title, color=nextcord.Color.blurple())
            await interaction.response.send_message(embed=embed)           
    
    #pause the player
    @nextcord.slash_command(name='pause', description="pause the current track")
    async def pause(self, interaction: Interaction):
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)

        if not interaction.guild.voice_client:
            # We cant pause, if we're not connected.
            return await interaction.response.send_message('Not connected.')

        if not interaction.user.voice or (player.is_connected and interaction.user.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not pause the bot.
            return await interaction.response.send_message('You\'re not in my voicechannel!')

        await player.set_pause(True)
        await interaction.response.send_message('**Player paused**')
    
    #resume the player
    @nextcord.slash_command(name='resume', description="resumes paused track")
    async def resume(self, interaction: Interaction):
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)

        if not interaction.guild.voice_client:
            # We cant pause, if we're not connected.
            return await interaction.response.send_message('Not connected.')

        if not interaction.user.voice or (player.is_connected and interaction.user.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not pause the bot.
            return await interaction.response.send_message('You\'re not in my voicechannel!')

        await player.set_pause(False)
        await interaction.response.send_message('**Player paused**')

    
    @nextcord.slash_command(name="loop", description="loops current song")        
    async def loop(self, interaction: Interaction):
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)

        if not interaction.guild.voice_client:
            # We cant pause, if we're not connected.
            return await interaction.response.send_message('Not connected.')

        if not interaction.user.voice or (player.is_connected and interaction.user.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not pause the bot.
            return await interaction.response.send_message('You\'re not in my voicechannel!')
        if player.repeat == False:
            player.set_repeat(True)
            return await interaction.response.send_message('**Song is now looping**')
        if player.repeat == True:
            player.set_repeat(False)
            return await interaction.response.send_message('**Song stopped looping**')

    @nextcord.slash_command(name="volume", description="changes volume of the player to a number between 0-1000")
    async def volume(self, interaction: Interaction, volume: int = SlashOption(description="volume number")):
        player = self.bot.lavalink.player_manager.get(interaction.guild.id)

        if not interaction.guild.voice_client:
            # We cant pause, if we're not connected.
            return await interaction.response.send_message('Not connected.')

        if not interaction.user.voice or (player.is_connected and interaction.user.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not pause the bot.
            return await interaction.response.send_message('You\'re not in my voicechannel!')
        if volume > 1000:
            await interaction.response.send_message("**Choose an number between 0 and 1000**")
        else:
            await player.set_volume(volume)
            await interaction.response.send_message(f'volume changed to {volume}')

    @nextcord.slash_command(name="volume", description="Sets the strength of the low pass filter.")
    async def lowpass(self, interaction: Interaction, strength: float = SlashOption(description="number between 0 and 100")):
        """ Sets the strength of the low pass filter. """
        # Get the player for this guild from cache.
        player = self.bot.lavalink.player_manager.get(interaction.guild_id)
        if not interaction.guild.voice_client:
            # We cant change lowpass filter, if we're not connected.
            return await interaction.response.send_message('Not connected.')

        if not interaction.user.voice or (player.is_connected and interaction.user.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not change the lowpass filter.
            return await interaction.response.send_message('You\'re not in my voicechannel!')
        # This enforces that strength should be a minimum of 0.
        # There's no upper limit on this filter.
        strength = max(0.0, strength)

        # Even though there's no upper limit, we will enforce one anyway to prevent
        # extreme values from being entered. This will enforce a maximum of 100.
        strength = min(100, strength)

        embed = nextcord.Embed(color=nextcord.Color.blurple(), title='Low Pass Filter')

        # A strength of 0 effectively means this filter won't function, so we can disable it.
        if strength == 0.0:
            player.remove_filter('lowpass')
            embed.description = 'Disabled **Low Pass Filter**'
            return await interaction.response.send_message(embed=embed)

        # Lets create our filter.
        low_pass = LowPass()
        low_pass.update(smoothing=strength)  # Set the filter strength to the user's desired level.

        # This applies our filter. If the filter is already enabled on the player, then this will
        # just overwrite the filter with the new values.
        await player.set_filter(low_pass)

        embed.description = f'Set **Low Pass Filter** strength to {strength}.'
        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(Music(bot))