"""Main Discord Music Bot implementation."""

import asyncio
import discord
from discord.ext import commands
import logging
from typing import Dict

from config import BOT_PREFIX, BOT_TOKEN
from music_queue import MusicQueue
from music_commands import MusicCommands
from register_commands import setup_commands, CommandRegistrar, SlashCommandErrorHandler
from ytdl_source import YTDLSource
from utils import create_song_embed
from ffmpeg_utils import setup_ffmpeg
from music_controls import create_music_controls

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_voice_dependencies() -> bool:
    """Check if all voice dependencies are available."""
    missing_deps = []
    
    # Check PyNaCl
    try:
        import nacl
        logger.info(f"✅ PyNaCl version: {nacl.__version__}")
    except ImportError:
        missing_deps.append("PyNaCl")
        logger.error("❌ PyNaCl not found - voice encryption will not work")
    
    # Check opus
    try:
        import discord.opus
        if discord.opus.is_loaded():
            logger.info("✅ Opus library loaded successfully")
        else:
            logger.warning("⚠️ Opus library not loaded - attempting to load...")
            try:
                discord.opus.load_opus('opus')
                if discord.opus.is_loaded():
                    logger.info("✅ Opus library loaded after manual load")
                else:
                    missing_deps.append("Opus")
                    logger.error("❌ Failed to load Opus library")
            except Exception as e:
                missing_deps.append("Opus")
                logger.error(f"❌ Error loading Opus: {e}")
    except Exception as e:
        missing_deps.append("Opus")
        logger.error(f"❌ Error checking Opus: {e}")
    
    if missing_deps:
        logger.error(f"❌ Missing voice dependencies: {', '.join(missing_deps)}")
        logger.error("💡 Install with: pip install discord.py[voice]")
        return False
    
    return True


