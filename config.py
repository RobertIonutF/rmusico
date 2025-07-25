"""Configuration settings for the Discord Music Bot."""

import os
from typing import Dict, Any
from pathlib import Path

# Load environment variables from .env file
def load_env_file() -> None:
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value

# Load .env file before accessing environment variables
load_env_file()

# Bot configuration
BOT_PREFIX = '!'
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', '')

# yt-dlp configuration for audio extraction
YTDL_FORMAT_OPTIONS: Dict[str, Any] = {
    'format': 'bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    # Enhanced extraction for 2024-2025 YouTube measures
    'extractor_retries': 3,
    'retry_sleep_functions': {'http': lambda n: min(4 ** n, 30)},
    # Modern YouTube client strategies
    'extractor_args': {
        'youtube': {
            'player_client': ['mweb', 'ios', 'android_music', 'tv'],
            'player_skip': ['webpage'],
            'skip': ['hls', 'dash'],  # Skip complex formats for Render constraints
        }
    },
    # Optimized headers for mobile web client
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    },
    # Rate limiting for bot detection avoidance
    'sleep_interval': 1,
    'max_sleep_interval': 3,
}

# FFmpeg options for optimal Discord streaming
FFMPEG_OPTIONS: Dict[str, str] = {
    'before_options': (
        '-reconnect 1 '
        '-reconnect_streamed 1 '
        '-reconnect_delay_max 5 '
        '-probesize 32 '
        '-fflags +discardcorrupt'
    ),
    'options': '-vn'
}

# Render.com optimized FFmpeg options for deployment
RENDER_FFMPEG_OPTIONS: Dict[str, str] = {
    'before_options': (
        '-reconnect 1 '
        '-reconnect_streamed 1 '
        '-reconnect_delay_max 5 '
        '-reconnect_at_eof 1 '
        '-timeout 30000000 '  # 30 second timeout for Render's network
        '-probesize 50M '     # Reduced for memory constraints
        '-analyzeduration 50M '  # Reduced for memory constraints
        '-err_detect ignore_err '  # Continue despite minor errors
        '-fflags +discardcorrupt'  # Discard corrupted packets
    ),
    'options': (
        '-vn '  # No video processing
        '-bufsize 512k '  # Conservative buffer for 512MB RAM limit
        '-maxrate 96k '   # Limit bitrate for stability
        '-threads 1 '     # Single thread due to CPU constraints
        '-avoid_negative_ts make_zero'  # Handle timestamp issues
    )
}

# FFmpeg Opus options (alternative for better quality)
FFMPEG_OPUS_OPTIONS: Dict[str, str] = {
    'before_options': (
        '-reconnect 1 '
        '-reconnect_streamed 1 '
        '-reconnect_delay_max 5 '
        '-reconnect_at_eof 1 '
        '-timeout 30000000 '
        '-probesize 50M '
        '-analyzeduration 50M '
        '-err_detect ignore_err '
        '-fflags +discardcorrupt'
    ),
    'options': (
        '-vn '
        '-c:a libopus '
        '-b:a 96k '  # Reduced bitrate for Render constraints
        '-ar 48000 '
        '-ac 2 '
        '-bufsize 512k '
        '-maxrate 96k '
        '-threads 1 '
        '-avoid_negative_ts make_zero'
    )
}

# Queue settings
MAX_QUEUE_DISPLAY = 10
DEFAULT_VOLUME = 0.5
MAX_SEARCH_RESULTS = 5
