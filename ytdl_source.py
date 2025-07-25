"""YouTube audio source and utilities for the Discord Music Bot."""

import asyncio
import discord
import yt_dlp
import logging
import os
from typing import Optional, Dict, Any, ClassVar

from config import YTDL_FORMAT_OPTIONS, FFMPEG_OPTIONS, FFMPEG_OPUS_OPTIONS, RENDER_FFMPEG_OPTIONS, DEFAULT_VOLUME, MAX_SEARCH_RESULTS
from modern_youtube import get_modern_extractor, get_multi_source_player

logger = logging.getLogger(__name__)

def get_ffmpeg_options() -> Dict[str, str]:
    """Get appropriate FFmpeg options based on environment."""
    # Detect if running on Render.com or similar constrained environment
    if os.environ.get('RENDER') or os.environ.get('PORT'):
        logger.info("Detected hosting environment, using optimized FFmpeg settings")
        return RENDER_FFMPEG_OPTIONS
    else:
        logger.info("Using standard FFmpeg settings")
        return FFMPEG_OPTIONS


class YTDLSource:
    """YouTube audio source for Discord voice playback."""
    
    ytdl: ClassVar[yt_dlp.YoutubeDL] = yt_dlp.YoutubeDL(YTDL_FORMAT_OPTIONS)
    
    def __init__(self, source: discord.AudioSource, *, data: Dict[str, Any], volume: float = DEFAULT_VOLUME):
        # Store the raw source and data
        self._source = source
        self.data = data
        self.title = data.get('title', 'Unknown')
        self.url = data.get('url', '')
        self.duration = data.get('duration')
        self.uploader = data.get('uploader')
        self.thumbnail = data.get('thumbnail')
        self.volume = volume
        
        # Create the final playable source with volume control if it's PCM
        if isinstance(source, discord.FFmpegPCMAudio):
            self.source = discord.PCMVolumeTransformer(source, volume=volume)
            self.supports_volume = True
        else:
            # For Opus sources, we can't apply volume transformation
            self.source = source
            self.supports_volume = False
    
    def set_volume(self, volume: float) -> None:
        """Set the volume of the audio source (only works with PCM)."""
        self.volume = volume
        if self.supports_volume and hasattr(self.source, 'volume'):
            self.source.volume = volume
        elif not self.supports_volume:
            logger.warning("Volume control not supported for Opus audio sources")
    
    def get_playable_source(self) -> discord.AudioSource:
        """Get the Discord AudioSource that can be played."""
        return self.source

    @classmethod
    async def from_url(cls, url: str, *, loop: Optional[asyncio.AbstractEventLoop] = None, stream: bool = False) -> 'YTDLSource':
        """Extract audio from YouTube URL using modern extraction."""
        loop = loop or asyncio.get_event_loop()
        
        try:
            logger.info(f"Extracting audio from URL: {url}")
            
            # Use modern extractor with comprehensive fallbacks
            modern_extractor = get_modern_extractor()
            data = await modern_extractor.extract_with_fallback(url)
            
            if not data:
                raise Exception("Failed to extract audio data from URL")
            
            audio_url = data.get('url')
            if not audio_url:
                raise Exception("No audio URL found in extracted data")
            
            # Get appropriate FFmpeg options for environment
            ffmpeg_opts = get_ffmpeg_options()
            
            # Try creating audio source with environment-appropriate settings
            try:
                # Try Opus first for better compression on constrained environments
                if os.environ.get('RENDER') or os.environ.get('PORT'):
                    source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_opts)
                    logger.info(f"Created Opus audio source for hosting environment: {data.get('title', 'Unknown')}")
                else:
                    source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_opts)
                    logger.info(f"Created PCM audio source: {data.get('title', 'Unknown')}")
                    
            except Exception as primary_error:
                logger.warning(f"Primary audio source failed: {primary_error}")
                try:
                    # Fallback to the other format
                    if os.environ.get('RENDER') or os.environ.get('PORT'):
                        source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
                        logger.info(f"Fallback to PCM audio source: {data.get('title', 'Unknown')}")
                    else:
                        source = discord.FFmpegOpusAudio(audio_url, **FFMPEG_OPUS_OPTIONS)
                        logger.info(f"Fallback to Opus audio source: {data.get('title', 'Unknown')}")
                except Exception as fallback_error:
                    logger.error(f"Both audio sources failed: Primary={primary_error}, Fallback={fallback_error}")
                    raise fallback_error
            
            return cls(source, data=data)
            
        except Exception as e:
            logger.error(f"Error extracting audio from {url}: {e}")
            raise

    @classmethod
    async def search_youtube(cls, query: str, *, loop: Optional[asyncio.AbstractEventLoop] = None) -> Optional[Dict[str, Any]]:
        """Search YouTube for a query."""
        loop = loop or asyncio.get_event_loop()
        
    @classmethod
    async def search_youtube(cls, query: str, *, loop: Optional[asyncio.AbstractEventLoop] = None) -> Optional[Dict[str, Any]]:
        """Search YouTube for a query using modern extraction."""
        loop = loop or asyncio.get_event_loop()
        
        try:
            logger.info(f"Searching YouTube for: {query}")
            
            # Use modern extractor for searches
            modern_extractor = get_modern_extractor()
            result = await modern_extractor.search_youtube(query)
            
            if result:
                logger.info(f"Found video: {result.get('title', 'Unknown')}")
                return result
            
            logger.warning(f"No results found for query: {query}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching YouTube for {query}: {e}")
            return None

    @classmethod
    async def search_youtube_multiple(cls, query: str, *, loop: Optional[asyncio.AbstractEventLoop] = None) -> list:
        """Search YouTube for multiple results using modern extraction."""
        loop = loop or asyncio.get_event_loop()
        
        try:
            logger.info(f"Searching YouTube for multiple results: {query}")
            
            # Use the modern extractor for multi-search
            modern_extractor = get_modern_extractor()
            
            # Create a search-specific extraction
            search_query = f"ytsearch{MAX_SEARCH_RESULTS}:{query}"
            opts = modern_extractor.base_opts.copy()
            opts['format'] = 'bestaudio[ext=webm]/bestaudio'
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                data = await loop.run_in_executor(
                    None, 
                    lambda: ydl.extract_info(search_query, download=False)
                )
            
            if 'entries' in data:
                logger.info(f"Found {len(data['entries'])} results")
                return data['entries']
            
            logger.warning(f"No results found for query: {query}")
            return []
            
        except Exception as e:
            logger.error(f"Error searching YouTube for {query}: {e}")
            return []

    def format_duration(self) -> str:
        """Format duration as MM:SS string."""
        if not self.duration:
            return "Unknown"
        
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02d}"