class MusicBot(commands.Bot):
    """Enhanced Discord Music Bot with organized structure."""
    
    def __init__(self):
        # Bot configuration
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(command_prefix=BOT_PREFIX, intents=intents)
        
        # Global music queues for each guild
        self.music_queues: Dict[int, MusicQueue] = {}
        
        # Command registrar for slash commands
        self.command_registrar: CommandRegistrar = None
        
        # Remove default help command to use custom one
        self.remove_command('help')
    
    async def setup_hook(self) -> None:
        """Setup hook called when the bot is starting up."""
        # Add prefix commands cog
        await self.add_cog(MusicCommands(self))
        logger.info("Music commands cog loaded")
        
        # Set up slash commands and command registration
        self.command_registrar = await setup_commands(self)
        logger.info("Command registration system loaded")
        
        # Set up slash command error handler
        self.tree.error(SlashCommandErrorHandler.on_app_command_error)
    
    def get_queue(self, guild_id: int) -> MusicQueue:
        """Get or create music queue for guild."""
        if guild_id not in self.music_queues:
            self.music_queues[guild_id] = MusicQueue()
            logger.info(f"Created new music queue for guild {guild_id}")
        return self.music_queues[guild_id]
    
    async def play_next(self, ctx: commands.Context) -> None:
        """Play the next song in queue."""
        queue = self.get_queue(ctx.guild.id)
        player = queue.get_next()
        
        if player:
            def after_playing(error):
                if error:
                    logger.error(f'Player error: {error}')
                
                # Schedule next song
                asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.loop)
            
            # Get the actual playable audio source
            audio_source = player.get_playable_source()
            ctx.voice_client.play(audio_source, after=after_playing)
            
            # Send now playing message with interactive controls
            embed = create_song_embed(player, "🎵 Now Playing", discord.Color.blue())
            view = create_music_controls(self, ctx.guild.id)
            message = await ctx.send(embed=embed, view=view)
            view.message = message
        else:
            logger.info(f"No more songs in queue for guild {ctx.guild.id}")
    
    async def play_next_interaction(self, interaction: discord.Interaction) -> None:
        """Play the next song in queue (for slash commands)."""
        queue = self.get_queue(interaction.guild.id)
        player = queue.get_next()
        
        if player:
            def after_playing(error):
                if error:
                    logger.error(f'Player error: {error}')
                
                # Create a dummy context for the next song
                # This is a workaround since interactions don't have the same context structure
                channel = interaction.channel
                asyncio.run_coroutine_threadsafe(
                    self._play_next_from_interaction(interaction.guild.id, channel), 
                    self.loop
                )
            
            interaction.guild.voice_client.play(player.get_playable_source(), after=after_playing)
            
            # Send now playing message if we haven't responded yet
            embed = create_song_embed(player, "🎵 Now Playing", discord.Color.blue())
            view = create_music_controls(self, interaction.guild.id)
            
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, view=view)
                    # Get the message object for the view
                    message = await interaction.original_response()
                    view.message = message
                else:
                    message = await interaction.followup.send(embed=embed, view=view)
                    view.message = message
            except discord.NotFound:
                # Interaction may have expired, send to channel directly
                message = await interaction.channel.send(embed=embed, view=view)
                view.message = message
        else:
            logger.info(f"No more songs in queue for guild {interaction.guild.id}")
    
    async def _play_next_from_interaction(self, guild_id: int, channel) -> None:
        """Helper method to continue playing songs after interaction-initiated playback."""
        guild = self.get_guild(guild_id)
        if not guild or not guild.voice_client:
            return
            
        queue = self.get_queue(guild_id)
        player = queue.get_next()
        
        if player:
            def after_playing(error):
                if error:
                    logger.error(f'Player error: {error}')
                
                asyncio.run_coroutine_threadsafe(
                    self._play_next_from_interaction(guild_id, channel), 
                    self.loop
                )
            
            guild.voice_client.play(player.get_playable_source(), after=after_playing)
            
            # Send now playing message
            embed = create_song_embed(player, "🎵 Now Playing", discord.Color.blue())
            view = create_music_controls(self, guild_id)
            message = await channel.send(embed=embed, view=view)
            view.message = message
    
    async def on_ready(self) -> None:
        """Bot ready event."""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        activity = discord.Activity(type=discord.ActivityType.listening, name=f"{BOT_PREFIX}help | /help")
        await self.change_presence(activity=activity)
        
        # Log command registration stats
        if self.command_registrar:
            stats = self.command_registrar.get_command_stats()
            logger.info(f"Command stats: {stats}")
    
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Called when bot joins a new guild."""
        logger.info(f"Joined new guild: {guild.name} ({guild.id}) with {guild.member_count} members")
        
        # Sync commands to new guild for immediate availability
        if self.command_registrar:
            await self.command_registrar.on_guild_join(guild)
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"❌ Command not found. Use `{BOT_PREFIX}help` to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Missing required argument. Check the command usage.")
        elif isinstance(error, commands.CheckFailure):
            # Custom check failures (like user not in voice channel)
            # Already handled in the command, so we don't need to send another message
            pass
        else:
            logger.error(f"Command error in {ctx.command}: {error}")
            await ctx.send(f"❌ An error occurred: {str(error)}")
    
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        """Handle voice state updates."""
        # If bot is alone in voice channel, disconnect after a delay
        if member == self.user:
            return
        
        voice_client = member.guild.voice_client
        if voice_client and len(voice_client.channel.members) == 1:  # Only bot left
            logger.info(f"Bot alone in voice channel {voice_client.channel.name}, scheduling disconnect")
            await asyncio.sleep(60)  # Wait 1 minute
            
            # Check again if still alone
            if voice_client.is_connected() and len(voice_client.channel.members) == 1:
                queue = self.get_queue(member.guild.id)
                queue.clear()
                await voice_client.disconnect()
                logger.info(f"Disconnected from {voice_client.channel.name} due to inactivity")


def main() -> None:
    """Main function to run the bot."""
    # Check voice dependencies first
    if not check_voice_dependencies():
        logger.error("❌ Voice dependencies missing! Audio may not work properly.")
        logger.error("💡 Install with: pip install discord.py[voice]")
        # Continue anyway in case user wants to test other functionality
    
    # Check FFmpeg installation
    if not setup_ffmpeg():
        logger.error("❌ FFmpeg setup failed! The bot may not work properly.")
        logger.error("Please install FFmpeg and restart the bot.")
        return
    
    if not BOT_TOKEN:
        logger.error("❌ Please set your Discord bot token!")
        logger.error("Create a .env file with DISCORD_BOT_TOKEN=your_token_here")
        logger.error("Or set the DISCORD_BOT_TOKEN environment variable")
        return
    
    bot = MusicBot()
    
    try:
        bot.run(BOT_TOKEN)
    except discord.LoginFailure:
        logger.error("❌ Invalid bot token!")
    except Exception as e:
        logger.error(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    main()
