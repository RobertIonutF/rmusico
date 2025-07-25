"""YouTube help and troubleshooting utilities."""

import discord
from typing import List

def create_youtube_blocked_embed() -> discord.Embed:
    """Create an embed explaining YouTube bot detection issues."""
    embed = discord.Embed(
        title="🚫 YouTube Access Restricted",
        description="YouTube has detected automated access and is blocking the bot.",
        color=discord.Color.red()
    )
    
    embed.add_field(
        name="🤖 What happened?",
        value="YouTube has anti-bot measures that block automated music downloads to prevent abuse.",
        inline=False
    )
    
    embed.add_field(
        name="💡 Alternatives",
        value="• Try again in a few minutes\n• Use specific song names instead of URLs\n• Consider using other music sources",
        inline=False
    )
    
    embed.add_field(
        name="🔧 For Bot Owner",
        value="Consider setting up YouTube cookies or using alternative music sources like SoundCloud.",
        inline=False
    )
    
    embed.set_footer(text="This is a temporary limitation and may resolve automatically.")
    
    return embed

def create_deployment_success_embed() -> discord.Embed:
    """Create an embed showing the bot is successfully deployed."""
    embed = discord.Embed(
        title="🎵 RMusico Bot Online!",
        description="Your Discord music bot is now running and ready to play music!",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="🎮 Quick Start",
        value="Use `/play <song name>` or `!play <song name>` to start playing music!",
        inline=False
    )
    
    embed.add_field(
        name="🎛️ Interactive Controls",
        value="Click the buttons that appear on music messages for easy control!",
        inline=False
    )
    
    embed.add_field(
        name="📋 Commands",
        value="Use `/help` or `!help` to see all available commands.",
        inline=False
    )
    
    embed.set_footer(text="Bot hosted on Render • Web dashboard available")
    
    return embed

def get_troubleshooting_tips() -> List[str]:
    """Get list of troubleshooting tips for common issues."""
    return [
        "🎤 Make sure you're in a voice channel before using music commands",
        "🔊 Check that the bot has permission to connect to voice channels",
        "🎵 Try using song names instead of direct YouTube URLs",
        "⏰ Some YouTube videos may be temporarily unavailable",
        "🔄 Try the `/skip` command if a song gets stuck",
        "📱 Use interactive buttons for easier control",
        "🎛️ Use `/controls` to access the full control panel"
    ]
