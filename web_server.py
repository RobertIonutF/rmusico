"""Simple Flask web server for the Discord Music Bot."""

import os
from flask import Flask, render_template, jsonify
from threading import Thread
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Bot status tracking
bot_status = {
    'connected': False,
    'guilds': 0,
    'voice_connected': False,
    'current_song': None,
    'queue_size': 0
}

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html', status=bot_status)

@app.route('/api/status')
def api_status():
    """API endpoint for bot status."""
    return jsonify(bot_status)

@app.route('/health')
def health():
    """Health check endpoint for Render."""
    return jsonify({
        'status': 'healthy',
        'bot_connected': bot_status['connected'],
        'service': 'rmusico-discord-bot'
    })

def update_bot_status(**kwargs):
    """Update bot status from the main bot."""
    bot_status.update(kwargs)

def run_web_server():
    """Run the Flask web server."""
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

def start_web_server_thread():
    """Start web server in a separate thread."""
    web_thread = Thread(target=run_web_server, daemon=True)
    web_thread.start()
    return web_thread

if __name__ == '__main__':
    run_web_server()
