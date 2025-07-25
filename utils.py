"""Utility functions for the Discord Music Bot."""

import discord
from typing import List, Any

from config import MAX_QUEUE_DISPLAY


def format_duration(duration: int) -> str:
    """Format duration in seconds as MM:SS string."""
    if not duration:
        return "Unknown"
    
    minutes = duration // 60
    seconds = duration % 60
    return f"{minutes}:{seconds:02d}"


def create_embed(title: str, description: str = "", color: discord.Color = discord.Color.blue()) -> discord.Embed:
    """Create a standardized embed with consistent styling."""
    return discord.Embed(title=title, description=description, color=color)


def create_queue_embed(queue) -> discord.Embed:
    """Create an embed showing the current music queue."""
    embed = create_embed("🎵 Music Queue")
    
    # Show currently playing song
    if queue.current:
        embed.add_field(
            name="🎵 Now Playing",
            value=f"**{queue.current.title}**",
            inline=False
        )
        
        if queue.loop_mode:
            embed.add_field(
                name="🔂 Loop Mode",
                value="Enabled",
                inline=True
            )
    
    # Show queue
    if queue.queue:
        queue_list = []
        display_count = min(len(queue.queue), MAX_QUEUE_DISPLAY)
        
        for i, song in enumerate(queue.queue[:display_count], 1):
            queue_list.append(f"{i}. **{song.title}**")
        
        embed.add_field(
            name=f"📝 Up Next ({len(queue.queue)} songs)",
            value="\n".join(queue_list) if queue_list else "No songs in queue",
            inline=False
        )
        
        if len(queue.queue) > MAX_QUEUE_DISPLAY:
            embed.add_field(
                name="...",
                value=f"And {len(queue.queue) - MAX_QUEUE_DISPLAY} more songs",
                inline=False
            )
    else:
        if not queue.current:
            embed.add_field(
                name="📝 Queue",
                value="No songs in queue",
                inline=False
            )
    
    return embed


def create_song_embed(song: Any, title: str = "🎵 Song Info", color: discord.Color = discord.Color.green()) -> discord.Embed:
    """Create an embed for displaying song information."""
    embed = create_embed(title, f"**{song.title}**", color)
    
    embed.add_field(
        name="Duration", 
        value=song.format_duration() if hasattr(song, 'format_duration') else format_duration(song.duration), 
        inline=True
    )
    embed.add_field(name="Uploader", value=song.uploader or "Unknown", inline=True)
    
    if hasattr(song, 'thumbnail') and song.thumbnail:
        embed.set_thumbnail(url=song.thumbnail)
    
    return embed


def create_search_results_embed(query: str, results: List[Any]) -> discord.Embed:
    """Create an embed showing search results."""
    embed = create_embed(f"🔍 Search Results for: {query}")
    
    for i, entry in enumerate(results, 1):
        duration = format_duration(entry.get('duration', 0))
        embed.add_field(
            name=f"{i}. {entry.get('title', 'Unknown')}",
            value=f"**Duration:** {duration}\n**Uploader:** {entry.get('uploader', 'Unknown')}",
            inline=False
        )
    
    embed.set_footer(text="Use !play <song title> to play a song")
    return embed
