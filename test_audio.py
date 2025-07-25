#!/usr/bin/env python3
"""Audio testing script for Discord Music Bot."""

import asyncio
import discord
import logging
from typing import Optional
import tempfile
import os

from config import BOT_TOKEN, FFMPEG_OPTIONS, FFMPEG_OPUS_OPTIONS
from ytdl_source import YTDLSource
from ffmpeg_utils import setup_ffmpeg, ffmpeg_manager
from music_controls import create_music_controls

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AudioTestBot(discord.Client):
    """Simple bot for testing audio functionality."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(intents=intents)
        
        # Simple queue system for testing
        self.current_player = None
        
    def get_queue(self, guild_id: int):
        """Mock queue method for testing."""
        class MockQueue:
            def __init__(self):
                self.current = None
                self.queue = []
                self.loop_mode = False
            
            def clear(self):
                self.queue.clear()
                
        mock_queue = MockQueue()
        mock_queue.current = self.current_player
        return mock_queue
        
    async def on_ready(self):
        """Bot ready event."""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info('Type "!testplay <url>" in a voice channel to test audio')
        
    async def on_message(self, message):
        """Handle messages."""
        if message.author == self.user:
            return
            
        if message.content.startswith('!testplay'):
            await self.test_audio_command(message)
        elif message.content.startswith('!testjoin'):
            await self.join_voice_command(message)
        elif message.content.startswith('!testleave'):
            await self.leave_voice_command(message)
        elif message.content.startswith('!testffmpeg'):
            await self.test_ffmpeg_command(message)
    
    async def join_voice_command(self, message):
        """Join voice channel command."""
        if not message.author.voice:
            await message.channel.send("❌ You must be in a voice channel!")
            return
            
        channel = message.author.voice.channel
        
        try:
            voice_client = await channel.connect()
            await message.channel.send(f"✅ Connected to {channel.name}")
            logger.info(f"Connected to voice channel: {channel.name}")
        except Exception as e:
            await message.channel.send(f"❌ Failed to connect: {e}")
            logger.error(f"Failed to connect to voice: {e}")
    
    async def leave_voice_command(self, message):
        """Leave voice channel command."""
        if message.guild.voice_client:
            await message.guild.voice_client.disconnect()
            await message.channel.send("✅ Disconnected from voice channel")
            logger.info("Disconnected from voice channel")
        else:
            await message.channel.send("❌ Not connected to any voice channel")
    
    async def test_ffmpeg_command(self, message):
        """Test FFmpeg functionality."""
        await message.channel.send("🧪 Testing FFmpeg functionality...")
        
        # Test FFmpeg installation
        if not ffmpeg_manager.check_ffmpeg_installation():
            await message.channel.send("❌ FFmpeg not found!")
            return
        
        version = ffmpeg_manager.get_ffmpeg_version()
        await message.channel.send(f"✅ FFmpeg version: {version or 'unknown'}")
        
        # Test audio conversion
        test_results = ffmpeg_manager.test_discord_audio_conversion()
        
        if test_results['opus']:
            await message.channel.send("✅ Opus conversion: PASS")
        else:
            await message.channel.send("❌ Opus conversion: FAIL")
            
        if test_results['pcm']:
            await message.channel.send("✅ PCM conversion: PASS")
        else:
            await message.channel.send("❌ PCM conversion: FAIL")
    
    async def test_audio_command(self, message):
        """Test audio playback."""
        # Check if user is in voice channel
        if not message.author.voice:
            await message.channel.send("❌ You must be in a voice channel to test audio!")
            return
        
        # Extract URL from message
        parts = message.content.split(maxsplit=1)
        if len(parts) < 2:
            await message.channel.send("❌ Please provide a URL: `!testplay <url>`")
            return
        
        url = parts[1]
        
        # Connect to voice if not already connected
        if not message.guild.voice_client:
            try:
                voice_client = await message.author.voice.channel.connect()
                logger.info(f"Connected to voice channel: {message.author.voice.channel.name}")
            except Exception as e:
                await message.channel.send(f"❌ Failed to connect to voice: {e}")
                return
        else:
            voice_client = message.guild.voice_client
        
        await message.channel.send(f"🎵 Testing audio from: {url}")
        
        try:
            # Test with YTDLSource
            logger.info(f"Creating audio source from: {url}")
            player = await YTDLSource.from_url(url, loop=self.loop, stream=True)
            
            def after_playing(error):
                if error:
                    logger.error(f'Player error: {error}')
                    asyncio.run_coroutine_threadsafe(
                        message.channel.send(f"❌ Playback error: {error}"), 
                        self.loop
                    )
                else:
                    logger.info("Audio test completed successfully")
                    asyncio.run_coroutine_threadsafe(
                        message.channel.send("✅ Audio test completed!"), 
                        self.loop
                    )
            
            voice_client.play(player.get_playable_source(), after=after_playing)
            
            # Store current player for controls
            self.current_player = player
            
            # Send now playing message with controls
            embed = discord.Embed(
                title="🎶 Now Playing", 
                description=f"**{player.title}**",
                color=discord.Color.blue()
            )
            
            # Add simple controls
            view = create_music_controls(self, message.guild.id)
            response = await message.channel.send(embed=embed, view=view)
            view.message = response
            
            logger.info(f"Started playing: {player.title}")
            
        except Exception as e:
            await message.channel.send(f"❌ Error creating audio source: {e}")
            logger.error(f"Error creating audio source: {e}")


async def main():
    """Main function."""
    # Check FFmpeg first
    if not setup_ffmpeg():
        print("❌ FFmpeg setup failed! Please install FFmpeg.")
        return
    
    if not BOT_TOKEN:
        print("❌ Please set DISCORD_BOT_TOKEN in your .env file")
        return
    
    print("🎵 Audio Test Bot")
    print("Commands:")
    print("  !testjoin - Join your voice channel")
    print("  !testplay <url> - Test audio playback")
    print("  !testffmpeg - Test FFmpeg functionality")
    print("  !testleave - Leave voice channel")
    print()
    
    bot = AudioTestBot()
    
    try:
        await bot.start(BOT_TOKEN)
    except discord.LoginFailure:
        print("❌ Invalid bot token!")
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
