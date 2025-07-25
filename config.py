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
    'format': 'bestaudio/best',
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
    # YouTube anti-bot measures workaround
    'extractor_retries': 3,
    'retry_sleep_functions': {'http': lambda n: min(4 ** n, 30)},
    # Use mobile web client which is less likely to trigger bot detection
    'extractor_args': {
        'youtube': {
            'player_client': ['mweb', 'tv', 'web'],
            'player_skip': ['webpage'],
            'skip': ['hls', 'dash'],
        }
    },
    # Better headers to avoid bot detection
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
    # Rate limiting to avoid triggering detection
    'sleep_interval': 1,
    'max_sleep_interval': 3,
    # Remove extractaudio and audioformat - let FFmpeg handle conversion
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

# FFmpeg Opus options (alternative for better quality)
FFMPEG_OPUS_OPTIONS: Dict[str, str] = {
    'before_options': (
        '-reconnect 1 '
        '-reconnect_streamed 1 '
        '-reconnect_delay_max 5 '
        '-probesize 32 '
        '-fflags +discardcorrupt'
    ),
    'options': '-vn -c:a libopus -b:a 128k -ar 48000 -ac 2'
}

# Queue settings
MAX_QUEUE_DISPLAY = 10
DEFAULT_VOLUME = 0.5
MAX_SEARCH_RESULTS = 5
