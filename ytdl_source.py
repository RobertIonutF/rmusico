"""YouTube audio source and utilities for the Discord Music Bot."""

import asyncio
import discord
import yt_dlp
import logging
from typing import Optional, Dict, Any, ClassVar

from config import YTDL_FORMAT_OPTIONS, FFMPEG_OPTIONS, FFMPEG_OPUS_OPTIONS, DEFAULT_VOLUME, MAX_SEARCH_RESULTS
from alternative_extractor import fallback_extract

logger = logging.getLogger(__name__)


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
        """Extract audio from YouTube URL."""
        loop = loop or asyncio.get_event_loop()
        
        try:
            logger.info(f"Extracting audio from URL: {url}")
            data = await loop.run_in_executor(
                None, 
                lambda: cls.ytdl.extract_info(url, download=not stream)
            )
            
            if 'entries' in data:
                # Handle playlists - take first video
                data = data['entries'][0]
                logger.info(f"Playlist detected, using first video: {data.get('title', 'Unknown')}")
            
            filename = data['url'] if stream else cls.ytdl.prepare_filename(data)
            
            # Use PCM audio for better compatibility with volume control
            # PCM allows volume transformation while Opus does not
            try:
                source = discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS)
                logger.info(f"Successfully created PCM audio source for: {data.get('title', 'Unknown')}")
            except Exception as pcm_error:
                logger.warning(f"PCM audio failed, trying Opus: {pcm_error}")
                try:
                    source = discord.FFmpegOpusAudio(filename, **FFMPEG_OPUS_OPTIONS)
                    logger.info(f"Successfully created Opus audio source (no volume control): {data.get('title', 'Unknown')}")
                except Exception as opus_error:
                    logger.error(f"Both PCM and Opus failed: PCM={pcm_error}, Opus={opus_error}")
                    raise opus_error
            
            return cls(source, data=data)
            
        except Exception as e:
            logger.error(f"Error extracting audio from {url}: {e}")
            
            # Try alternative extraction if main method fails
            if "Sign in to confirm you're not a bot" in str(e) or "bot" in str(e).lower():
                logger.info("Bot detection encountered, trying alternative extraction...")
                try:
                    fallback_data = await fallback_extract(url)
                    if fallback_data:
                        # Create a dummy audio source for fallback
                        # This is a placeholder - in production you'd need a different approach
                        logger.warning("⚠️ Using fallback extraction - limited functionality")
                        # For now, still raise the original error as we need proper audio stream
                        raise Exception("YouTube bot detection - bot cannot play audio without proper authentication")
                    else:
                        raise e
                except Exception as fallback_error:
                    logger.error(f"Fallback extraction also failed: {fallback_error}")
                    raise e
            else:
                raise

    @classmethod
    async def search_youtube(cls, query: str, *, loop: Optional[asyncio.AbstractEventLoop] = None) -> Optional[Dict[str, Any]]:
        """Search YouTube for a query."""
        loop = loop or asyncio.get_event_loop()
        
        try:
            logger.info(f"Searching YouTube for: {query}")
            # Search for videos
            search_query = f"ytsearch:{query}"
            data = await loop.run_in_executor(
                None, 
                lambda: cls.ytdl.extract_info(search_query, download=False)
            )
            
            if 'entries' in data and len(data['entries']) > 0:
                result = data['entries'][0]
                logger.info(f"Found video: {result.get('title', 'Unknown')}")
                return result
            
            logger.warning(f"No results found for query: {query}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching YouTube for {query}: {e}")
            return None

    @classmethod
    async def search_youtube_multiple(cls, query: str, *, loop: Optional[asyncio.AbstractEventLoop] = None) -> list:
        """Search YouTube for multiple results."""
        loop = loop or asyncio.get_event_loop()
        
        try:
            logger.info(f"Searching YouTube for multiple results: {query}")
            search_query = f"ytsearch{MAX_SEARCH_RESULTS}:{query}"
            data = await loop.run_in_executor(
                None, 
                lambda: cls.ytdl.extract_info(search_query, download=False)
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
