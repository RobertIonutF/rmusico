# Discord Music Bot

A feature-rich Discord music bot that streams audio from YouTube with queue management, search functionality, and various playback controls.

## Features

- 🎵 **Dual Command Support**: Both slash commands (`/play`) and prefix commands (`!play`)
- 📝 **Queue Management**: Add, remove, shuffle, clear songs in queue
- ⏯️ **Playback Controls**: Play, pause, resume, stop, skip
- 🔊 **Volume Control**: Adjust playback volume (0-100%)
- 🔁 **Loop Mode**: Loop current song
- 🔍 **YouTube Search**: Search with multiple results display
- 📊 **Rich Embeds**: Beautiful song information with thumbnails
- 🚀 **Auto-disconnect**: Leaves voice channel when alone
- ⚙️ **FFmpeg Integration**: Optimized audio processing
- 🛡️ **Error Handling**: Comprehensive error handling and logging

## Requirements

- Python 3.8+
- discord.py
- yt-dlp
- FFmpeg

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd rmusico
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install system dependencies for voice support (Linux):
```bash
sudo apt install libopus0 ffmpeg
```
If deploying on Render, create an `apt.txt` file with `libopus0` so it gets installed automatically.

4. Install FFmpeg (if not installed):
   - **Windows**: Download from [FFmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - **Linux**: `sudo apt install ffmpeg`
   - **macOS**: `brew install ffmpeg`

5. Set up your bot token:
   - Create a Discord application at [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a bot and copy the token
   - Copy `.env.example` to `.env`: `copy .env.example .env` (Windows) or `cp .env.example .env` (Linux/macOS)
   - Edit `.env` and replace `your_bot_token_here` with your actual bot token
   - **Never commit the `.env` file to version control!**

## Usage

Run the bot:
```bash
python music_bot.py
```

### Commands

The bot supports both slash commands and traditional prefix commands:

| Slash Command | Prefix Command | Description |
|---------------|----------------|-------------|
| `/play <url/query>` | `!play <url/query>` | Play music from YouTube URL or search |
| `/pause` | `!pause` | Pause the current song |
| `/resume` | `!resume` | Resume the paused song |
| `/stop` | `!stop` | Stop music and clear queue |
| `/skip` | `!skip` | Skip the current song |
| `/queue` | `!queue` | Show the current queue |
| `/clear` | `!clear` | Clear the music queue |
| `/shuffle` | `!shuffle` | Shuffle the queue |
| `/volume <0-100>` | `!volume <0-100>` | Change playback volume |
| `/loop` | `!loop` | Toggle loop mode |
| `/nowplaying` | `!nowplaying` | Show currently playing song with controls |
| `/controls` | `!controls` | Show music control panel |
| `/volume_panel` | `!volume_panel` | Show volume control panel |
| `/search <query>` | `!search <query>` | Search YouTube for songs |
| `/join` | `!join` | Join your voice channel |
| `/leave` | `!leave` | Leave the voice channel |
| `/help` | `!help` | Show all commands |

**Note**: Slash commands provide a better user experience with autocomplete and validation!

## 🎛️ Interactive Controls

The bot now includes **interactive button controls** for a better user experience:

### Music Control Buttons
When playing music, you'll see buttons for:
- **⏸️/▶️** - Pause/Resume playback
- **⏹️** - Stop music and clear queue
- **⏭️** - Skip to next song
- **🔀** - Shuffle queue
- **🔄/🔂** - Toggle loop mode

## 🤖 YouTube Bot Detection & Solutions

YouTube has implemented stronger bot detection measures that may affect the bot's ability to play music from direct URLs. Here are the solutions implemented:

### Automatic Fallback Strategies

1. **Smart Extraction**: The bot automatically tries direct URL extraction first, then falls back to search if blocked
2. **Multiple Client Types**: Uses different YouTube client types (web, mobile, TV) to bypass blocks
3. **Search-First Mode**: When direct URLs fail, the bot extracts the video title and searches for it instead

### Best Practices for Users

- **Use search terms instead of URLs**: Instead of pasting a YouTube URL, try: `/play artist - song name`
- **Prefer song names**: Example: `/play Rick Astley Never Gonna Give You Up`
- **Avoid direct URLs when possible**: The bot handles search queries more reliably

### Advanced Solutions (For Deployment)

#### Option 1: YouTube Cookies (Recommended for Production)
If you have persistent bot detection issues, you can provide YouTube cookies:

1. Export your browser cookies for YouTube:
   ```bash
   # Using yt-dlp to extract cookies from Chrome
   yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://youtube.com"
   ```

2. Set the `COOKIES_PATH` environment variable:
   ```bash
   export COOKIES_PATH="/path/to/cookies.txt"
   ```

3. **⚠️ Security Warning**: Never commit cookie files to version control! Add `*.txt` to `.gitignore`

#### Option 2: Alternative Sources
Consider using other sources when YouTube blocks persist:
- SoundCloud URLs
- Direct audio file URLs
- Self-hosted audio files

### Error Messages Explained

- **"sign in to confirm you're not a bot"**: YouTube is blocking the IP. Try search terms instead of URLs.
- **"Video unavailable"**: The video is region-blocked, private, or deleted.
- **"Try using song names instead"**: The bot suggests using search terms rather than direct URLs.

### Queue Management
Use `!queue` or `/queue` to see interactive queue controls:
- **📋 Show Queue** - Display current queue
- **🗑️ Clear Queue** - Remove all songs
- **🔀 Shuffle Queue** - Randomize song order

### Volume Controls
Access volume controls with `!volume_panel` or `/volume_panel`:
- **🔇/🔊** - Mute/unmute audio
- **🔉** - Decrease volume (-10%)
- **🔊** - Increase volume (+10%)

**Benefits:**
- ✅ No need to remember commands
- ✅ Visual feedback for actions
- ✅ Easy to use on mobile
- ✅ Prevents accidental commands
- ✅ Works for anyone in the voice channel

## 🚀 Deployment

### Render.com Deployment (Optimized)
This bot is specially optimized for Render.com with 2025 improvements:

#### Automatic Optimizations:
- ✅ **Memory-optimized FFmpeg** for 512MB RAM limits
- ✅ **Advanced YouTube extraction** with bot detection bypass
- ✅ **Opus library loading** with `libopus.so.0` fallback
- ✅ **Environment detection** for hosting platforms
- ✅ **Smart extraction** (tries URLs, falls back to search)

#### Deployment Steps:
1. **Fork this repository** to your GitHub account
2. **Create a Render account** at [render.com](https://render.com)
3. **Connect your GitHub** and select this repository
4. **Set environment variables:**
   - `DISCORD_BOT_TOKEN` - Your Discord bot token
   - `PORT` - Will be set automatically by Render
5. **Deploy** - Render will automatically install dependencies and start the bot

#### Optional YouTube Cookie Setup (For Bot Detection):
If YouTube blocks your bot frequently, add cookies:
1. Export cookies from your browser:
   ```bash
   yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://youtube.com"
   ```
2. Upload `cookies.txt` to your repository (⚠️ **Never commit to public repos!**)
3. Set environment variable: `COOKIES_PATH=/opt/render/project/src/cookies.txt`

### Features for Hosting:
- ✅ **Web Dashboard** - View bot status at your deployment URL
- ✅ **Health Checks** - Automatic monitoring for uptime
- ✅ **Auto-restart** - Bot restarts if it crashes
- ✅ **Advanced Logging** - Full logging for debugging
- ✅ **Smart Port Binding** - Proper web service configuration
- ✅ **Bot Detection Handling** - Multiple fallback strategies

### Local Development
```bash
# Clone the repository
git clone <your-fork-url>
cd rmusico

# Install dependencies
pip install -r requirements.txt

# Create .env file with your bot token
echo "DISCORD_BOT_TOKEN=your_token_here" > .env

# Run the bot
python app.py
```

## 🔧 Troubleshooting

### YouTube Issues
If you see "YouTube Access Restricted" errors:
- **Automatic retry** - Bot uses multiple extraction strategies automatically
- **Wait a few minutes** - YouTube may lift temporary restrictions
- **Use song names** instead of direct URLs when possible
- **Try different search terms** for better results

### Bot Detection Protection
The bot includes advanced protection against YouTube bot detection:
- ✅ **Multiple client strategies** (mobile, TV, Android, web)
- ✅ **Smart retry logic** with different user agents
- ✅ **Rate limiting** to avoid triggering detection
- ✅ **Fallback extractors** when main methods fail
- ✅ **Mobile-first approach** (less likely to be blocked)

### Common Solutions
- 🎤 Join a voice channel before using music commands
- 🔊 Ensure bot has voice channel permissions  
- 📱 Use interactive buttons for easier control
- 🔄 Try `/skip` if a song gets stuck
- 🎛️ Use `/controls` for the full control panel
- 🔍 Use song titles instead of YouTube URLs

## Project Structure

```
rmusico/
├── config.py             # Configuration settings
├── music_bot.py          # Main bot implementation
├── music_commands.py     # Prefix command implementations
├── register_commands.py  # Slash command registration system
├── music_queue.py        # Queue management
├── ytdl_source.py        # YouTube audio source handling
├── utils.py              # Utility functions for embeds
├── ffmpeg_utils.py       # FFmpeg setup and utilities
├── manage_commands.py    # Command management CLI tool
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
├── .env                  # Your environment variables (create from .env.example)
├── .gitignore            # Git ignore file
├── app.py                # Backward compatibility wrapper
└── README.md             # This file
## Command Management

The bot includes a command management utility for handling slash command registration:

### Quick Setup for Testing
```bash
# Sync commands to a specific guild (immediate, for testing)
python manage_commands.py sync --guild YOUR_GUILD_ID

# List commands in a guild
python manage_commands.py list --guild YOUR_GUILD_ID
```

### Production Deployment
```bash
# Sync commands globally (takes up to 1 hour)
python manage_commands.py sync

# List global commands
python manage_commands.py list
```

### Command Cleanup
```bash
# Clear commands from a guild
python manage_commands.py clear --guild YOUR_GUILD_ID

# Clear global commands
python manage_commands.py clear
```

## FFmpeg Setup

The bot requires FFmpeg for audio processing. The bot will automatically check for FFmpeg on startup.

### Check FFmpeg Installation
```bash
python ffmpeg_utils.py
```

### Installation Instructions

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg
```

## Security Best Practices

- ✅ **Never commit your `.env` file** - it's already in `.gitignore`
- ✅ **Use environment variables** for sensitive data like bot tokens
- ✅ **Copy `.env.example` to `.env`** and fill in your actual values
- ✅ **Rotate your bot token** if it's ever exposed publicly

## Environment Variables

Create a `.env` file in the project root with:

```env
# Required
DISCORD_BOT_TOKEN=your_actual_bot_token_here

# Optional (with defaults)
BOT_PREFIX=!
LOG_LEVEL=INFO
```

The bot is now organized into modular components:

- **config.py**: Centralized configuration management
- **music_bot.py**: Main bot class with event handling
- **music_commands.py**: Discord commands as a Cog
- **music_queue.py**: Queue management with loop functionality
- **ytdl_source.py**: YouTube audio extraction and searching
- **utils.py**: Utility functions for creating embeds

## Best Practices Implemented

1. **Modular Design**: Separated concerns into different modules
2. **Type Hints**: Added comprehensive type annotations
3. **Error Handling**: Robust error handling with logging
4. **Documentation**: Detailed docstrings for all functions
5. **Configuration**: Centralized settings management
6. **Logging**: Structured logging for debugging
7. **Resource Management**: Proper cleanup and disconnection
8. **Code Organization**: Logical grouping of related functionality

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
