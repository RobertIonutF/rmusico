# Discord Music Bot - Audio Troubleshooting Guide

## Common Causes of Static Audio

### 1. FFmpeg Configuration Issues
**Problem**: Using wrong audio codec or format, or incompatible volume control
**Solution**: The bot now uses PCM audio with volume control, with Opus as fallback

**What was fixed**:
- **Primary**: Uses `discord.FFmpegPCMAudio` with volume control (PCMVolumeTransformer)
- **Fallback**: Uses `discord.FFmpegOpusAudio` when PCM fails (no volume control)
- **Fixed Error**: "AudioSource must not be Opus encoded" - PCMVolumeTransformer can't handle Opus

### 2. Missing Voice Dependencies
**Problem**: PyNaCl or Opus libraries not installed
**Solution**: Install discord.py with voice support

```bash
# Windows
pip install discord.py[voice]

# Linux/macOS
pip3 install discord.py[voice]
```

### 3. Incorrect Audio Format
**Problem**: yt-dlp extracting audio in incompatible format
**Solution**: Let FFmpeg handle conversion instead of yt-dlp

**What was changed**:
- Removed `extractaudio: True` and `audioformat: 'opus'` from yt-dlp config
- Let FFmpeg do the audio conversion for better compatibility

### 4. Network/Streaming Issues
**Problem**: Poor connection or buffering issues
**Solution**: Improved reconnection settings

**FFmpeg options now include**:
- `-reconnect 1` - Enable reconnection
- `-reconnect_streamed 1` - Reconnect for streaming
- `-reconnect_delay_max 5` - Max delay between attempts
- `-fflags +discardcorrupt` - Handle corrupted data

## Testing Your Setup

### 1. Run the Audio Test Bot
```bash
python test_audio.py
```

Commands:
- `!testffmpeg` - Test FFmpeg functionality
- `!testjoin` - Join voice channel
- `!testplay <url>` - Test audio with a URL
- `!testleave` - Leave voice channel

### 2. Check FFmpeg Installation
```bash
python ffmpeg_utils.py
```

This will:
- Check if FFmpeg is installed
- Test PCM and Opus conversion
- Show installation instructions if needed

### 3. Manual FFmpeg Test
```bash
# Test if FFmpeg can process audio
ffmpeg -i "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav" -t 5 -f null -

# Test Opus encoding specifically
ffmpeg -i "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav" -c:a libopus -b:a 128k -ar 48000 -ac 2 -t 5 -f null -
```

## Configuration Changes Made

### config.py
```python
# PCM options (primary - supports volume control)
FFMPEG_OPTIONS = {
    'options': '-vn'  # No video, PCM audio output
}

# Opus options (fallback - better compression, no volume control)
FFMPEG_OPUS_OPTIONS = {
    'options': '-vn -c:a libopus -b:a 128k -ar 48000 -ac 2'  # Opus encoding
}
```

### ytdl_source.py
```python
# New approach with fallback
try:
    # Primary: PCM with volume control
    source = discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS)
    audio_source = discord.PCMVolumeTransformer(source, volume=volume)
except Exception:
    # Fallback: Opus without volume control
    source = discord.FFmpegOpusAudio(filename, **FFMPEG_OPUS_OPTIONS)
    audio_source = source  # No volume control possible
```

## Common Error Messages

### "AudioSource must not be Opus encoded"
- **Cause**: Trying to use PCMVolumeTransformer with Opus audio
- **Fix**: Applied in this update - PCM is now primary, Opus is fallback without volume control

### "Only static/noise playing"
- **Cause**: Wrong audio codec combination (was the original issue)
- **Fix**: Applied in this update - using proper PCM encoding

### "Volume control not supported"
- **Cause**: Using Opus audio format (fallback mode)
- **Fix**: This is expected behavior - Opus provides better quality but no volume control

### "PyNaCl not installed"
- **Cause**: Missing voice encryption library
- **Fix**: `pip install PyNaCl` or `pip install discord.py[voice]`

### "Opus library not loaded"
- **Cause**: System opus library missing
- **Fix**: Install opus library or let Discord.py use built-in version

### "FFmpeg not found"
- **Cause**: FFmpeg not installed or not in PATH
- **Fix**: Install FFmpeg following platform-specific instructions

## Quality Settings

### PCM (Primary - with Volume Control)
- No compression
- Higher bandwidth usage
- Direct audio stream
- Full volume control support

### Opus (Fallback - without Volume Control)
- Bitrate: 128k (good quality/bandwidth balance)
- Sample rate: 48000 Hz (Discord's native rate)
- Channels: 2 (stereo)
- No volume control (limitation of Discord.py)

## Advanced Troubleshooting

### 1. Enable Debug Logging
Add to your code:
```python
logging.getLogger('discord').setLevel(logging.DEBUG)
```

### 2. Test Different URLs
- YouTube videos
- Direct audio files (.mp3, .wav)
- Streaming URLs

### 3. Check Discord Voice Region
Some voice regions may have different audio requirements or quality.

### 4. Monitor Resource Usage
- CPU usage during playback
- Memory consumption
- Network bandwidth

## Still Having Issues?

1. **Update Dependencies**:
   ```bash
   pip install -U discord.py yt-dlp PyNaCl
   ```

2. **Reinstall FFmpeg**:
   - Download latest version from https://ffmpeg.org/
   - Ensure it's in your system PATH

3. **Test with Simple Audio**:
   - Try a direct .mp3 URL first
   - Then test with YouTube URLs

4. **Check Bot Permissions**:
   - Connect to voice channels
   - Speak in voice channels
   - Use voice activity

## Platform-Specific Notes

### Windows
- Use Windows Subsystem for Linux (WSL) if having issues
- Ensure Visual C++ redistributables are installed

### Linux
- Install system audio libraries: `sudo apt install libffi-dev libnacl-dev`
- Check ALSA/PulseAudio configuration

### macOS
- Install Xcode command line tools
- Use Homebrew for FFmpeg: `brew install ffmpeg`

---

This guide should resolve the static audio issue. The main fix was correcting the FFmpeg audio codec configuration and ensuring proper Discord.py voice setup.
