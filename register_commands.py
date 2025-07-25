"""
Command registration system for Discord Music Bot.

This module handles the registration of both slash commands and traditional prefix commands,
providing a hybrid approach that allows users to interact with the bot in multiple ways.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any

import discord
from discord import app_commands
from discord.ext import commands

from config import BOT_PREFIX
from ytdl_source import YTDLSource
from utils import create_embed, create_song_embed, create_queue_embed, create_search_results_embed
from music_controls import create_music_controls, create_queue_controls, create_volume_controls

logger = logging.getLogger(__name__)


class MusicSlashCommands(commands.Cog):
    """Slash command implementations for the music bot."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def cog_load(self) -> None:
        """Called when the cog is loaded."""
        logger.info("Music slash commands cog loaded")
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if user is in voice channel for most commands."""
        if interaction.command and interaction.command.name not in ['help', 'search', 'queue']:
            if not interaction.user.voice:
                await interaction.response.send_message("❌ You need to be in a voice channel!", ephemeral=True)
                return False
        return True
    
    @app_commands.command(name="join", description="Join your voice channel")
    async def slash_join(self, interaction: discord.Interaction) -> None:
        """Join the voice channel."""
        if not interaction.user.voice:
            await interaction.response.send_message("❌ You need to be in a voice channel!", ephemeral=True)
            return
            
        channel = interaction.user.voice.channel
        
        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
            
        await interaction.response.send_message(f"🎵 Connected to **{channel.name}**!")

    @app_commands.command(name="leave", description="Leave the voice channel")
    async def slash_leave(self, interaction: discord.Interaction) -> None:
        """Leave the voice channel."""
        if interaction.guild.voice_client:
            queue = self.bot.get_queue(interaction.guild.id)
            queue.clear()
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("👋 Disconnected from voice channel!")
        else:
            await interaction.response.send_message("❌ Bot is not in a voice channel!", ephemeral=True)

    @app_commands.command(name="play", description="Play music from YouTube URL or search query")
    @app_commands.describe(query="YouTube URL or search query")
    async def slash_play(self, interaction: discord.Interaction, query: str) -> None:
        """Play music from YouTube URL or search query."""
        await interaction.response.defer()
        
        # Join voice channel if not already connected
        if not interaction.guild.voice_client:
            if not interaction.user.voice:
                await interaction.followup.send("❌ You need to be in a voice channel!")
                return
            await interaction.user.voice.channel.connect()
        
        queue = self.bot.get_queue(interaction.guild.id)
        
        try:
            # Check if it's a URL or search query
            if query.startswith(('http://', 'https://')):
                # Direct URL
                player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
            else:
                # Search query
                search_result = await YTDLSource.search_youtube(query, loop=self.bot.loop)
                if not search_result:
                    await interaction.followup.send("❌ No results found!")
                    return
                
                player = await YTDLSource.from_url(search_result['webpage_url'], loop=self.bot.loop, stream=True)
            
            # Add to queue
            queue.add(player)
            
            # Create embed for song info
            embed = create_song_embed(player, "🎵 Added to Queue")
            embed.add_field(name="Position in Queue", value=str(queue.size), inline=True)
                
            await interaction.followup.send(embed=embed)
            
            # Start playing if nothing is currently playing
            if not interaction.guild.voice_client.is_playing():
                await self.bot.play_next_interaction(interaction)
                
        except Exception as e:
            logger.error(f"Error playing music: {e}")
            await interaction.followup.send(f"❌ Error playing music: {str(e)}")

    @app_commands.command(name="pause", description="Pause the current song")
    async def slash_pause(self, interaction: discord.Interaction) -> None:
        """Pause the current song."""
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            await interaction.response.send_message("⏸️ Music paused!")
        else:
            await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)

    @app_commands.command(name="resume", description="Resume the paused song")
    async def slash_resume(self, interaction: discord.Interaction) -> None:
        """Resume the paused song."""
        if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            await interaction.response.send_message("▶️ Music resumed!")
        else:
            await interaction.response.send_message("❌ Music is not paused!", ephemeral=True)

    @app_commands.command(name="stop", description="Stop the music and clear queue")
    async def slash_stop(self, interaction: discord.Interaction) -> None:
        """Stop the music and clear queue."""
        if interaction.guild.voice_client:
            queue = self.bot.get_queue(interaction.guild.id)
            queue.clear()
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("⏹️ Music stopped and queue cleared!")
        else:
            await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)

    @app_commands.command(name="skip", description="Skip the current song")
    async def slash_skip(self, interaction: discord.Interaction) -> None:
        """Skip the current song."""
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()  # This will trigger the after callback to play next
            await interaction.response.send_message("⏭️ Song skipped!")
        else:
            await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)

    @app_commands.command(name="queue", description="Show the current music queue")
    async def slash_queue(self, interaction: discord.Interaction) -> None:
        """Show the current music queue with interactive controls."""
        queue = self.bot.get_queue(interaction.guild.id)
        
        embed = create_queue_embed(queue)
        view = create_queue_controls(self.bot, interaction.guild.id)
        await interaction.response.send_message(embed=embed, view=view)
        
        # Get the message object for the view
        message = await interaction.original_response()
        view.message = message

    @app_commands.command(name="clear", description="Clear the music queue")
    async def slash_clear(self, interaction: discord.Interaction) -> None:
        """Clear the music queue."""
        queue = self.bot.get_queue(interaction.guild.id)
        queue.clear()
        await interaction.response.send_message("🗑️ Queue cleared!")

    @app_commands.command(name="shuffle", description="Shuffle the music queue")
    async def slash_shuffle(self, interaction: discord.Interaction) -> None:
        """Shuffle the music queue."""
        queue = self.bot.get_queue(interaction.guild.id)
        if queue.queue:
            queue.shuffle()
            await interaction.response.send_message("🔀 Queue shuffled!")
        else:
            await interaction.response.send_message("❌ Queue is empty!", ephemeral=True)

    @app_commands.command(name="volume", description="Change the playback volume")
    @app_commands.describe(volume="Volume level (0-100)")
    @app_commands.rename(volume="level")
    async def slash_volume(self, interaction: discord.Interaction, volume: app_commands.Range[int, 0, 100]) -> None:
        """Change the playback volume (0-100)."""
        if not interaction.guild.voice_client:
            await interaction.response.send_message("❌ Bot is not in a voice channel!", ephemeral=True)
            return
        
        # Get the current playing source from the queue
        queue = self.bot.get_queue(interaction.guild.id)
        if queue.current:
            if queue.current.supports_volume:
                queue.current.set_volume(volume / 100)
                await interaction.response.send_message(f"🔊 Volume set to {volume}%!")
            else:
                await interaction.response.send_message("⚠️ Volume control not supported for current audio format (Opus)", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)

    @app_commands.command(name="loop", description="Toggle loop mode for current song")
    async def slash_loop(self, interaction: discord.Interaction) -> None:
        """Toggle loop mode for current song."""
        queue = self.bot.get_queue(interaction.guild.id)
        queue.loop_mode = not queue.loop_mode
        
        status = "enabled" if queue.loop_mode else "disabled"
        emoji = "🔁" if queue.loop_mode else "▶️"
        await interaction.response.send_message(f"{emoji} Loop mode {status}!")

    @app_commands.command(name="nowplaying", description="Show currently playing song")
    async def slash_nowplaying(self, interaction: discord.Interaction) -> None:
        """Show currently playing song with controls."""
        queue = self.bot.get_queue(interaction.guild.id)
        
        if not queue.current:
            await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)
            return
        
        embed = create_song_embed(queue.current, "🎵 Now Playing", discord.Color.blue())
        embed.add_field(name="Loop", value="🔁 Enabled" if queue.loop_mode else "▶️ Disabled", inline=True)
        
        view = create_music_controls(self.bot, interaction.guild.id)
        await interaction.response.send_message(embed=embed, view=view)
        
        # Get the message object for the view
        message = await interaction.original_response()
        view.message = message

    @app_commands.command(name="controls", description="Show music control panel")
    async def slash_controls(self, interaction: discord.Interaction) -> None:
        """Show music control panel."""
        embed = create_embed(
            "🎛️ Music Controls",
            "Use the buttons below to control music playback!"
        )
        
        queue = self.bot.get_queue(interaction.guild.id)
        if queue.current:
            embed.add_field(
                name="🎵 Currently Playing",
                value=queue.current.title,
                inline=False
            )
        
        view = create_music_controls(self.bot, interaction.guild.id)
        await interaction.response.send_message(embed=embed, view=view)
        
        # Get the message object for the view
        message = await interaction.original_response()
        view.message = message

    @app_commands.command(name="volume_panel", description="Show volume control panel")
    async def slash_volume_panel(self, interaction: discord.Interaction) -> None:
        """Show volume control panel."""
        queue = self.bot.get_queue(interaction.guild.id)
        
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
        
        view = create_volume_controls(self.bot, interaction.guild.id)
        await interaction.response.send_message(embed=embed, view=view)
        
        # Get the message object for the view
        message = await interaction.original_response()
        view.message = message

    @app_commands.command(name="search", description="Search YouTube and show results")
    @app_commands.describe(query="Search query")
    async def slash_search(self, interaction: discord.Interaction, query: str) -> None:
        """Search YouTube and show results."""
        await interaction.response.defer()
        
        try:
            results = await YTDLSource.search_youtube_multiple(query, loop=self.bot.loop)
            
            if not results:
                await interaction.followup.send("❌ No results found!")
                return
            
            embed = create_search_results_embed(query, results)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error searching YouTube: {e}")
            await interaction.followup.send(f"❌ Error searching: {str(e)}")

    @app_commands.command(name="help", description="Show all available commands")
    async def slash_help(self, interaction: discord.Interaction) -> None:
        """Show help message with all commands."""
        embed = create_embed(
            "🎵 Music Bot Commands",
            "Here are all available commands:"
        )
        
        # Add information about both slash and prefix commands
        embed.add_field(
            name="How to use commands",
            value=f"• **Slash commands**: Type `/` and select a command\n• **Prefix commands**: Type `{BOT_PREFIX}command`",
            inline=False
        )
        
        commands_list = [
            ("play <url/query>", "Play music from YouTube URL or search"),
            ("pause", "Pause the current song"),
            ("resume", "Resume the paused song"),
            ("stop", "Stop music and clear queue"),
            ("skip", "Skip the current song"),
            ("queue", "Show the current queue with controls"),
            ("clear", "Clear the music queue"),
            ("shuffle", "Shuffle the queue"),
            ("volume <0-100>", "Change playback volume"),
            ("loop", "Toggle loop mode"),
            ("nowplaying", "Show currently playing song with controls"),
            ("controls", "Show music control panel"),
            ("volume_panel", "Show volume control panel"),
            ("search <query>", "Search YouTube for songs"),
            ("join", "Join your voice channel"),
            ("leave", "Leave the voice channel"),
        ]
        
        command_text = "\n".join([f"**{cmd}** - {desc}" for cmd, desc in commands_list])
        embed.add_field(name="Available Commands", value=command_text, inline=False)
        
        embed.set_footer(text="Supports YouTube videos and shorts!")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class CommandRegistrar:
    """Handles registration and synchronization of Discord commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.synced_guilds: set = set()
    
    async def register_all_commands(self) -> None:
        """Register all commands (slash and prefix) with Discord."""
        try:
            # Add the slash commands cog
            await self.bot.add_cog(MusicSlashCommands(self.bot))
            logger.info("Added slash commands cog")
            
            # Sync commands globally
            await self.sync_commands()
            
        except Exception as e:
            logger.error(f"Error registering commands: {e}")
    
    async def sync_commands(self, guild: Optional[discord.Guild] = None) -> List[app_commands.AppCommand]:
        """
        Sync slash commands with Discord.
        
        Args:
            guild: Optional guild to sync to. If None, syncs globally.
            
        Returns:
            List of synced commands.
        """
        try:
            if guild:
                # Guild-specific sync (faster for testing)
                synced = await self.bot.tree.sync(guild=guild)
                self.synced_guilds.add(guild.id)
                logger.info(f"Synced {len(synced)} commands to guild {guild.name}")
            else:
                # Global sync (takes up to 1 hour to propagate)
                synced = await self.bot.tree.sync()
                logger.info(f"Synced {len(synced)} commands globally")
            
            return synced
            
        except Exception as e:
            logger.error(f"Error syncing commands: {e}")
            return []
    
    async def sync_commands_to_guild(self, guild_id: int) -> bool:
        """
        Sync commands to a specific guild for faster testing.
        
        Args:
            guild_id: The guild ID to sync to.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                logger.error(f"Guild {guild_id} not found")
                return False
            
            await self.sync_commands(guild)
            return True
            
        except Exception as e:
            logger.error(f"Error syncing to guild {guild_id}: {e}")
            return False
    
    async def clear_commands(self, guild: Optional[discord.Guild] = None) -> None:
        """
        Clear all slash commands.
        
        Args:
            guild: Optional guild to clear from. If None, clears globally.
        """
        try:
            self.bot.tree.clear_commands(guild=guild)
            await self.bot.tree.sync(guild=guild)
            
            location = f"guild {guild.name}" if guild else "globally"
            logger.info(f"Cleared all commands {location}")
            
        except Exception as e:
            logger.error(f"Error clearing commands: {e}")
    
    def get_command_stats(self) -> Dict[str, Any]:
        """Get statistics about registered commands."""
        slash_commands = len(self.bot.tree.get_commands())
        prefix_commands = len([cmd for cmd in self.bot.commands if not isinstance(cmd, commands.HybridCommand)])
        hybrid_commands = len([cmd for cmd in self.bot.commands if isinstance(cmd, commands.HybridCommand)])
        
        return {
            "slash_commands": slash_commands,
            "prefix_commands": prefix_commands,
            "hybrid_commands": hybrid_commands,
            "total_commands": slash_commands + prefix_commands + hybrid_commands,
            "synced_guilds": len(self.synced_guilds)
        }
    
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Called when the bot joins a new guild."""
        logger.info(f"Joined guild: {guild.name} ({guild.id})")
        
        # Optionally sync commands to new guild for immediate availability
        # Note: Global sync takes up to 1 hour, guild sync is immediate
        if guild.id not in self.synced_guilds:
            await self.sync_commands_to_guild(guild.id)


