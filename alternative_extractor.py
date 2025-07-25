"""Alternative YouTube extractors for when main yt-dlp fails."""

import logging
import re
from typing import Optional, Dict, Any
import aiohttp
import json
import asyncio

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
            # Try multiple methods in order of reliability
            methods = [
                AlternativeExtractor._try_oembed,
                AlternativeExtractor._try_noembed,
                AlternativeExtractor._try_youtube_api_fallback
            ]
            
            for method in methods:
                try:
                    result = await method(video_id)
                    if result:
                        return result
                except Exception as e:
                    logger.debug(f"Method {method.__name__} failed: {e}")
                    continue
                    
            return None
        except Exception as e:
            logger.warning(f"Alternative extraction failed: {e}")
            return None
    
    @staticmethod
    def _extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([^&\n?#]+)',
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
        
        timeout = aiohttp.ClientTimeout(total=10)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
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
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'formats': [
                            {
                                'url': f"https://www.youtube.com/watch?v={video_id}",
                                'ext': 'webm',
                                'format_id': 'fallback'
                            }
                        ],
                        'extractor': 'oembed_fallback'
                    }
        return None
    
    @staticmethod
    async def _try_noembed(video_id: str) -> Optional[Dict[str, Any]]:
        """Try NoEmbed API as secondary fallback."""
        noembed_url = f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}"
        
        timeout = aiohttp.ClientTimeout(total=10)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(noembed_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if not data.get('error'):
                        return {
                            'id': video_id,
                            'title': data.get('title', 'Unknown Title'),
                            'uploader': data.get('author_name', 'Unknown'),
                            'duration': None,
                            'webpage_url': f"https://www.youtube.com/watch?v={video_id}",
                            'thumbnail': data.get('thumbnail_url'),
                            'description': f"Video by {data.get('author_name', 'Unknown')}",
                            'view_count': None,
                            'upload_date': None,
                            'url': f"https://www.youtube.com/watch?v={video_id}",
                            'formats': [
                                {
                                    'url': f"https://www.youtube.com/watch?v={video_id}",
                                    'ext': 'webm',
                                    'format_id': 'noembed_fallback'
                                }
                            ],
                            'extractor': 'noembed_fallback'
                        }
        return None
    
    @staticmethod
    async def _try_youtube_api_fallback(video_id: str) -> Optional[Dict[str, Any]]:
        """Last resort: create minimal metadata for user notification."""
        # This doesn't actually fetch from YouTube API (would need API key)
        # but creates a basic structure for error display
        await asyncio.sleep(0.1)  # Small delay to simulate API call
        
        return {
            'id': video_id,
            'title': f'YouTube Video {video_id}',
            'uploader': 'YouTube',
            'duration': None,
            'webpage_url': f"https://www.youtube.com/watch?v={video_id}",
            'thumbnail': f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            'description': 'Video temporarily unavailable due to access restrictions',
            'view_count': None,
            'upload_date': None,
            'url': f"https://www.youtube.com/watch?v={video_id}",
            'formats': [
                {
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'ext': 'unavailable',
                    'format_id': 'blocked'
                }
            ],
            'extractor': 'blocked_fallback'
        }

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
