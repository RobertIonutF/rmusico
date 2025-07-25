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
