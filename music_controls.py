"""Interactive music control views and buttons for Discord Music Bot."""

import asyncio
import discord
from discord.ext import commands
from typing import Optional, TYPE_CHECKING
import logging
import random

if TYPE_CHECKING:
    from music_bot import MusicBot

logger = logging.getLogger(__name__)


class MusicControlView(discord.ui.View):
    """Interactive view with music control buttons."""
    
    def __init__(self, bot: 'MusicBot', guild_id: int, *, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.guild_id = guild_id
        self.message: Optional[discord.Message] = None
    
    async def on_timeout(self) -> None:
        """Disable all buttons when the view times out."""
        for item in self.children:
            item.disabled = True
        
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass  # Message was deleted
            except Exception as e:
                logger.error(f"Error disabling view on timeout: {e}")
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user can use the music controls."""
        # Allow anyone in the same voice channel or with manage messages permission
        if interaction.user.guild_permissions.manage_messages:
            return True
        
        # Check if user is in the same voice channel as the bot
        voice_client = interaction.guild.voice_client
        if voice_client and interaction.user.voice:
            return interaction.user.voice.channel == voice_client.channel
        
        await interaction.response.send_message(
            "❌ You must be in the same voice channel as the bot to use these controls!",
            ephemeral=True
        )
        return False
    
    @discord.ui.button(label='⏸️', style=discord.ButtonStyle.secondary, custom_id='music:pause')
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Pause/Resume the current song."""
        voice_client = interaction.guild.voice_client
        
        if not voice_client:
            await interaction.response.send_message("❌ Bot is not connected to voice!", ephemeral=True)
            return
        
        if voice_client.is_playing():
            voice_client.pause()
            button.label = '▶️'
            button.style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("⏸️ Paused playback!", ephemeral=True)
        elif voice_client.is_paused():
            voice_client.resume()
            button.label = '⏸️'
            button.style = discord.ButtonStyle.secondary
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("▶️ Resumed playback!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)
    
    @discord.ui.button(label='⏹️', style=discord.ButtonStyle.danger, custom_id='music:stop')
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Stop the current song and clear the queue."""
        voice_client = interaction.guild.voice_client
        
        if not voice_client:
            await interaction.response.send_message("❌ Bot is not connected to voice!", ephemeral=True)
            return
        
        # Clear the queue and stop playback
        queue = self.bot.get_queue(self.guild_id)
        queue.clear()
        queue.current = None
        
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            await interaction.response.send_message("⏹️ Stopped playback and cleared queue!")
        else:
            await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)
    
    @discord.ui.button(label='⏭️', style=discord.ButtonStyle.primary, custom_id='music:skip')
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Skip to the next song."""
        voice_client = interaction.guild.voice_client
        
        if not voice_client:
            await interaction.response.send_message("❌ Bot is not connected to voice!", ephemeral=True)
            return
        
        queue = self.bot.get_queue(self.guild_id)
        
        if voice_client.is_playing() or voice_client.is_paused():
            if len(queue.queue) > 0 or queue.loop_mode:
                voice_client.stop()  # This will trigger the after callback and play the next song
                await interaction.response.send_message("⏭️ Skipped to next song!")
            else:
                voice_client.stop()
                await interaction.response.send_message("⏭️ Skipped! No more songs in queue.")
        else:
            await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)
    
    @discord.ui.button(label='🔀', style=discord.ButtonStyle.secondary, custom_id='music:shuffle')
    async def shuffle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Shuffle the current queue."""
        queue = self.bot.get_queue(self.guild_id)
        
        if len(queue.queue) < 2:
            await interaction.response.send_message("❌ Need at least 2 songs in queue to shuffle!", ephemeral=True)
            return
        
        random.shuffle(queue.queue)
        await interaction.response.send_message(f"🔀 Shuffled {len(queue.queue)} songs in the queue!")
    
    @discord.ui.button(label='🔄', style=discord.ButtonStyle.secondary, custom_id='music:loop')
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Toggle loop mode for the current song."""
        queue = self.bot.get_queue(self.guild_id)
        queue.loop_mode = not queue.loop_mode
        
        if queue.loop_mode:
            button.label = '🔂'
            button.style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("🔂 Loop mode enabled!", ephemeral=True)
        else:
            button.label = '🔄'
            button.style = discord.ButtonStyle.secondary
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("🔄 Loop mode disabled!", ephemeral=True)


class QueueControlView(discord.ui.View):
    """View for queue management controls."""
    
    def __init__(self, bot: 'MusicBot', guild_id: int, *, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.guild_id = guild_id
        self.message: Optional[discord.Message] = None
    
    async def on_timeout(self) -> None:
        """Disable all buttons when the view times out."""
        for item in self.children:
            item.disabled = True
        
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Error disabling queue view on timeout: {e}")
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user can use the queue controls."""
        # Allow anyone in the same voice channel or with manage messages permission
        if interaction.user.guild_permissions.manage_messages:
            return True
        
        voice_client = interaction.guild.voice_client
        if voice_client and interaction.user.voice:
            return interaction.user.voice.channel == voice_client.channel
        
        await interaction.response.send_message(
            "❌ You must be in the same voice channel as the bot to use these controls!",
            ephemeral=True
        )
        return False
    
    @discord.ui.button(label='📋 Show Queue', style=discord.ButtonStyle.primary, custom_id='queue:show')
    async def show_queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show the current queue."""
        from utils import create_queue_embed  # Import here to avoid circular imports
        
        queue = self.bot.get_queue(self.guild_id)
        embed = create_queue_embed(queue)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='🗑️ Clear Queue', style=discord.ButtonStyle.danger, custom_id='queue:clear')
    async def clear_queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Clear the queue."""
        queue = self.bot.get_queue(self.guild_id)
        
        if len(queue.queue) == 0:
            await interaction.response.send_message("❌ Queue is already empty!", ephemeral=True)
            return
        
        count = len(queue.queue)
        queue.clear()
        await interaction.response.send_message(f"🗑️ Cleared {count} songs from the queue!")
    
    @discord.ui.button(label='🔀 Shuffle Queue', style=discord.ButtonStyle.secondary, custom_id='queue:shuffle')
    async def shuffle_queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Shuffle the queue."""
        queue = self.bot.get_queue(self.guild_id)
        
        if len(queue.queue) < 2:
            await interaction.response.send_message("❌ Need at least 2 songs in queue to shuffle!", ephemeral=True)
            return
        
        random.shuffle(queue.queue)
        await interaction.response.send_message(f"🔀 Shuffled {len(queue.queue)} songs!")


class VolumeControlView(discord.ui.View):
    """View for volume control with buttons."""
    
    def __init__(self, bot: 'MusicBot', guild_id: int, *, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.guild_id = guild_id
        self.message: Optional[discord.Message] = None
    
    async def on_timeout(self) -> None:
        """Disable all buttons when the view times out."""
        for item in self.children:
            item.disabled = True
        
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Error disabling volume view on timeout: {e}")
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user can use the volume controls."""
        if interaction.user.guild_permissions.manage_messages:
            return True
        
        voice_client = interaction.guild.voice_client
        if voice_client and interaction.user.voice:
            return interaction.user.voice.channel == voice_client.channel
        
        await interaction.response.send_message(
            "❌ You must be in the same voice channel as the bot to use these controls!",
            ephemeral=True
        )
        return False
    
    @discord.ui.button(label='🔇', style=discord.ButtonStyle.secondary, custom_id='volume:mute')
    async def mute_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mute/unmute the audio."""
        queue = self.bot.get_queue(self.guild_id)
        
        if not queue.current:
            await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)
            return
        
        if not queue.current.supports_volume:
            await interaction.response.send_message("⚠️ Volume control not supported for current audio format!", ephemeral=True)
            return
        
        # Check current volume to determine if muted
        current_volume = queue.current.volume
        
        if current_volume > 0:
            # Mute
            queue.current.set_volume(0)
            button.label = '🔊'
            button.style = discord.ButtonStyle.danger
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("🔇 Muted audio!", ephemeral=True)
        else:
            # Unmute to 50%
            queue.current.set_volume(0.5)
            button.label = '🔇'
            button.style = discord.ButtonStyle.secondary
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("🔊 Unmuted audio (50%)!", ephemeral=True)
    
    @discord.ui.button(label='🔉', style=discord.ButtonStyle.secondary, custom_id='volume:down')
    async def volume_down_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Decrease volume by 10%."""
        queue = self.bot.get_queue(self.guild_id)
        
        if not queue.current:
            await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)
            return
        
        if not queue.current.supports_volume:
            await interaction.response.send_message("⚠️ Volume control not supported for current audio format!", ephemeral=True)
            return
        
        current_volume = queue.current.volume
        new_volume = max(0, current_volume - 0.1)
        queue.current.set_volume(new_volume)
        
        percentage = int(new_volume * 100)
        await interaction.response.send_message(f"🔉 Volume decreased to {percentage}%!", ephemeral=True)
    
    @discord.ui.button(label='🔊', style=discord.ButtonStyle.secondary, custom_id='volume:up')
    async def volume_up_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Increase volume by 10%."""
        queue = self.bot.get_queue(self.guild_id)
        
        if not queue.current:
            await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)
            return
        
        if not queue.current.supports_volume:
            await interaction.response.send_message("⚠️ Volume control not supported for current audio format!", ephemeral=True)
            return
        
        current_volume = queue.current.volume
        new_volume = min(1.0, current_volume + 0.1)
        queue.current.set_volume(new_volume)
        
        percentage = int(new_volume * 100)
        await interaction.response.send_message(f"🔊 Volume increased to {percentage}%!", ephemeral=True)


def create_music_controls(bot: 'MusicBot', guild_id: int) -> MusicControlView:
    """Create a music control view for the given guild."""
    return MusicControlView(bot, guild_id)


def create_queue_controls(bot: 'MusicBot', guild_id: int) -> QueueControlView:
    """Create a queue control view for the given guild."""
    return QueueControlView(bot, guild_id)


def create_volume_controls(bot: 'MusicBot', guild_id: int) -> VolumeControlView:
    """Create a volume control view for the given guild."""
    return VolumeControlView(bot, guild_id)