# Command registration functions for integration with music_bot.py
async def setup_commands(bot: commands.Bot) -> CommandRegistrar:
    """
    Set up command registration for the music bot.
    
    Args:
        bot: The bot instance.
        
    Returns:
        CommandRegistrar instance.
    """
    registrar = CommandRegistrar(bot)
    await registrar.register_all_commands()
    return registrar


async def sync_commands_for_testing(bot: commands.Bot, guild_id: int) -> bool:
    """
    Quickly sync commands to a specific guild for testing.
    
    Args:
        bot: The bot instance.
        guild_id: The guild ID to sync to.
        
    Returns:
        True if successful, False otherwise.
    """
    registrar = CommandRegistrar(bot)
    return await registrar.sync_commands_to_guild(guild_id)


# Error handler for slash commands
@app_commands.guild_only()
class SlashCommandErrorHandler:
    """Handles errors for slash commands."""
    
    @staticmethod
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        """Handle slash command errors."""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"⏱️ Command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
                ephemeral=True
            )
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command!",
                ephemeral=True
            )
        elif isinstance(error, app_commands.BotMissingPermissions):
            await interaction.response.send_message(
                "❌ I don't have permission to perform this action!",
                ephemeral=True
            )
        else:
            logger.error(f"Slash command error: {error}")
            
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred while processing the command.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ An error occurred while processing the command.",
                    ephemeral=True
                )
