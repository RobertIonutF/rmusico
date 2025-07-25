"""
Discord Music Bot - Refactored version with modular architecture.

This is a wrapper that imports and runs the refactored music bot.
For the new modular implementation, see music_bot.py and related modules.
"""

import os
import logging
from web_server import start_web_server_thread, update_bot_status
from music_bot import main

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Start web server for Render deployment
    if os.environ.get('PORT'):
        logger.info("Starting web server for hosting platform...")
        start_web_server_thread()
        # Update initial status
        update_bot_status(connected=False, guilds=0, voice_connected=False, queue_size=0)
    
    # Start the Discord bot
    main()