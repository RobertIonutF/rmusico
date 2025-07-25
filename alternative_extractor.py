"""Alternative YouTube extractors for when main yt-dlp fails."""

import logging
import re
from typing import Optional, Dict, Any
import aiohttp
import json

logger = logging.getLogger(__name__)

class AlternativeExtractor:
    """Alternative extractor for when yt-dlp fails with bot detection."""
    
    @staticmethod
    async def extract_video_info(url: str) -> Optional[Dict[str, Any]]:
        """Try to extract video info using alternative methods."""
        video_id = AlternativeExtractor._extract_video_id(url)
        if not video_id:
            return None
            
        try:
            # Try YouTube's oEmbed API (limited but more reliable)
            return await AlternativeExtractor._try_oembed(video_id)
        except Exception as e:
            logger.warning(f"Alternative extraction failed: {e}")
            return None
    
    @staticmethod
    def _extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/v/([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    @staticmethod
    async def _try_oembed(video_id: str) -> Optional[Dict[str, Any]]:
        """Try YouTube's oEmbed API."""
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(oembed_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Create a simplified info dict
                    return {
                        'id': video_id,
                        'title': data.get('title', 'Unknown Title'),
                        'uploader': data.get('author_name', 'Unknown'),
                        'duration': None,  # oEmbed doesn't provide duration
                        'webpage_url': f"https://www.youtube.com/watch?v={video_id}",
                        'thumbnail': data.get('thumbnail_url'),
                        'description': f"Video by {data.get('author_name', 'Unknown')}",
                        'view_count': None,
                        'upload_date': None,
                        # Note: No direct audio URL - this would need the bot to use 
                        # YouTube's web player URL as a fallback
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'formats': [
                            {
                                'url': f"https://www.youtube.com/watch?v={video_id}",
                                'ext': 'webm',
                                'format_id': 'fallback'
                            }
                        ]
                    }
        return None

async def fallback_extract(url: str) -> Optional[Dict[str, Any]]:
    """Main fallback extraction function."""
    logger.info(f"Attempting alternative extraction for: {url}")
    
    try:
        info = await AlternativeExtractor.extract_video_info(url)
        if info:
            logger.info(f"✅ Alternative extraction successful: {info['title']}")
            return info
        else:
            logger.warning("❌ Alternative extraction failed")
            return None
    except Exception as e:
        logger.error(f"Alternative extraction error: {e}")
        return None
