"""Smart YouTube handler with multiple fallback strategies."""

import asyncio
import logging
from typing import Optional, Dict, Any, List
import yt_dlp
import random

from config import YTDL_FORMAT_OPTIONS
from alternative_extractor import fallback_extract

logger = logging.getLogger(__name__)

class SmartYouTubeExtractor:
    """Smart YouTube extractor with multiple fallback strategies."""
    
    def __init__(self):
        self.extractors = []
        self._setup_extractors()
    
    def _setup_extractors(self):
        """Setup multiple yt-dlp configurations with different strategies."""
        
        # Strategy 1: Mobile web client (most reliable for avoiding bot detection)
        mweb_opts = YTDL_FORMAT_OPTIONS.copy()
        mweb_opts['extractor_args'] = {
            'youtube': {
                'player_client': ['mweb'],
                'player_skip': ['webpage'],
                'skip': ['hls', 'dash'],
            }
        }
        mweb_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
        }
        self.extractors.append(('mweb', yt_dlp.YoutubeDL(mweb_opts)))
        
        # Strategy 2: TV client
        tv_opts = YTDL_FORMAT_OPTIONS.copy()
        tv_opts['extractor_args'] = {
            'youtube': {
                'player_client': ['tv'],
                'player_skip': ['webpage'],
            }
        }
        self.extractors.append(('tv', yt_dlp.YoutubeDL(tv_opts)))
        
        # Strategy 3: Android client
        android_opts = YTDL_FORMAT_OPTIONS.copy()
        android_opts['extractor_args'] = {
            'youtube': {
                'player_client': ['android'],
                'player_skip': ['webpage'],
            }
        }
        android_opts['http_headers'] = {
            'User-Agent': 'com.google.android.youtube/17.31.35 (Linux; U; Android 11) gzip'
        }
        self.extractors.append(('android', yt_dlp.YoutubeDL(android_opts)))
        
        # Strategy 4: Default web client (last resort)
        web_opts = YTDL_FORMAT_OPTIONS.copy()
        self.extractors.append(('web', yt_dlp.YoutubeDL(web_opts)))
    
    async def extract_info(self, url: str, *, loop: Optional[asyncio.AbstractEventLoop] = None) -> Dict[str, Any]:
        """Extract info using multiple strategies."""
        loop = loop or asyncio.get_event_loop()
        
        # Randomize order to distribute load
        extractors = self.extractors.copy()
        random.shuffle(extractors)
        
        last_error = None
        
        for strategy_name, extractor in extractors:
            try:
                logger.info(f"Trying {strategy_name} client for: {url}")
                
                data = await loop.run_in_executor(
                    None, 
                    lambda: extractor.extract_info(url, download=False)
                )
                
                if 'entries' in data:
                    # Handle playlists - take first video
                    data = data['entries'][0]
                    logger.info(f"Playlist detected, using first video: {data.get('title', 'Unknown')}")
                
                logger.info(f"✅ {strategy_name} client succeeded: {data.get('title', 'Unknown')}")
                return data
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"❌ {strategy_name} client failed: {error_msg}")
                last_error = e
                
                # Check if it's a bot detection error
                if "Sign in to confirm you're not a bot" in error_msg or "bot" in error_msg.lower():
                    logger.info(f"Bot detection on {strategy_name}, trying next strategy...")
                    continue
                else:
                    # If it's not a bot detection error, continue trying other strategies
                    continue
        
        # All yt-dlp strategies failed, try alternative extraction
        logger.warning("All yt-dlp strategies failed, attempting alternative extraction...")
        
        try:
            fallback_data = await fallback_extract(url)
            if fallback_data:
                logger.info(f"✅ Alternative extraction successful: {fallback_data['title']}")
                return fallback_data
        except Exception as fallback_error:
            logger.error(f"Alternative extraction also failed: {fallback_error}")
        
        # If everything fails, raise the last yt-dlp error
        if last_error:
            raise last_error
        else:
            raise Exception("All extraction methods failed")
    
    async def search_youtube(self, query: str, *, loop: Optional[asyncio.AbstractEventLoop] = None) -> Optional[Dict[str, Any]]:
        """Search YouTube using the best available strategy."""
        loop = loop or asyncio.get_event_loop()
        
        # Use the first (most reliable) extractor for searches
        strategy_name, extractor = self.extractors[0]
        
        try:
            logger.info(f"Searching YouTube with {strategy_name} client: {query}")
            search_query = f"ytsearch:{query}"
            
            data = await loop.run_in_executor(
                None, 
                lambda: extractor.extract_info(search_query, download=False)
            )
            
            if 'entries' in data and len(data['entries']) > 0:
                result = data['entries'][0]
                logger.info(f"Found video: {result.get('title', 'Unknown')}")
                return result
            
            logger.warning(f"No results found for query: {query}")
            return None
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return None

# Global instance
_smart_extractor = None

def get_smart_extractor() -> SmartYouTubeExtractor:
    """Get or create the global smart extractor instance."""
    global _smart_extractor
    if _smart_extractor is None:
        _smart_extractor = SmartYouTubeExtractor()
    return _smart_extractor
