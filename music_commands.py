"""Music-related commands for the Discord Music Bot."""

import asyncio
import discord
from discord.ext import commands
import logging
from typing import TYPE_CHECKING

from ytdl_source import YTDLSource
from utils import create_embed, create_song_embed, create_queue_embed, create_search_results_embed
from music_controls import create_music_controls, create_queue_controls, create_volume_controls
from youtube_helper import create_youtube_blocked_embed, get_troubleshooting_tips

if TYPE_CHECKING:
    from music_bot import MusicBot

logger = logging.getLogger(__name__)


class MusicCommands(commands.Cog):
    """Music playback commands."""
    
    def __init__(self, bot: 'MusicBot'):
        self.bot = bot
    
    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        """Check if user is in voice channel before most commands."""
        if ctx.command.name not in ['help', 'search', 'queue']:
            if not ctx.author.voice:
                await ctx.send("❌ You need to be in a voice channel!")
                raise commands.CheckFailure("User not in voice channel")
    
    @commands.command(name='join', aliases=['connect'])
    async def join_voice(self, ctx: commands.Context) -> None:
        """Join the voice channel."""
        channel = ctx.author.voice.channel
        
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
            
        await ctx.send(f"🎵 Connected to **{channel.name}**!")

    @commands.command(name='leave', aliases=['disconnect'])
    async def leave_voice(self, ctx: commands.Context) -> None:
        """Leave the voice channel."""
        if ctx.voice_client:
            queue = self.bot.get_queue(ctx.guild.id)
            queue.clear()
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Disconnected from voice channel!")
        else:
            await ctx.send("❌ Bot is not in a voice channel!")

    @commands.command(name='play', aliases=['p'])
    async def play_music(self, ctx: commands.Context, *, query: str) -> None:
        """Play music from YouTube URL or search query."""
        # Join voice channel if not already connected
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()
        
        queue = self.bot.get_queue(ctx.guild.id)
        
        async with ctx.typing():
            try:
                # Check if it's a URL or search query
                if query.startswith(('http://', 'https://')):
                    # Direct URL
                    player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
                else:
                    # Search query
                    search_result = await YTDLSource.search_youtube(query, loop=self.bot.loop)
                    if not search_result:
                        await ctx.send("❌ No results found!")
                        return
                    
                    player = await YTDLSource.from_url(search_result['webpage_url'], loop=self.bot.loop, stream=True)
                
                # Add to queue
                queue.add(player)
                
                # Create embed for song info
                embed = create_song_embed(player, "🎵 Added to Queue")
                embed.add_field(name="Position in Queue", value=str(queue.size), inline=True)
                    
                await ctx.send(embed=embed)
                
                # Start playing if nothing is currently playing
                if not ctx.voice_client.is_playing():
                    await self.bot.play_next(ctx)
                    
            except Exception as e:
                logger.error(f"Error playing music: {e}")
                
                # Check if it's a YouTube bot detection error
                if "Sign in to confirm you're not a bot" in str(e) or "bot" in str(e).lower():
                    embed = create_youtube_blocked_embed()
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"❌ Error playing music: {str(e)}")

    @commands.command(name='pause')
    async def pause_music(self, ctx: commands.Context) -> None:
        """Pause the current song."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Music paused!")
        else:
            await ctx.send("❌ Nothing is playing!")

    @commands.command(name='resume')
    async def resume_music(self, ctx: commands.Context) -> None:
        """Resume the paused song."""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Music resumed!")
        else:
            await ctx.send("❌ Music is not paused!")

    @commands.command(name='stop')
    async def stop_music(self, ctx: commands.Context) -> None:
        """Stop the music and clear queue."""
        if ctx.voice_client:
            queue = self.bot.get_queue(ctx.guild.id)
            queue.clear()
            ctx.voice_client.stop()
            await ctx.send("⏹️ Music stopped and queue cleared!")
        else:
            await ctx.send("❌ Nothing is playing!")

    @commands.command(name='skip', aliases=['next'])
    async def skip_music(self, ctx: commands.Context) -> None:
        """Skip the current song."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()  # This will trigger the after callback to play next
            await ctx.send("⏭️ Song skipped!")
        else:
            await ctx.send("❌ Nothing is playing!")

    @commands.command(name='queue', aliases=['q'])
    async def show_queue(self, ctx: commands.Context) -> None:
        """Show the current music queue with interactive controls."""
        queue = self.bot.get_queue(ctx.guild.id)
        
        embed = create_queue_embed(queue)
        view = create_queue_controls(self.bot, ctx.guild.id)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @commands.command(name='clear')
    async def clear_queue(self, ctx: commands.Context) -> None:
        """Clear the music queue."""
        queue = self.bot.get_queue(ctx.guild.id)
        queue.clear()
        await ctx.send("🗑️ Queue cleared!")

    @commands.command(name='shuffle')
    async def shuffle_queue(self, ctx: commands.Context) -> None:
        """Shuffle the music queue."""
        queue = self.bot.get_queue(ctx.guild.id)
        if queue.queue:
            queue.shuffle()
            await ctx.send("🔀 Queue shuffled!")
        else:
            await ctx.send("❌ Queue is empty!")

    @commands.command(name='volume', aliases=['vol'])
    async def change_volume(self, ctx: commands.Context, volume: int) -> None:
        """Change the playback volume (0-100)."""
        if not ctx.voice_client:
            await ctx.send("❌ Bot is not in a voice channel!")
            return
        
        if not 0 <= volume <= 100:
            await ctx.send("❌ Volume must be between 0 and 100!")
            return
        
        # Get the current playing source from the queue
        queue = self.bot.get_queue(ctx.guild.id)
        if queue.current:
            if queue.current.supports_volume:
                queue.current.set_volume(volume / 100)
                await ctx.send(f"🔊 Volume set to {volume}%!")
            else:
                await ctx.send("⚠️ Volume control not supported for current audio format (Opus)")
        else:
            await ctx.send("❌ Nothing is playing!")

    @commands.command(name='loop')
    async def toggle_loop(self, ctx: commands.Context) -> None:
        """Toggle loop mode for current song."""
        queue = self.bot.get_queue(ctx.guild.id)
        queue.loop_mode = not queue.loop_mode
        
        status = "enabled" if queue.loop_mode else "disabled"
        emoji = "🔁" if queue.loop_mode else "▶️"
        await ctx.send(f"{emoji} Loop mode {status}!")

    @commands.command(name='nowplaying', aliases=['np'])
    async def now_playing(self, ctx: commands.Context) -> None:
        """Show currently playing song."""
        queue = self.bot.get_queue(ctx.guild.id)
        
        if not queue.current:
            await ctx.send("❌ Nothing is playing!")
            return
        
        embed = create_song_embed(queue.current, "🎵 Now Playing", discord.Color.blue())
        embed.add_field(name="Loop", value="🔁 Enabled" if queue.loop_mode else "▶️ Disabled", inline=True)
        
        # Add music controls to the now playing message
        view = create_music_controls(self.bot, ctx.guild.id)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @commands.command(name='controls')
    async def show_controls(self, ctx: commands.Context) -> None:
        """Show music control panel."""
        embed = create_embed(
            "🎛️ Music Controls",
            "Use the buttons below to control music playback!"
        )
        
        queue = self.bot.get_queue(ctx.guild.id)
        if queue.current:
            embed.add_field(
                name="🎵 Currently Playing",
                value=queue.current.title,
                inline=False
            )
        
        view = create_music_controls(self.bot, ctx.guild.id)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @commands.command(name='volume_panel', aliases=['vol_panel'])
    async def volume_panel(self, ctx: commands.Context) -> None:
        """Show volume control panel."""
        queue = self.bot.get_queue(ctx.guild.id)
        
        embed = create_embed(
            "🔊 Volume Controls",
            "Use the buttons below to control volume!"
        )
        
        if queue.current:
            if queue.current.supports_volume:
                current_vol = int(queue.current.volume * 100)
                embed.add_field(
                    name="Current Volume",
                    value=f"{current_vol}%",
                    inline=True
                )
            else:
                embed.add_field(
                    name="Volume Control",
                    value="Not supported (Opus format)",
                    inline=True
                )
        
        view = create_volume_controls(self.bot, ctx.guild.id)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @commands.command(name='search')
    async def search_youtube(self, ctx: commands.Context, *, query: str) -> None:
        """Search YouTube and show results."""
        async with ctx.typing():
            try:
                results = await YTDLSource.search_youtube_multiple(query, loop=self.bot.loop)
                
                if not results:
                    await ctx.send("❌ No results found!")
                    return
                
                embed = create_search_results_embed(query, results)
                await ctx.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error searching YouTube: {e}")
                await ctx.send(f"❌ Error searching: {str(e)}")

    @commands.command(name='help')
    async def help_command(self, ctx: commands.Context) -> None:
        """Show help message with all commands."""
        embed = create_embed(
            "🎵 Music Bot Commands",
            "Here are all available commands:"
        )
        
        commands_list = [
            ("!play <url/query>", "Play music from YouTube URL or search"),
            ("!pause", "Pause the current song"),
            ("!resume", "Resume the paused song"),
            ("!stop", "Stop music and clear queue"),
            ("!skip", "Skip the current song"),
            ("!queue", "Show the current queue with controls"),
            ("!clear", "Clear the music queue"),
            ("!shuffle", "Shuffle the queue"),
            ("!volume <0-100>", "Change playback volume"),
            ("!loop", "Toggle loop mode"),
            ("!nowplaying", "Show currently playing song with controls"),
            ("!controls", "Show music control panel"),
            ("!volume_panel", "Show volume control panel"),
            ("!search <query>", "Search YouTube for songs"),
            ("!join", "Join your voice channel"),
            ("!leave", "Leave the voice channel"),
        ]
        
        for command, description in commands_list:
            embed.add_field(name=command, value=description, inline=False)
        
        embed.set_footer(text="Supports YouTube videos and shorts!")
        await ctx.send(embed=embed)
