"""Modern YouTube extractor with 2024-2025 bot detection handling."""

import asyncio
import logging
import aiohttp
from typing import Optional, Dict, Any, List
import yt_dlp
import os

from config import YTDL_FORMAT_OPTIONS

logger = logging.getLogger(__name__)

class ModernYouTubeExtractor:
    """Advanced YouTube extractor with comprehensive fallback strategies."""
    
    def __init__(self):
        self.base_opts = YTDL_FORMAT_OPTIONS.copy()
        self.extraction_cache = {}  # Short-term URL cache
        self.failed_urls = set()   # Track recently failed URLs
        
    async def extract_with_fallback(self, url: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """Extract with comprehensive error handling for Render constraints."""
        
        # Check cache first
        if url in self.extraction_cache:
            cached = self.extraction_cache[url]
            if await self._validate_url(cached.get('url', '')):
                logger.info(f"Using cached extraction for: {url}")
                return cached
        
        # Skip recently failed URLs briefly
        if url in self.failed_urls:
            logger.warning(f"Skipping recently failed URL: {url}")
            return None
        
        # Try different format strategies
        format_strategies = [
            'bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio',
            'bestaudio[ext=webm]',
            'bestaudio[ext=m4a]', 
            'worst[ext=webm]/worst[ext=m4a]',
            'bestaudio',
        ]
        
        for attempt in range(max_retries):
            for format_str in format_strategies:
                try:
                    logger.info(f"Attempt {attempt + 1}/{max_retries}, format: {format_str}")
                    
                    # Create strategy-specific options
                    opts = self.base_opts.copy()
                    opts['format'] = format_str
                    
                    # Add specific client rotation for this attempt
                    client_order = self._get_client_order(attempt)
                    opts['extractor_args']['youtube']['player_client'] = client_order
                    
                    loop = asyncio.get_event_loop()
                    
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        data = await loop.run_in_executor(
                            None, 
                            lambda: ydl.extract_info(url, download=False)
                        )
                    
                    if 'entries' in data:
                        data = data['entries'][0]
                    
                    # Validate extracted data
                    audio_url = data.get('url')
                    if not audio_url or 'Invalid' in str(audio_url):
                        raise Exception("Invalid audio URL extracted")
                    
                    # Test URL accessibility with timeout
                    if not await self._validate_url(audio_url):
                        raise Exception(f"Audio URL validation failed")
                    
                    result = {
                        'url': audio_url,
                        'title': data.get('title', 'Unknown Title'),
                        'duration': data.get('duration', 0),
                        'uploader': data.get('uploader', 'Unknown'),
                        'webpage_url': data.get('webpage_url', url),
                        'thumbnail': data.get('thumbnail'),
                        'id': data.get('id', ''),
                        'extractor': data.get('extractor', 'youtube'),
                        'format_id': data.get('format_id', 'unknown')
                    }
                    
                    # Cache successful extraction briefly
                    self.extraction_cache[url] = result
                    
                    # Clean up failed URLs on success
                    if url in self.failed_urls:
                        self.failed_urls.remove(url)
                    
                    logger.info(f"✅ Extraction successful: {result['title']}")
                    return result
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.warning(f"❌ Format {format_str} failed: {error_msg}")
                    
                    # Check for specific error types
                    if any(keyword in error_msg.lower() for keyword in 
                           ['sign in', 'bot', 'captcha', 'blocked']):
                        logger.info("Bot detection encountered, trying next strategy...")
                        continue
                    elif 'unavailable' in error_msg.lower():
                        logger.error("Video unavailable, marking as failed")
                        self.failed_urls.add(url)
                        return None
                    else:
                        # Other errors, continue with next format
                        continue
            
            # Exponential backoff between retry attempts
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 10)
                logger.info(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        # All strategies failed
        logger.error(f"All extraction strategies failed for: {url}")
        self.failed_urls.add(url)
        return None
    
    def _get_client_order(self, attempt: int) -> List[str]:
        """Get client order based on attempt number."""
        client_strategies = [
            ['mweb', 'ios', 'android_music'],      # Mobile-first
            ['ios', 'mweb', 'tv'],                 # iOS-first
            ['android_music', 'mweb', 'tv'],       # Android Music-first  
            ['tv', 'mweb', 'ios'],                 # TV-first
        ]
        return client_strategies[attempt % len(client_strategies)]
    
    async def _validate_url(self, audio_url: str, timeout: int = 10) -> bool:
        """Validate that the audio URL is accessible."""
        if not audio_url or not audio_url.startswith('http'):
            return False
        
        try:
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession(timeout=timeout_obj, headers=headers) as session:
                async with session.head(audio_url) as resp:
                    is_valid = resp.status in [200, 206]  # 206 for partial content
                    if not is_valid:
                        logger.warning(f"URL validation failed with status {resp.status}")
                    return is_valid
                    
        except asyncio.TimeoutError:
            logger.warning("URL validation timed out")
            return False
        except Exception as e:
            logger.warning(f"URL validation error: {e}")
            return False
    
    async def search_youtube(self, query: str, max_results: int = 1) -> Optional[Dict[str, Any]]:
        """Search YouTube with modern extraction."""
        try:
            search_query = f"ytsearch{max_results}:{query}"
            logger.info(f"Searching YouTube: {query}")
            
            opts = self.base_opts.copy()
            opts['format'] = 'bestaudio[ext=webm]/bestaudio'
            
            loop = asyncio.get_event_loop()
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                data = await loop.run_in_executor(
                    None, 
                    lambda: ydl.extract_info(search_query, download=False)
                )
            
            if 'entries' in data and len(data['entries']) > 0:
                result = data['entries'][0]
                logger.info(f"Found: {result.get('title', 'Unknown')}")
                
                # Pre-validate the result
                if await self._validate_url(result.get('url', '')):
                    return result
                else:
                    logger.warning("Search result URL validation failed")
                    return None
            
            logger.warning(f"No search results for: {query}")
            return None
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return None
    
    def cleanup_cache(self):
        """Clean up old cache entries."""
        # Simple cleanup - in production, you'd implement TTL
        if len(self.extraction_cache) > 50:
            # Keep only the most recent 25 entries
            items = list(self.extraction_cache.items())
            self.extraction_cache = dict(items[-25:])
        
        # Clean up failed URLs after some time
        if len(self.failed_urls) > 100:
            self.failed_urls.clear()

class MultiSourcePlayer:
    """Multi-source fallback player for when YouTube fails."""
    
    def __init__(self):
        self.extractor = ModernYouTubeExtractor()
    
    async def get_playable_source(self, query: str) -> Optional[Dict[str, Any]]:
        """Get playable source with multiple fallback strategies."""
        
        # Strategy 1: Direct URL if provided
        if query.startswith(('http://', 'https://')):
            result = await self.extractor.extract_with_fallback(query)
            if result:
                return result
        
        # Strategy 2: Search for exact query
        result = await self.extractor.search_youtube(query)
        if result:
            return result
        
        # Strategy 3: Try search variations
        search_variations = [
            f"{query} audio",
            f"{query} official", 
            f"{query} music",
            f"{query} full"
        ]
        
        for variation in search_variations:
            try:
                result = await self.extractor.search_youtube(variation)
                if result:
                    logger.info(f"Found using variation: {variation}")
                    return result
            except Exception as e:
                logger.debug(f"Variation {variation} failed: {e}")
                continue
        
        logger.error(f"All strategies failed for query: {query}")
        return None

# Global instances
_modern_extractor = None
_multi_source_player = None

def get_modern_extractor() -> ModernYouTubeExtractor:
    """Get or create the global modern extractor instance."""
    global _modern_extractor
    if _modern_extractor is None:
        _modern_extractor = ModernYouTubeExtractor()
    return _modern_extractor

def get_multi_source_player() -> MultiSourcePlayer:
    """Get or create the global multi-source player instance."""
    global _multi_source_player
    if _multi_source_player is None:
        _multi_source_player = MultiSourcePlayer()
    return _multi_source_player
